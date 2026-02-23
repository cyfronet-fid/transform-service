# pipeline.py

import json

from client import AggregatorClient

from sage.sender import send_to_solr
from sage.transfomer import transform_raw_dataset


def flatten_datasets(catalogs):
    """
    Extract all raw dataset dicts from all catalogs.
    """
    datasets = []

    if not isinstance(catalogs, list):
        print("[ERROR] Expected list of catalog objects.")
        return datasets

    for catalog in catalogs:
        raw_list = catalog.get("dcat:dataset", [])
        if isinstance(raw_list, list):
            for ds in raw_list:
                if isinstance(ds, dict):
                    datasets.append(ds)

    return datasets


def main():
    print("Fetching catalog data...\n")

    # 1) Load all catalogs from EDC
    client = AggregatorClient()
    data = client.fetch_catalog()

    # 2) Flatten into dataset list
    raw_datasets = flatten_datasets(data)
    print(f"Total raw datasets: {len(raw_datasets)}")

    if not raw_datasets:
        print("No datasets found.")
        return

    # 3) Transform datasets (skip invalid ones)
    transformed = [
        t for t in (transform_raw_dataset(ds) for ds in raw_datasets) if t is not None
    ]

    print(f"Transformed datasets: {len(transformed)}")

    # 4) Show one example
    print("\n=== SAMPLE RAW RECORD ===")
    print(json.dumps(raw_datasets[3], indent=2)[:2000])  # truncated

    print("\n=== SAMPLE TRANSFORMED RECORD ===")
    print(json.dumps(transformed[3], indent=2))

    # 5) Send to Solr
    print("\nSending data to Solr...")
    send_to_solr(transformed)


if __name__ == "__main__":
    main()
