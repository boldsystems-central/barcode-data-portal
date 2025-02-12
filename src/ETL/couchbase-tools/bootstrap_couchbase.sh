#!/bin/bash

# Requires:
# python
# BCDM: bold_singlepane_public_export.jsonl
# Summaries: tax_geo_inst_summaries.jsonl, country_summaries.jsonl. institution_summaries.jsonl
#            sequence_run_site_summaries.jsonl, bin_summaries.jsonl, dataset_summaries.jsonl
#            primer_summaries.jsonl, taxonomy_summaries.jsonl
# Terms: accepted_terms_combined.jsonl
# Registries: bold_dataset_registry.jsonl, bold_barcodecluster_registry.jsonl, bold_geopol_registry.jsonl
#             bold_institution_registry.jsonl, bold_primer_registry.jsonl, bold_taxonomy_registry.jsonl

WORKING_DIR=$1

# To get COUCHBASE_ENDPOINT, COUCHBASE_USER and COUCHBASE_PASSWORD REDIS_HOST
source .env

# Step 1: Generate collections
python src/ETL/couchbase-tools/run_query.py --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file src/ETL/couchbase-tools/couchbase_collections.sql

# Step 2: Load primary documents
python src/ETL/couchbase-tools/bulk_load_documents.py --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'record_id' --file $WORKING_DIR/bold_singlepane_public_export.jsonl

# Step 3: Load summary and terms
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection tax_geo_inst_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'tax_geo_inst_id' --file $WORKING_DIR/tax_geo_inst_summaries.jsonl
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection country_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'country/ocean' --file $WORKING_DIR/country_summaries.jsonl
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection institution_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'inst' --file $WORKING_DIR/institution_summaries.jsonl
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection sequence_run_site_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'sequence_run_site' --file $WORKING_DIR/sequence_run_site_summaries.jsonl
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection bin_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'bin_uri' --file $WORKING_DIR/bin_summaries.jsonl
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection dataset_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'dataset.code' --file $WORKING_DIR/dataset_summaries.jsonl
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection primer_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'name' --file $WORKING_DIR/primer_summaries.jsonl
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection taxonomy_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'taxid' --file $WORKING_DIR/taxonomy_summaries.jsonl
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection accepted_terms --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'term' --file $WORKING_DIR/accepted_terms_combined.jsonl

# Step 4: Load ancillary documents
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection datasets --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'dataset.code' --file $WORKING_DIR/bold_dataset_registry.jsonl
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection barcodeclusters --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'barcodecluster.uri' --file $WORKING_DIR/bold_barcodecluster_registry.jsonl
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection countries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'name' --file $WORKING_DIR/bold_geopol_registry.jsonl
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection institutions --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'name' --file $WORKING_DIR/bold_institution_registry.jsonl
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection primers --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'name' --file $WORKING_DIR/bold_primer_registry.jsonl
python src/ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection taxonomies --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'taxid' --file $WORKING_DIR/bold_taxonomy_registry.jsonl

# Step 5: Generate indexes
python src/ETL/couchbase-tools/run_query.py --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file src/ETL/couchbase-tools/couchbase_index_definitions.sql
