"""Get, transform, upload data for Polish EOSC repositories"""

import argparse
import logging
from pathlib import Path
from typing import Optional

try:
    import logging.config

    from app.logger import LOGGING_CONFIG

    logging.config.dictConfig(LOGGING_CONFIG)
except ImportError:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

import eosc_pl.transform.transformers.pd as trans
from eosc_pl.settings import Repository, get_config
from eosc_pl.transform.utils.loader import (
    load_datasets_from_file,
    pd_load_datasets_with_pagination,
)
from eosc_pl.transform.utils.send import send_json_string_to_solr

logger = logging.getLogger(__name__)


def print_data_sources_summary(repository_name: str, datasets):
    """Print detected data sources and dataverses for processed datasets."""
    datasource_pids = set()
    if "datasource_pids" in datasets.columns:
        for val in datasets["datasource_pids"].dropna():
            if isinstance(val, list):
                datasource_pids.update(val)
            elif val:
                datasource_pids.add(str(val))

    dataverse_names = set()
    for col in ("dataverse_name", "name_of_dataverse"):
        if col in datasets.columns:
            for val in datasets[col].dropna():
                if val:
                    dataverse_names.add(str(val))

    print("\n" + "=" * 50)
    print(f"=== DATA SOURCES SUMMARY ({repository_name.upper()}) ===")
    print(f"Total datasets processed: {len(datasets)}")
    print(f"Primary DataSource PID(s): {sorted(list(datasource_pids))}")
    if dataverse_names:
        print(f"Detected {len(dataverse_names)} distinct Dataverse data source(s):")
        for name in sorted(dataverse_names)[:10]:
            print(f"  - {name}")
        if len(dataverse_names) > 10:
            print(f"  ... and {len(dataverse_names) - 10} more.")
    print("=" * 50 + "\n")


def process(
    repository: Repository,
    dry_run: bool = False,
    from_file: Optional[str | Path] = None,
    limit: Optional[int] = None,
    save_output: bool = True,
    output_dir: Optional[str | Path] = None,
):
    conf = get_config(repository)
    if dry_run:
        conf.DRY_RUN = True

    logger.info("Processing repository: %s", repository.value)

    # 1. Load data (from local file if provided, otherwise from API)
    if from_file:
        logger.info("Loading data from local file: %s", from_file)
        datasets_raw = load_datasets_from_file(from_file, max_records=limit)
    else:
        logger.info("Fetching data from API: %s", conf.DATASET_LIST_ADDRESS)
        datasets_raw = pd_load_datasets_with_pagination(conf, max_records=limit)

    if datasets_raw is None or datasets_raw.empty:
        logger.warning("No datasets loaded for %s", repository.value)
        return

    logger.info("Loaded %d raw datasets for %s", len(datasets_raw), repository.value)

    # 2. Transform
    transformer_cls = trans.transformers.get(repository)
    if not transformer_cls:
        raise ValueError(f"Transformer for {repository.value} not found.")

    logger.info("Applying transformations for %s", repository.value)
    datasets = transformer_cls()(datasets_raw)
    logger.info("Transformed %d datasets successfully", len(datasets))

    # 3. Print Data Sources summary in console
    print_data_sources_summary(repository.value, datasets)

    # 4. Save locally if requested
    out_dir = Path(output_dir) if output_dir else conf.OUTPUT_DIR
    if save_output:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{repository.value}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(datasets.to_json(orient="records", indent=2))
        logger.info("Saved transformed datasets to %s", out_file)

    # 5. Send to Solr / dry-run
    datasets_json = datasets.to_json(orient="records")
    if dry_run or getattr(conf, "DRY_RUN", False):
        logger.info(
            "Dry-run enabled: skipped sending %d records to Solr.", len(datasets)
        )
    else:
        logger.info("Sending %d records to Solr...", len(datasets))
        send_json_string_to_solr(datasets_json, conf)


def main():
    parser = argparse.ArgumentParser(
        description="Transform and upload EOSC PL repository datasets"
    )
    parser.add_argument(
        "repositories",
        nargs="*",
        help="Repository names to process (repod, rodbuk, ecudo, ega, onedata). Defaults to repod and rodbuk if omitted.",
    )
    parser.add_argument(
        "--dry-run",
        "--skip-solr",
        action="store_true",
        help="Skip sending transformed records to Solr (useful when testing without VPN)",
    )
    parser.add_argument(
        "--from-file",
        type=str,
        default=None,
        help="Path to local file containing raw JSON data (e.g. eosc_pl/rodbuk.txt)",
    )
    parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=None,
        help="Maximum number of records to process (useful for local testing)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not save transformed records to local output JSON file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory where output JSON files will be stored (defaults to eosc_pl/output)",
    )

    args = parser.parse_args()

    repo_names = args.repositories
    if not repo_names:
        repos_to_run = list(Repository)
    else:
        repos_to_run = []
        for name in repo_names:
            name_lower = name.lower()
            if name_lower == "ecudo":
                from eosc_pl.ecudo.pipeline import run_pipeline as run_ecudo

                out_file = (
                    Path(args.output_dir) / "ecudo.json" if args.output_dir else None
                )
                run_ecudo(
                    load_from=args.from_file,
                    dry_run=args.dry_run,
                    output_path=out_file,
                    limit=args.limit,
                )
            elif name_lower == "ega":
                from eosc_pl.ega.pipeline import run_pipeline as run_ega

                out_file = (
                    Path(args.output_dir) / "ega.json" if args.output_dir else None
                )
                run_ega(
                    dry_run=args.dry_run,
                    output_path=out_file,
                    limit=args.limit,
                )
            elif name_lower in ("onedata", "oai_pmh"):
                from eosc_pl.oai_pmh.pipeline import run_pipeline as run_oai

                out_file = (
                    Path(args.output_dir) / "onedata.json" if args.output_dir else None
                )
                run_oai(
                    repository="onedata",
                    max_records=args.limit,
                    dry_run=args.dry_run,
                    output_path=out_file,
                )
            else:
                try:
                    repos_to_run.append(Repository(name_lower))
                except ValueError:
                    logger.error(
                        "Invalid repository name: '%s'. Allowed values: repod, rodbuk, ecudo, ega, onedata",
                        name,
                    )

    if args.from_file and len(repos_to_run) > 1:
        logger.error(
            "--from-file can only be used with a single repository specified (e.g. 'rodbuk --from-file ...')"
        )
        return

    if repos_to_run:
        logger.info("Repositories to process: %s", [r.value for r in repos_to_run])

        for repo in repos_to_run:
            try:
                process(
                    repository=repo,
                    dry_run=args.dry_run,
                    from_file=args.from_file,
                    limit=args.limit,
                    save_output=not args.no_save,
                    output_dir=args.output_dir,
                )
            except Exception as e:
                logger.exception("Failed processing repository %s: %s", repo.value, e)

    logger.info("All requested operations processed.")


if __name__ == "__main__":
    main()
