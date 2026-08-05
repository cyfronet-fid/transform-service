# SAGE Metadata Pipeline

This directory contains the SAGE metadata ingestion and transformation pipeline.

## Prerequisites

- Python 3.10+
- Project dependencies installed
- A valid `sage/.env` configuration file

## Running the pipeline

The pipeline should be executed from the **project root**, not from the `sage` directory.

```bash
python -m sage.pipeline
```

or, if using Pipenv:

```bash
pipenv run python -m sage.pipeline
```

## Configuration

The pipeline reads its configuration from:

```text
sage/.env
```

Ensure the required variables are defined before running the pipeline, for example:

```env
AGGREGATOR_URL=...
AGGREGATOR_API_KEY=...
SOLR_URL=...
SOLR_COLS_NAME=...
REQUEST_TIMEOUT=300
```

## Output

The pipeline performs the following steps:

1. Fetches metadata from the SAGE Aggregator API.
2. Flattens catalog datasets.
3. Transforms raw metadata into the target schema.
4. Sends transformed records to Solr.