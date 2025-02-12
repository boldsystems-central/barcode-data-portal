# Weekly Rebuild Standard Operating Procesure

As mentioned in the [Rebuild Design document](REBUILD_DESIGN.md) this pipeline is a weekly update of data in BOLD.
It is run once every week and will result in the database being updated in real-time as users are using the portal.

### Instantiate Connection to Couchbase and Python environment
Select a folder which will serve as a working-space/stage, while the pipeline is being executed.
```
WORKING_DIR="path-to-the-data-to-be-uploaded-and-other-intermediate-steps"

cd /path-to-the-bold-public-portal-repository

# To get REDIS_HOST, COUCHBASE_ENDPOINT, COUCHBASE_USER and COUCHBASE_PASSWORD
source .env
export REDIS_HOST
export COUCHBASE_ENDPOINT
export COUCHBASE_USER
export COUCHBASE_PASSWORD

source /opt/miniconda3/etc/profile.d/conda.sh
conda activate 'your-python-virtual-env'

mkdir -p $WORKING_DIR

```

### Stage 1.1 - Download and unzip BOLD's Barcode Core Data model data into the working directory
This data is the BCDM representation of BOLD's data.

### Stage 1.2 - Download and unzip Registries into working directory
Registries required.

1. bold_dataset_registry.jsonl.gz
2. bold_barcodecluster_registry.jsonl.gz
3. bold_geopol_registry.jsonl.gz
4. bold_institution_registry.jsonl.gz
5. bold_primer_registry.jsonl.gz
6. bold_taxonomy_registry.jsonl.gz


### Stage 2 - Update Couchbase
```
# Perform updates on Couchbase
echo "[$(date)] Generating data..." >> $WORKING_DIR/log.txt
bash src/ETL/generate_and_sanitize_data.sh $WORKING_DIR

echo "[$(date)] Updating Couchbase..." >> $WORKING_DIR/log.txt
bash src/ETL/couchbase-tools/update_couchbase.sh $WORKING_DIR &>> $WORKING_DIR/update_log.txt

echo "[$(date)] Updating Couchbase exceptions..." >> $WORKING_DIR/log.txt
bash src/ETL/couchbase-tools/update_couchbase_summary_exceptions.sh $WORKING_DIR &>> $WORKING_DIR/exception_update_log.txt
```

### Stage 3 - Update Redis cache
```
# Perform updates on Redis cache
echo "[$(date)] Updating Redis..." >> $WORKING_DIR/log.txt
python src/tools/generateSummaryCache.py -i src/tools/summary_cache_queries.json
python src/tools/generateTaxMapCache.py -i src/tools/tax_map_cache_queries.json
python src/tools/generateStatsCache.py
```

### Stage 4 - Store pipeline artifacts
Store the artifacts from the upsert pipeline in order to track and assess changes made overtime.

1. $WORKING_DIR/update_log.txt
2. $WORKING_DIR/exception_update_log.txt
3. $WORKING_DIR/BCDM_updates.jsonl
4. $WORKING_DIR/tax_geo_summaries_updates.jsonl
5. $WORKING_DIR/country_summaries_updates.jsonl
6. $WORKING_DIR/institution_summaries_updates.jsonl
7. $WORKING_DIR/sequence_run_site_summaries_updates.jsonl
8. $WORKING_DIR/bin_summaries_updates.jsonl
9. $WORKING_DIR/dataset_summaries_updates.jsonl
10. $WORKING_DIR/primer_summaries_updates.jsonl
11. $WORKING_DIR/taxonomy_summaries_updates.jsonl
12. $WORKING_DIR/datasets_updates.jsonl
13. $WORKING_DIR/barcodeclusters_updates.jsonl
14. $WORKING_DIR/countries_updates.jsonl
15. $WORKING_DIR/institutions_updates.jsonl
16. $WORKING_DIR/primers_updates.jsonl
17. $WORKING_DIR/taxonomies_updates.jsonl
18. $WORKING_DIR/accepted_terms_updates.jsonl


### Review BCDM data flagged for deletion and recreate cache
In Couchbase, the weekly update pipeline adds new data and updates existing data, however it enlists the data to be deleted for review in files that have the suffix "_deletions.txt". For e.g. records to be deleted from the `tax_geo_summaries` will be listed in `tax_geo_summaries_deletions.txt`.
Review these deletion candidates and then delete them from Couchbase using `src/ETL/couchbase-tools/remove_from_couchbase.sh`.

Once the data is deleted from Couchbase, recreate the cache to reflect the latest snapshot in Couchbase.
```
# Perform updates on Redis cache
echo "[$(date)] Updating Redis..." >> $WORKING_DIR/log.txt
python src/tools/generateSummaryCache.py -i src/tools/summary_cache_queries.json
python src/tools/generateTaxMapCache.py -i src/tools/tax_map_cache_queries.json
python src/tools/generateStatsCache.py
```
