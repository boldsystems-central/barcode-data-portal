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

# To get COUCHBASE_ENDPOINT, COUCHBASE_USER and COUCHBASE_PASSWORD
source .env

# 1. Upsert BCDM documents
q="select meta().id from \`BCDM\`.\`_default\`.\`primary\`"
python src/ETL/couchbase-tools/run_query.py \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --file <(echo $q) > $WORKING_DIR/BCDM_indexed_column.jsonl
python src/ETL/couchbase-tools/upsert_documents_by_hash.py \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --file $WORKING_DIR/bold_singlepane_public_export.jsonl \
    --index_column 'record_id' \
    --index_column_file $WORKING_DIR/BCDM_indexed_column.jsonl > $WORKING_DIR/BCDM_updates.jsonl

# 2. Upsert DERIVED documents
DERIVED="\
tax_geo_inst_summaries:tax_geo_inst_id:tax_geo_inst_summaries.jsonl
country_summaries:country/ocean:country_summaries.jsonl
institution_summaries:inst:institution_summaries.jsonl
sequence_run_site_summaries:sequence_run_site:sequence_run_site_summaries.jsonl
bin_summaries:bin_uri:bin_summaries.jsonl
dataset_summaries:dataset.code:dataset_summaries.jsonl
primer_summaries:name:primer_summaries.jsonl
taxonomy_summaries:taxid:taxonomy_summaries.jsonl
"

for D in $DERIVED
do
    collection=$( cut -d ':' -f 1 <<< "${D}" )
    index_column=$( cut -d ':' -f 2 <<< "${D}" )
    file=$( cut -d ':' -f 3 <<< "${D}" )

    q="select meta().id from \`DERIVED\`.\`_default\`.\`${collection}\`"
    python src/ETL/couchbase-tools/run_query.py \
        --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
        --file <(echo $q) > $WORKING_DIR/${collection}_indexed_column.jsonl
    python src/ETL/couchbase-tools/upsert_documents.py \
        --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
        --file $WORKING_DIR/$file \
        --index_column $index_column \
        --index_column_file $WORKING_DIR/${collection}_indexed_column.jsonl \
        --bucket DERIVED \
        --scope _default \
        --collection $collection > $WORKING_DIR/${collection}_updates.jsonl
done

# 3. Upsert ANCILLARY documents
ANCILLARY="\
datasets:dataset.code:bold_dataset_registry.jsonl
barcodeclusters:barcodecluster.uri:bold_barcodecluster_registry.jsonl
countries:name:bold_geopol_registry.jsonl
institutions:name:bold_institution_registry.jsonl
primers:name:bold_primer_registry.jsonl
taxonomies:taxid:bold_taxonomy_registry.jsonl
"

for A in $ANCILLARY
do
    collection=$( cut -d ':' -f 1 <<< "${A}" )
    index_column=$( cut -d ':' -f 2 <<< "${A}" )
    file=$( cut -d ':' -f 3 <<< "${A}" )

    q="select meta().id from \`ANCILLARY\`.\`_default\`.\`${collection}\`"
    python src/ETL/couchbase-tools/run_query.py \
        --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
        --file <(echo $q) > $WORKING_DIR/${collection}_indexed_column.jsonl
    python src/ETL/couchbase-tools/upsert_documents.py \
        --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
        --file $WORKING_DIR/$file \
        --index_column $index_column \
        --index_column_file $WORKING_DIR/${collection}_indexed_column.jsonl \
        --bucket ANCILLARY \
        --scope _default \
        --collection $collection > $WORKING_DIR/${collection}_updates.jsonl
done

# 4. Upsert terms documents
TERMS="\
accepted_terms:term:accepted_terms_combined.jsonl
"

for T in $TERMS
do
    collection=$( cut -d ':' -f 1 <<< "${T}" )
    index_column=$( cut -d ':' -f 2 <<< "${T}" )
    file=$( cut -d ':' -f 3 <<< "${T}" )

    q="select meta().id from \`DERIVED\`.\`_default\`.\`${collection}\`"
    python src/ETL/couchbase-tools/run_query.py \
        --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
        --file <(echo $q) > $WORKING_DIR/${collection}_indexed_column.jsonl
    python src/ETL/couchbase-tools/upsert_documents.py \
        --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
        --file $WORKING_DIR/$file \
        --index_column $index_column \
        --index_column_file $WORKING_DIR/${collection}_indexed_column.jsonl \
        --bucket DERIVED \
        --scope _default \
        --collection $collection > $WORKING_DIR/${collection}_updates.jsonl
done
