# Data upload and transformation for Polish EOSC

### Overview
This package handles harvesting, transforming, and sending Polish scientific datasets and metadata to Solr for EOSC PL.

Supported repositories:
- **RepOD** (`repod`) – Polish Open Research Data repository (Dataverse)
- **Rodbuk** (`rodbuk`) – Cracow Open Research Data repository (Dataverse)
- **ECUDO** (`ecudo`) – Polish Oceanographic Data Centre
- **EGA** (`ega`) – European Genome-phenome Archive Polish datasets
- **OneData** (`onedata` / `oai_pmh`) – OneData repository harvested via OAI-PMH

All output files are saved in `eosc_pl/output/<repository>.json`.

---

### Setup
Always run from the root directory of the repository (`transform-service`) with virtual environment activated:
```bash
source .venv/bin/activate
```

---

### How to run each pipeline

#### 1. RepOD & Rodbuk (`process.py`)
Run both default repositories:
```bash
python3 -m eosc_pl.process
```
Run specific repository:
```bash
python3 -m eosc_pl.process repod
python3 -m eosc_pl.process rodbuk
```
Local dry-run (skips Solr upload, saves to `eosc_pl/output/`):
```bash
python3 -m eosc_pl.process rodbuk --dry-run
python3 -m eosc_pl.process repod --dry-run
```
Test with local data files (`--from-file`):
```bash
python3 -m eosc_pl.process rodbuk --from-file eosc_pl/rodbuk.txt --dry-run
python3 -m eosc_pl.process repod --from-file eosc_pl/repod.txt --limit 10 --dry-run
```
Limit number of records fetched (`--limit`):
```bash
python3 -m eosc_pl.process repod --limit 20 --dry-run
python3 -m eosc_pl.process rodbuk --limit 20 --dry-run
```

#### 2. ECUDO
Standalone:
```bash
python3 -m eosc_pl.ecudo.pipeline --dry-run
python3 -m eosc_pl.ecudo.pipeline --dry-run --limit 10
python3 -m eosc_pl.ecudo.pipeline --from-file <path_to_dump.json> --dry-run
```
Or via `process.py`:
```bash
python3 -m eosc_pl.process ecudo --dry-run --limit 10
```
Output saved to: `eosc_pl/output/ecudo.json`

#### 3. EGA
Standalone:
```bash
python3 -m eosc_pl.ega.pipeline --dry-run
python3 -m eosc_pl.ega.pipeline --dry-run --limit 5
python3 -m eosc_pl.ega.pipeline --dry-run EGAD50000000124 EGAD50000000125
```
Or via `process.py`:
```bash
python3 -m eosc_pl.process ega --dry-run --limit 5
```
Output saved to: `eosc_pl/output/ega.json`

#### 4. OneData (OAI-PMH)
Standalone:
```bash
python3 -m eosc_pl.oai_pmh.pipeline onedata --dry-run
python3 -m eosc_pl.oai_pmh.pipeline onedata --dry-run --limit 10
```
Or via `process.py`:
```bash
python3 -m eosc_pl.process onedata --dry-run --limit 10
```
Output saved to: `eosc_pl/output/onedata.json`

---

### CLI Arguments for `process.py`
- `repositories`: Names of repositories (`repod`, `rodbuk`, `ecudo`, `ega`, `onedata`). Defaults to `repod` and `rodbuk`.
- `--dry-run` / `--skip-solr`: Skips sending data to Solr and saves transformed data to file.
- `--from-file <path>`: Loads data from a local JSON/txt file instead of querying the search API.
- `--limit <int>` / `-n <int>`: Maximum number of records to fetch/process.
- `--output-dir <path>`: Custom directory for output files (default: `eosc_pl/output`).
- `--no-save`: Do not write output JSON files to disk.

---

### Environment Variables (`.env`):
- `RODBUK_DATASET_LIST_ADDRESS` - Rodbuk search endpoint (default: `https://rodbuk.pl/api/search`).
- `RODBUK_DATASET_DETAIL_ADDRESS` - Rodbuk detail endpoint (default: `https://rodbuk.pl/api/datasets/export?exporter=dataverse_json&persistentId=`).
- `REPOD_DATASET_LIST_ADDRESS` - RepOD search endpoint (default: `https://repod.icm.edu.pl/api/search`).
- `REPOD_DATASET_DETAIL_ADDRESS` - RepOD detail endpoint (default: `https://repod.icm.edu.pl/api/datasets/export?exporter=dataverse_json&persistentId=doi:`).
- `SOLR_URL` - Solr address. Default: `http://149.156.182.2:8983`.
- `SOLR_EOSCPL_DATASET_COLS_NAME` - Solr collection names. Default: `"pl_all_collection pl_dataset"`.
- `DRY_RUN` - If `true`, Solr sending is skipped by default.
