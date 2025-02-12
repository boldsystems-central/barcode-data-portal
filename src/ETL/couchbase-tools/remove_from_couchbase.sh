#!/bin/bash

# Requires:
# python
# BCDM Deletions: BCDM_deletions.txt
# Summaries Deletions: tax_geo_inst_summaries_deletions.txt, country_summaries_deletions.txt,
#                      institution_summaries_deletions.txt, sequence_run_site_summaries_deletions.txt,
#                      bin_summaries_deletions.txt, dataset_summaries_deletions.txt,
#                      primer_summaries_deletions.txt, taxonomy_summaries_deletions.txt
# Terms Deletions: accepted_terms_deletions.txt
# Registries Deletions: datasets_deletions.txt, barcodeclusters_deletions.txt,
#                       countries_deletions.txt, institutions_deletions.txt,
#                       primers_deletions.txt, taxonomies_deletions.txt

WORKING_DIR=$1

# To get COUCHBASE_ENDPOINT, COUCHBASE_USER and COUCHBASE_PASSWORD
source .env

# 1. Remove BCDM documents
python src/ETL/couchbase-tools/bulk_remove_documents.py --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/BCDM_deletions.txt

# 2. Remove DERIVED documents
python src/ETL/couchbase-tools/bulk_remove_documents.py --bucket DERIVED --collection tax_geo_inst_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/tax_geo_inst_summaries_deletions.txt
python src/ETL/couchbase-tools/bulk_remove_documents.py --bucket DERIVED --collection country_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/country_summaries_deletions.txt
python src/ETL/couchbase-tools/bulk_remove_documents.py --bucket DERIVED --collection institution_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/institution_summaries_deletions.txt
python src/ETL/couchbase-tools/bulk_remove_documents.py --bucket DERIVED --collection sequence_run_site_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/sequence_run_site_summaries_deletions.txt
python src/ETL/couchbase-tools/bulk_remove_documents.py --bucket DERIVED --collection bin_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/bin_summaries_deletions.txt
python src/ETL/couchbase-tools/bulk_remove_documents.py --bucket DERIVED --collection dataset_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/dataset_summaries_deletions.txt
python src/ETL/couchbase-tools/bulk_remove_documents.py --bucket DERIVED --collection primer_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/primer_summaries_deletions.txt
python src/ETL/couchbase-tools/bulk_remove_documents.py --bucket DERIVED --collection taxonomy_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/taxonomy_summaries_deletions.txt

# 3: Remove ANCILLARY documents
python src/ETL/couchbase-tools/bulk_remove_documents.py --bucket ANCILLARY --collection datasets --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/datasets_deletions.txt
python src/ETL/couchbase-tools/bulk_remove_documents.py --bucket ANCILLARY --collection barcodeclusters --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/barcodeclusters_deletions.txt
python src/ETL/couchbase-tools/bulk_remove_documents.py --bucket ANCILLARY --collection countries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/countries_deletions.txt
python src/ETL/couchbase-tools/bulk_remove_documents.py --bucket ANCILLARY --collection institutions --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/institutions_deletions.txt
python src/ETL/couchbase-tools/bulk_remove_documents.py --bucket ANCILLARY --collection primers --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/primers_deletions.txt
python src/ETL/couchbase-tools/bulk_remove_documents.py --bucket ANCILLARY --collection taxonomies --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/taxonomies_deletions.txt

# 4. Remove terms documents
python src/ETL/couchbase-tools/bulk_remove_documents.py --bucket DERIVED --collection accepted_terms --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file $WORKING_DIR/accepted_terms_deletions.txt
