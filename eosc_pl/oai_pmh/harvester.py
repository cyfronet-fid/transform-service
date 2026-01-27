#!/usr/bin/env python3
"""
Harvest OAI-PMH using Sickle and convert each record XML to JSON while preserving all data.

Outputs NDJSON (one JSON object per line). Each object contains:
  - header: simplified header fields
  - metadata_canonical: full DOM-like JSON with namespaces, attributes, children...
  - metadata_flat: compact, query-friendly JSON (attributes -> @attributes, text -> #text)
  - raw: original XML (string)
"""
import argparse
import datetime
import json
import os
import urllib.parse
from collections import defaultdict

from lxml import etree
from oai_pmh.onedata.transform import transform_metadata_dc
from sickle import Sickle

# Use a safe XML parser configuration
XML_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, recover=True)

DC_TERMS = {
    "title",
    "creator",
    "subject",
    "description",
    "publisher",
    "contributor",
    "date",
    "type",
    "format",
    "identifier",
    "source",
    "language",
    "relation",
    "coverage",
    "rights",
}


def qname(el_or_tag):
    """Return (namespace, localname) for an lxml element or qname string."""
    q = etree.QName(el_or_tag)
    return q.namespace, q.localname


def elem_to_canonical(el):
    """Convert an lxml.Element into a canonical JSON node that preserves everything."""
    if el is None:
        return None
    node = {}
    q = etree.QName(el.tag)
    node["_tag"] = q.localname
    node["_ns"] = q.namespace
    node["_prefix"] = getattr(el, "prefix", None)
    # nsmap visible at this element
    node["_nsmap"] = {k: v for k, v in (el.nsmap or {}).items() if v is not None}
    # attributes (preserve ns info and prefix if available)
    attrs = {}
    for k, v in el.attrib.items():
        aq = etree.QName(k)
        # try to find the prefix that maps to aq.namespace (may be None)
        prefix = None
        for pfx, uri in (el.nsmap or {}).items():
            if uri == aq.namespace:
                prefix = pfx
                break
        attrs[aq.localname] = {"value": v, "ns": aq.namespace, "prefix": prefix}
    node["_attributes"] = attrs
    # text
    node["_text"] = el.text.strip() if el.text and el.text.strip() else None
    # children (preserve order)
    node["_children"] = [elem_to_canonical(child) for child in el]
    # tail
    node["_tail"] = el.tail.strip() if el.tail and el.tail.strip() else None
    return node


def elem_to_flat(el):
    """
    Convert an lxml.Element to a flattened JSON structure:
      - repeated elements become lists,
      - element attrs -> @attributes,
      - element text -> '#text' (or direct string if element only contains text).
    Namespace is preserved in key using 'prefix:local' if prefix exists, otherwise
    using '{namespace}local' (so keys remain unique).
    """
    if el is None:
        return None

    # If element has no children and no attributes -> return text directly (if any)
    children = list(el)
    if not children and not el.attrib:
        text = (el.text or "").strip()
        return text

    result = {}
    # attributes
    if el.attrib:
        result["@attributes"] = {}
        for k, v in el.attrib.items():
            aq = etree.QName(k)
            result["@attributes"][aq.localname] = v

    # children
    for child in children:
        ns, local = qname(child.tag)
        prefix = child.prefix
        if prefix:
            name = f"{prefix}:{local}"
        elif ns:
            name = f"{{{ns}}}{local}"
        else:
            name = local

        value = elem_to_flat(child)
        if name in result:
            if isinstance(result[name], list):
                result[name].append(value)
            else:
                result[name] = [result[name], value]
        else:
            result[name] = value

    # text (if mixed content)
    text = (el.text or "").strip()
    if text:
        result["#text"] = text

    return result


def header_to_dict(header_el):
    """Simplify the <header> element into a dict (header fields can repeat like setSpec)."""
    if header_el is None:
        return None
    d = {}
    for child in header_el:
        name = etree.QName(child.tag).localname
        val = (child.text or "").strip() if len(child) == 0 else elem_to_flat(child)
        if name in d:
            if isinstance(d[name], list):
                d[name].append(val)
            else:
                d[name] = [d[name], val]
        else:
            d[name] = val
    if header_el.attrib:
        d["@attributes"] = {
            etree.QName(k).localname: v for k, v in header_el.attrib.items()
        }
    return d


def extract_metadata_element_from_record_root(root):
    """
    Given the <record> root element, find the <metadata> element (by local-name)
    and return either its first child (common OAI patterns) or the metadata element itself.
    """
    md_nodes = root.xpath('.//*[local-name()="metadata"]')
    if not md_nodes:
        return None
    md_parent = md_nodes[0]
    # often metadata has a single child (e.g. <oai_dc:dc ...>), prefer that child
    if len(md_parent) > 0:
        return md_parent[0]
    return md_parent


def strip_dc_prefix(flat):
    """Return a copy of flat dict with 'dc:' prefix removed and @attributes dropped."""
    if not isinstance(flat, dict):
        return flat
    clean = {}
    for k, v in flat.items():
        if k == "@attributes":
            continue
        if k.startswith("dc:"):
            clean[k.split(":", 1)[1]] = v
        else:
            clean[k] = v
    return clean


def process_record(record):
    """
    Convert a Sickle Record into a JSON-able dict with header, canonical metadata, flat metadata, raw xml.
    """
    # get raw XML: Sickle exposes record.raw (string or bytes) or record.xml (Element)
    raw = None
    if hasattr(record, "raw") and record.raw:
        raw = record.raw
    elif hasattr(record, "xml") and record.xml is not None:
        raw = etree.tostring(record.xml, encoding="utf-8")
    else:
        # fallback
        raw = str(record)

    if isinstance(raw, str):
        raw_bytes = raw.encode("utf-8")
    else:
        raw_bytes = raw

    try:
        root = etree.fromstring(raw_bytes, parser=XML_PARSER)
    except Exception as e:
        # If parsing fails, return minimal info but preserve raw
        return {
            "header": None,
            "metadata_canonical": None,
            "metadata_flat": None,
            "raw": raw_bytes.decode("utf-8", errors="replace"),
            "parse_error": str(e),
        }

    # header
    header_nodes = root.xpath('.//*[local-name()="header"]')
    header = header_to_dict(header_nodes[0]) if header_nodes else None

    # metadata
    md_el = extract_metadata_element_from_record_root(root)
    canonical = elem_to_canonical(md_el) if md_el is not None else None
    flat = elem_to_flat(md_el) if md_el is not None else None
    dc_clean = strip_dc_prefix(flat) if flat is not None else None

    return {
        "header": header,
        "metadata_canonical": canonical,
        "metadata_flat": flat,
        "metadata_dc": dc_clean,
        "raw": raw_bytes.decode("utf-8", errors="replace"),
    }


def harvest_to_ndjson(
    base_url,
    out_path=None,
    metadataPrefix="oai_dc",
    from_date=None,
    ignore_deleted=True,
    max_records=None,
):
    """
    Harvest OAI-PMH records.
    Writes two files:
      1) out_path (default ./output/YYYY-MM-DD/<host>.ndjson) full records
      2) out_path with suffix "_dc.ndjson" containing transformed metadata_dc
         (ready for pandas/PySpark DataFrame)
    """
    sickle = Sickle(base_url, timeout=60)
    identify = sickle.Identify()
    params = {"metadataPrefix": metadataPrefix, "ignore_deleted": ignore_deleted}
    if from_date:
        params["from"] = from_date
    else:
        params["from"] = identify.earliestDatestamp

    records = sickle.ListRecords(**params)

    # Build default path if not provided
    if out_path is None:
        today = datetime.date.today().strftime("%Y-%m-%d")
        parsed = urllib.parse.urlparse(base_url)
        host = parsed.hostname or "repository"
        out_dir = os.path.join(os.getcwd(), "output", today)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{host}.ndjson")

    out_path_dc = out_path.replace(".ndjson", "_dc.ndjson")

    written = 0
    with open(out_path, "w", encoding="utf-8") as fh_full, open(
        out_path_dc, "w", encoding="utf-8"
    ) as fh_dc:
        for rec in records:
            obj = process_record(rec)
            fh_full.write(json.dumps(obj, ensure_ascii=False) + "\n")

            transformed = transform_metadata_dc(obj.get("metadata_dc"))
            if transformed:
                fh_dc.write(json.dumps(transformed, ensure_ascii=False) + "\n")

            written += 1
            if max_records and written >= max_records:
                break

    return written, out_path, out_path_dc


# Optional helper: extract Dublin Core fields (DC terms) from metadata element
def extract_oai_dc_fields(md_element):
    """Return a mapping of DC term -> list(values) when metadata is oai_dc (best-effort)."""
    if md_element is None:
        return {}
    out = defaultdict(list)
    for elem in md_element.xpath(".//*"):
        local = etree.QName(elem.tag).localname
        ns = etree.QName(elem.tag).namespace or ""
        # detect DC namespace heuristically
        if local in DC_TERMS and ("purl.org/dc" in ns or "dc" in (elem.prefix or "")):
            txt = (elem.text or "").strip()
            if txt:
                out[local].append(txt)
    return dict(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Harvest OAI-PMH and output NDJSON with lossless XML→JSON conversion."
    )
    parser.add_argument(
        "base_url", help="OAI-PMH base URL (e.g. https://data.eosc.pl/oai_pmh)"
    )
    parser.add_argument(
        "--out", "-o", help="Output NDJSON file (default: ./records.ndjson)"
    )
    parser.add_argument("--metadataPrefix", default="oai_dc")
    parser.add_argument(
        "--from_date", help="from date (YYYY-MM-DD) or omit to use earliestDatestamp"
    )
    parser.add_argument("--max", type=int, help="stop after N records (for testing)")
    args = parser.parse_args()

    written, out_path = harvest_to_ndjson(
        args.base_url,
        out_path=args.out,
        metadataPrefix=args.metadataPrefix,
        from_date=args.from_date,
        max_records=args.max,
    )
    print(f"✅ Wrote {written} records to {out_path}")
