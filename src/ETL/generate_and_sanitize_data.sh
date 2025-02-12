#!/bin/bash

# Requires:
# python, jq, iconv
# BCDM: bold_singlepane_public_export.jsonl
# Registries: bold_dataset_registry.jsonl, bold_barcodecluster_registry.jsonl, bold_geopol_registry.jsonl
#             bold_institution_registry.jsonl, bold_primer_registry.jsonl, bold_taxonomy_registry.jsonl

WORKING_DIR=$1
SIZE_LIMIT=20000000

# Step 1: Apply policies to BCDM documents
cat $WORKING_DIR/bold_singlepane_public_export.jsonl | bash src/ETL/apply_BCDM_policies.sh > $WORKING_DIR/bold_singlepane_public_export_filtered.jsonl
mv $WORKING_DIR/bold_singlepane_public_export_filtered.jsonl $WORKING_DIR/bold_singlepane_public_export.jsonl

# Step 2: Generate summary and terms documents
python src/ETL/extract_terms_and_summary_from_BCDM.py --summary_file $WORKING_DIR/tax_geo_inst_summaries.jsonl --terms_file $WORKING_DIR/accepted_terms.jsonl < $WORKING_DIR/bold_singlepane_public_export.jsonl
python src/ETL/extract_minimized_terms_with_inst_bins_ids_codes_BCDM.py --terms_file $WORKING_DIR/accepted_terms_contd.jsonl < $WORKING_DIR/bold_singlepane_public_export.jsonl
cat $WORKING_DIR/accepted_terms.jsonl $WORKING_DIR/accepted_terms_contd.jsonl > $WORKING_DIR/accepted_terms_combined.jsonl
rm $WORKING_DIR/accepted_terms.jsonl $WORKING_DIR/accepted_terms_contd.jsonl

# Step 2.1 Generate country summary
python src/ETL/extract_country_summary.py --summary_file $WORKING_DIR/country_summaries.jsonl < $WORKING_DIR/bold_singlepane_public_export.jsonl

touch $WORKING_DIR/reduced_country_summaries.jsonl $WORKING_DIR/filtered_country_summaries.jsonl
while IFS= read -r country; do
    file_name="country_$(echo "$country" | sed -r 's/[^a-zA-Z0-9]+/-/g').json"
    grep -F "\"country\/ocean\":\"$country\"" $WORKING_DIR/country_summaries.jsonl > $WORKING_DIR/$file_name

    query_id=$(python src/tools/generateQueryId.py -t "geo:country/ocean:$country" -e "full")
    reduced_summary=$(cat $WORKING_DIR/$file_name | python src/tools/generateReducedSummary.py)
    printf "$query_id\t$reduced_summary\n" >> $WORKING_DIR/reduced_country_summaries.jsonl

    jq -c ".aggregates = {}" $WORKING_DIR/$file_name >> $WORKING_DIR/filtered_country_summaries.jsonl
done < <(awk -v size_limit="$SIZE_LIMIT" '{ if (length($0) > size_limit) print }' $WORKING_DIR/country_summaries.jsonl | jq -r '."country/ocean"')

# Step 2.2 Generate institution summary
python src/ETL/extract_institution_summary.py --summary_file $WORKING_DIR/institution_summaries.jsonl < $WORKING_DIR/bold_singlepane_public_export.jsonl

touch $WORKING_DIR/reduced_institution_summaries.jsonl $WORKING_DIR/filtered_institution_summaries.jsonl
while IFS= read -r inst; do
    file_name="inst_$(echo "$inst" | sed -r 's/[^a-zA-Z0-9]+/-/g').json"
    grep -F "\"inst\":\"$inst\"" $WORKING_DIR/institution_summaries.jsonl > $WORKING_DIR/$file_name

    query_id=$(python src/tools/generateQueryId.py -t "inst:name:$inst" -e "full")
    reduced_summary=$(cat $WORKING_DIR/$file_name | python src/tools/generateReducedSummary.py)
    printf "$query_id\t$reduced_summary\n" >> $WORKING_DIR/reduced_institution_summaries.jsonl

    jq -c ".aggregates = {}" $WORKING_DIR/$file_name >> $WORKING_DIR/filtered_institution_summaries.jsonl
done < <(awk -v size_limit="$SIZE_LIMIT" '{ if (length($0) > size_limit) print }' $WORKING_DIR/institution_summaries.jsonl | jq -r '.inst')

# Step 2.3 Generate sequence run site summary
python src/ETL/extract_sequence_run_site_summary.py --summary_file $WORKING_DIR/sequence_run_site_summaries.jsonl < $WORKING_DIR/bold_singlepane_public_export.jsonl

touch $WORKING_DIR/reduced_sequence_run_site_summaries.jsonl $WORKING_DIR/filtered_sequence_run_site_summaries.jsonl
while IFS= read -r seq_run_site; do
    file_name="seq_run_site_$(echo "$seq_run_site" | sed -r 's/[^a-zA-Z0-9]+/-/g').json"
    grep -F "\"sequence_run_site\":\"$seq_run_site\"" $WORKING_DIR/sequence_run_site_summaries.jsonl > $WORKING_DIR/$file_name

    query_id=$(python src/tools/generateQueryId.py -t "inst:seqsite:$seq_run_site" -e "full")
    reduced_summary=$(cat $WORKING_DIR/$file_name | python src/tools/generateReducedSummary.py)
    printf "$query_id\t$reduced_summary\n" >> $WORKING_DIR/reduced_sequence_run_site_summaries.jsonl

    jq -c ".aggregates = {}" $WORKING_DIR/$file_name >> $WORKING_DIR/filtered_sequence_run_site_summaries.jsonl
done < <(awk -v size_limit="$SIZE_LIMIT" '{ if (length($0) > size_limit) print }' $WORKING_DIR/sequence_run_site_summaries.jsonl | jq -r '.sequence_run_site')

# Step 2.4 Generate bin summary
(python src/ETL/extract_bin_summary.py < $WORKING_DIR/bold_singlepane_public_export.jsonl | jq -c 'sort_by(.counts.sequences) | reverse | .[0:2000] | .[]') > $WORKING_DIR/bin_summaries.jsonl

touch $WORKING_DIR/reduced_bin_summaries.jsonl $WORKING_DIR/filtered_bin_summaries.jsonl
while IFS= read -r bin; do
    file_name="bin_$(echo "$bin" | sed -r 's/[^a-zA-Z0-9]+/-/g').json"
    grep -F "\"bin_uri\":\"$bin\"" $WORKING_DIR/bin_summaries.jsonl > $WORKING_DIR/$file_name

    query_id=$(python src/tools/generateQueryId.py -t "bin:uri:$bin" -e "full")
    reduced_summary=$(cat $WORKING_DIR/$file_name | python src/tools/generateReducedSummary.py)
    printf "$query_id\t$reduced_summary\n" >> $WORKING_DIR/reduced_bin_summaries.jsonl

    jq -c ".aggregates = {}" $WORKING_DIR/$file_name >> $WORKING_DIR/filtered_bin_summaries.jsonl
done < <(awk -v size_limit="$SIZE_LIMIT" '{ if (length($0) > size_limit) print }' $WORKING_DIR/bin_summaries.jsonl | jq -r '.bin_uri')

# Step 2.5 Generate dataset summary
python src/ETL/extract_dataset_summary.py --summary_file $WORKING_DIR/dataset_summaries.jsonl < $WORKING_DIR/bold_singlepane_public_export.jsonl

touch $WORKING_DIR/reduced_dataset_summaries.jsonl $WORKING_DIR/filtered_dataset_summaries.jsonl
while IFS= read -r dataset; do
    file_name="dataset_$(echo "$dataset" | sed -r 's/[^a-zA-Z0-9]+/-/g').json"
    grep -F "\"dataset.code\":\"$dataset\"" $WORKING_DIR/dataset_summaries.jsonl > $WORKING_DIR/$file_name

    query_id=$(python src/tools/generateQueryId.py -t ""recordsetcode:code:$dataset"" -e "full")
    reduced_summary=$(cat $WORKING_DIR/$file_name | python src/tools/generateReducedSummary.py)
    printf "$query_id\t$reduced_summary\n" >> $WORKING_DIR/reduced_dataset_summaries.jsonl

    jq -c ".aggregates = {}" $WORKING_DIR/$file_name >> $WORKING_DIR/filtered_dataset_summaries.jsonl
done < <(awk -v size_limit="$SIZE_LIMIT" '{ if (length($0) > size_limit) print }' $WORKING_DIR/dataset_summaries.jsonl | jq -r '."dataset.code"')

# Step 2.6 Generate primer summary
python src/ETL/extract_primer_summary.py --summary_file $WORKING_DIR/primer_summaries.jsonl < $WORKING_DIR/bold_singlepane_public_export.jsonl

touch $WORKING_DIR/reduced_primer_summaries.jsonl $WORKING_DIR/filtered_primer_summaries.jsonl
while IFS= read -r primer; do
    file_name="primer_$(echo "$primer" | sed -r 's/[^a-zA-Z0-9]+/-/g').json"
    grep -F "\"name\":\"$primer\"" $WORKING_DIR/primer_summaries.jsonl > $WORKING_DIR/$file_name

    query_id="null"
    reduced_summary=$(cat $WORKING_DIR/$file_name | python src/tools/generateReducedSummary.py)
    printf "$query_id\t$reduced_summary\n" >> $WORKING_DIR/reduced_primer_summaries.jsonl

    jq -c ".aggregates = {}" $WORKING_DIR/$file_name >> $WORKING_DIR/filtered_primer_summaries.jsonl
done < <(awk -v size_limit="$SIZE_LIMIT" '{ if (length($0) > size_limit) print }' $WORKING_DIR/primer_summaries.jsonl | jq -r '.name')

# Step 3: Sanitize registry documents
jq -c '. | select(.name != "")' $WORKING_DIR/bold_institution_registry.jsonl > $WORKING_DIR/bold_institution_registry_filtered.jsonl
mv $WORKING_DIR/bold_institution_registry_filtered.jsonl $WORKING_DIR/bold_institution_registry.jsonl

# Handling utf-8 encoding
iconv -f 'iso-8859-1' -t UTF-8 $WORKING_DIR/bold_institution_registry.jsonl > $WORKING_DIR/bold_institution_registry.utf8.jsonl
mv $WORKING_DIR/bold_institution_registry.utf8.jsonl $WORKING_DIR/bold_institution_registry.jsonl
iconv -f 'iso-8859-1' -t UTF-8 $WORKING_DIR/bold_taxonomy_registry.jsonl > $WORKING_DIR/bold_taxonomy_registry.utf8.jsonl
mv $WORKING_DIR/bold_taxonomy_registry.utf8.jsonl $WORKING_DIR/bold_taxonomy_registry.jsonl

# Step 4: Generate special summaries that use registries
python src/ETL/extract_taxonomy_summary.py --registry_file $WORKING_DIR/bold_taxonomy_registry.jsonl --summary_file $WORKING_DIR/taxonomy_summaries.jsonl < $WORKING_DIR/bold_singlepane_public_export.jsonl
