#!/bin/bash

# Requires:
# python, jq
# Reduced Summaries: reduced_institution_summaries.jsonl, reduced_sequence_run_site_summaries.jsonl,
#                    reduced_bin_summaries.jsonl, reduced_dataset_summaries.jsonl
# Filtered Summaries: filtered_country_summaries.jsonl, filtered_institution_summaries.jsonl,
#                     filtered_sequence_run_site_summaries.jsonl, filtered_bin_summaries.jsonl,
#                     filtered_dataset_summaries.jsonl, filtered_primer_summaries.jsonl

# Note: Only subset of reduced summaries are uploaded as other reduced summaries would never end up being used

WORKING_DIR=$1

# To get REDIS_HOST, COUCHBASE_ENDPOINT, COUCHBASE_USER and COUCHBASE_PASSWORD
source .env

# country_summaries
python src/ETL/couchbase-tools/bulk_upsert_documents.py \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --bucket DERIVED --collection country_summaries --primary-key 'country/ocean' \
    --file $WORKING_DIR/filtered_country_summaries.jsonl

# institution_summaries
while IFS=$'\t' read -r query_id summary; do
    echo "$summary" | redis-cli -h $REDIS_HOST -x set $query_id
done < $WORKING_DIR/reduced_institution_summaries.jsonl

python src/ETL/couchbase-tools/bulk_upsert_documents.py \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --bucket DERIVED --collection institution_summaries --primary-key 'inst' \
    --file $WORKING_DIR/filtered_institution_summaries.jsonl

# sequence_run_site_summaries
while IFS=$'\t' read -r query_id summary; do
    echo "$summary" | redis-cli -h $REDIS_HOST -x set $query_id
done < $WORKING_DIR/reduced_sequence_run_site_summaries.jsonl

python src/ETL/couchbase-tools/bulk_upsert_documents.py \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --bucket DERIVED --collection sequence_run_site_summaries --primary-key 'sequence_run_site' \
    --file $WORKING_DIR/filtered_sequence_run_site_summaries.jsonl

# bin_summaries
while IFS=$'\t' read -r query_id summary; do
    echo "$summary" | redis-cli -h $REDIS_HOST -x set $query_id
done < $WORKING_DIR/reduced_bin_summaries.jsonl

python src/ETL/couchbase-tools/bulk_upsert_documents.py \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --bucket DERIVED --collection bin_summaries --primary-key 'bin_uri' \
    --file $WORKING_DIR/filtered_bin_summaries.jsonl

# dataset_summaries
while IFS=$'\t' read -r query_id summary; do
    echo "$summary" | redis-cli -h $REDIS_HOST -x set $query_id
done < $WORKING_DIR/reduced_dataset_summaries.jsonl

python src/ETL/couchbase-tools/bulk_upsert_documents.py \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --bucket DERIVED --collection dataset_summaries --primary-key 'dataset.code' \
    --file $WORKING_DIR/filtered_dataset_summaries.jsonl

# primer_summaries
python src/ETL/couchbase-tools/bulk_upsert_documents.py \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --bucket DERIVED --collection primer_summaries --primary-key 'name' \
    --file $WORKING_DIR/filtered_primer_summaries.jsonl
