## DB Files

``` bash
#Command to generate terms and summary
time cat ./db_data/BCDM.jsonl | python3.10 ./src/ETL/extract_terms_and_summary_from_BCDM.py --terms_file ./db_data/terms.jsonl --summary_file ./db_data/summaries.jsonl
``` 
