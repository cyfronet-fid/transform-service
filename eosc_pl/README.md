# Data upload and transformation for Polish EOSC

### Usage
Environmental variables are set in settings, they can be overwritten with the .env file.

To start the process, run the `process.py` file. 
If you want to process all repositories, run the proces with no arguments. 
If you want to process a specific repositories, provide the names of the repositories as the argument. You can
provide a list of the repositories separating each with a white space Ex: `process.py rodbuk repod`

Repositories names should be as specified in the Enum (`transform/utils/consts.py`). 
As for now there are 2 values: `repod` and `rodbuk`.

### .env variables:
- `RODBUK_DATASET_LIST_ADDRESS` - A Rodbuk's datasets address. E.g.: https://rodbuk.pl/api/search?q=*&type=dataset&per_page=1000&metadata_fields=citation:*
- `RODBUK_DATASET_DETAIL_ADDRESS` - A Rodbuk's address for license for a certain dataset based on doi. E.g.: https://rodbuk.pl/api/datasets/export?exporter=dataverse_json&persistentId=
- `REPOD_DATASET_LIST_ADDRESS` - A Repod's datasets address.  E.g: https://repod.icm.edu.pl/api/search?q=*&type=dataset
- `REPOD_DATASET_DETAIL_ADDRESS` - A Repod's address for detail, need to be called for most of dataset's metadata. E.g:  https://repod.icm.edu.pl/api/datasets/export?exporter=dataverse_json&persistentId=doi:10.18150/XBUVP6
- `SOLR_URL` - Solr address. Default: `http://149.156.182.2:8983`.
- `SOLR_EOSCPL_DATASET_COLS_NAME` -  The name of the collections to which datasets will be sent. E.g.: "pl_all_collection pl_dataset"
<br></br>