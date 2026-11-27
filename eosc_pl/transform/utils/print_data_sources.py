import logging


def print_data_sources_summary(
    repository_name: str,
    datasets=None,
    primary_datasource_pids=None,
    publishers=None,
    show_dataverses: bool = True,
):
    """
    Log a unified summary of data sources for processed datasets.

    Supports:
    - pandas DataFrame
    - list of dictionaries
    - optional publishers
    - optional DataSource PIDs
    - optional Dataverse names
    """

    datasource_pids = set(primary_datasource_pids or [])
    dataverse_names = set()
    detected_publishers = set()

    total_datasets = len(datasets) if datasets is not None else 0

    # Process pandas DataFrame
    if datasets is not None and hasattr(datasets, "columns"):

        if "datasource_pids" in datasets.columns:
            for val in datasets["datasource_pids"].dropna():
                if isinstance(val, (list, tuple, set)):
                    datasource_pids.update(str(x) for x in val if x)
                elif val:
                    datasource_pids.add(str(val))

        if show_dataverses:
            for col in ("dataverse_name", "name_of_dataverse"):
                if col in datasets.columns:
                    for val in datasets[col].dropna():
                        if val:
                            dataverse_names.add(str(val))

        if "publisher" in datasets.columns:
            for val in datasets["publisher"].dropna():
                if val:
                    detected_publishers.add(str(val))

    # Process list of dictionaries
    elif isinstance(datasets, list):
        for record in datasets:
            if not isinstance(record, dict):
                continue

            val = record.get("datasource_pids")
            if isinstance(val, (list, tuple, set)):
                datasource_pids.update(str(x) for x in val if x)
            elif val:
                datasource_pids.add(str(val))

            if show_dataverses:
                for key in ("dataverse_name", "name_of_dataverse"):
                    val = record.get(key)
                    if val:
                        dataverse_names.add(str(val))

            publisher = record.get("publisher")
            if publisher:
                detected_publishers.add(str(publisher))

    # Process explicitly provided publishers
    if publishers:
        detected_publishers.update(str(pub) for pub in publishers if pub)

    # Log summary
    logging.info("%s", "=" * 50)
    logging.info("=== DATA SOURCES SUMMARY (%s) ===", repository_name.upper())
    logging.info("Total datasets processed: %d", total_datasets)
    logging.info("Primary DataSource PID(s): %s", sorted(datasource_pids))

    if detected_publishers:
        logging.info(
            "Detected %d distinct publisher/organization data source(s):",
            len(detected_publishers),
        )
        for pub in sorted(detected_publishers):
            logging.info("  - %s", pub)

    if dataverse_names:
        logging.info(
            "Detected %d distinct Dataverse data source(s):",
            len(dataverse_names),
        )
        for name in sorted(dataverse_names)[:10]:
            logging.info("  - %s", name)

        if len(dataverse_names) > 10:
            logging.info(
                "  ... and %d more.",
                len(dataverse_names) - 10,
            )

    logging.info("%s\n", "=" * 50)
