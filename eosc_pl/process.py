"""Get, transform, upload data"""

import logging
import sys

import transform.transformers.pd as trans
from settings import Repository, get_config
from transform.utils.loader import pd_load_datasets_with_pagination
from transform.utils.send import send_json_string_to_solr

logger = logging.getLogger(__name__)


def process(repository):
    conf = get_config(repository)

    # Load
    datasets_raw = pd_load_datasets_with_pagination(conf)

    # Transform
    transformer = trans.transformers.get(repository)
    if not transformer:
        raise ValueError(f"Transformer for {repository.value} not found.")

    datasets = transformer()(datasets_raw)

    # Send
    datasets_json = datasets.to_json(orient="records")
    send_json_string_to_solr(datasets_json, conf)


if __name__ == "__main__":
    repositories = sys.argv[1:]

    if not repositories:
        repositories = list(Repository)

    for repository in repositories:
        try:
            repo_enum = (
                Repository(repository) if isinstance(repository, str) else repository
            )
        except ValueError:
            logger.error(f"Invalid repository name provided: {repository}")
            continue

        logger.info(f"Processing data for {repo_enum.value}")
        try:
            process(repo_enum)
        except Exception as e:
            logger.error(e)
            continue
    logger.info("All requested repositories has been proceeded.")
