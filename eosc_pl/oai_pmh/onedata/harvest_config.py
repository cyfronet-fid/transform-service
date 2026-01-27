from oai_pmh.harvester import harvest_to_ndjson

OAI_BASE_URL = "https://data.eosc.pl/oai_pmh"
METADATA_PREFIX = "oai_dc"

if __name__ == "__main__":
    written, out_full, out_dc = harvest_to_ndjson(
        base_url=OAI_BASE_URL,
        metadataPrefix=METADATA_PREFIX,
        max_records=100,
    )
    print(f"Harvested {written} records to {out_dc}")
