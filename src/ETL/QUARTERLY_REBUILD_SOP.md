# Quarterly Rebuild Standard Operating Procesure

As mentioned in the [Rebuild Design document](REBUILD_DESIGN.md) this pipeline is a clean install of the latest data in BOLD.
It is run once every quarter and takes several hours (4-6) hours to complete. During this time BOLD Public Portal should be taken offline.

This pipeline assumes that BOLD's data to the uploaded are accessible.

<font color='red'>NOTE</font>
**Take the BOLD Portal offline**

Before starting the quarterly pipeline, please
* decide a comfortable time window and make the necessary announcements about maintenance work and portal unavailibility.
* keep all the pipeline requirements ready before launching the pipeline to save time required to preprocess large data files.
* communicate this down-time via a notice to the BOLD user base on the website and scheduled maintenance emails.

Draft the notice of an upcoming maintenance of BOLD portal and save the message into a file to be copied into application container.
```bash
echo "$NOTICE_MSG" > /tmp/notice.txt
docker cp /tmp/notice.txt fastapi-app-production:/tmp/bold-public-portal/notice.txt
```

<br/>

---

### Taking BOLD Portal Offline

Draft a message to inform users that the site is offline. After drafting the message, save the message into a file within
the server of the site and copy it into the container.

```bash
echo "$OFFLINE_MSG" > /tmp/offline.txt
docker cp /tmp/offline.txt fastapi-app-production:/tmp/bold-public-portal/offline.txt
```

### Instantiate Connection to Couchbase and Python environment

Select a folder which will serve as a working-space/stage, while the pipeline is being executed.
```
WORKING_DIR="path-to-the-data-to-be-uploaded-and-other-intermediate-steps"

cd /path-to-the-bold-public-portal-repository

# To get COUCHBASE_ENDPOINT, COUCHBASE_USER and COUCHBASE_PASSWORD REDIS_HOST
source .env
```


### Pre-run checks
A. Clear existing caches (file system cache and Redis cache).

File System cache
```
find /tmp/bold-public-portal/cache -type f -delete
```

Redis cache
```
redis-cli -h {hostname_IP} -p {port} FLUSHALL
```

B. To ensure a clean couchbase cluster, delete existing Couchbase collections.
Delete the BCDM collection.
```
query="DROP COLLECTION \`BCDM\`.\`_default\`.\`primary\` IF EXISTS"

python src/ETL/couchbase-tools/run_query.py \
--endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
--file <(echo $q)
```

Couchbase collection deletion queries can be found under
* `src/ETL/couchbase_clear_ancillary_collection.sql`
* `src/ETL/couchbase_clear_hybrid_collection.sql`
* `src/ETL/couchbase_clear_terms_collection.sql`

To execute these queries in Couchbase, use the `src/ETL/couchbase-tools/run_query.py` tool with each of the above `.sql` files.


<br/>

---

### Stage 1 - Generate Collections in Couchbase
```
python src/ETL/couchbase-tools/run_query.py \
        --endpoint $COUCHBASE_ENDPOINT \
        --username $COUCHBASE_USER \
        --password $COUCHBASE_PASSWORD \
        --file src/ETL/couchbase-tools/couchbase_collections.sql
```

### Stage 2 - Upload Primary BCDM documents
```
python src/ETL/couchbase-tools/bulk_load_documents.py \
        --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD\ --primary-key 'record_id' \
        --file $WORKING_DIR/bold_singlepane_public_export.jsonl
```

### Stage 3 - Upload summary documents and accepted terms
```
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection tax_geo_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'tax_geo_id' --file $WORKING_DIR/tax_geo_summaries.jsonl

python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection country_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'country/ocean' --file $WORKING_DIR/country_summaries.jsonl

python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection institution_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'inst' --file $WORKING_DIR/institution_summaries.jsonl

python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection sequence_run_site_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'sequence_run_site' --file $WORKING_DIR/sequence_run_site_summaries.jsonl

python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection bin_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'bin_uri' --file $WORKING_DIR/bin_summaries.jsonl

python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection dataset_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'dataset.code' --file $WORKING_DIR/dataset_summaries.jsonl

python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection primer_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'name' --file $WORKING_DIR/primer_summaries.jsonl

python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection taxonomy_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'taxid' --file $WORKING_DIR/taxonomy_summaries.jsonl

python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection accepted_terms --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'term' --file $WORKING_DIR/accepted_terms_combined.jsonl
```

### Stage 4 - Upload registries
```
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection datasets --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'dataset.code' --file $WORKING_DIR/bold_dataset_registry.jsonl

python src/ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection barcodeclusters --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'barcodecluster.uri' --file $WORKING_DIR/bold_barcodecluster_registry.jsonl

python src/ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection countries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'name' --file $WORKING_DIR/bold_geopol_registry.jsonl

python src/ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection institutions --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'name' --file $WORKING_DIR/bold_institution_registry.jsonl

python src/ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection primers --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'name' --file $WORKING_DIR/bold_primer_registry.jsonl

python src/ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection taxonomies --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'taxid' --file $WORKING_DIR/bold_taxonomy_registry.jsonl
```

### Stage 5: Generate indexes
```
python src/ETL/couchbase-tools/run_query.py --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file src/ETL/couchbase-tools/couchbase_index_definitions.sql
```

### Stage 6: Import summary documents exceeding Couchbase's limit
```
bash src/ETL/couchbase-tools/update_couchbase_summary_exceptions.sh $WORKING_DIR &>> $WORKING_DIR/exception_update_log.txt
```

### Stage 6: Initialize Redis cache
```
python src/tools/generateSummaryCache.py -i src/tools/summary_cache_queries.json
python src/tools/generateTaxMapCache.py -i src/tools/tax_map_cache_queries.json
python src/tools/generateStatsCache.py
```

### Post-run checks

On completion of the upload into Couchbase, please validate that the upload was successful and accurate. This can be done by ensuring that BCDM data and/or aggregates are identical to the same in Couchbase.

<font color='red'>NOTE</font>
**Put the BOLD Portal back online**
Once the data is validated indicating a successful run of the Quarterly pipeline, the BOLD Portal offline status should be removed from the website and an email should be sent to users, communicating that BOLD portal is back online. Remove the notice and offline messages from the application container using the following code block.

```bash
docker exec fastapi-app-production rm /tmp/bold-public-portal/notice.txt
docker exec fastapi-app-production rm /tmp/bold-public-portal/offline.txt
```
