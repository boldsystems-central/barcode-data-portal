# Tools

## BOLD Public Portal Caching

- `generateStatsCache.py`
  - Generate general stats cache
  - `python src/tools/generateStatsCache.py`
- `generateSummaryCache.py`
  - Generate summary cache for specific queries
  - `python src/tools/generateSummaryCache.py -i src/tools/summary_cache_queries.json`
- `generateTaxMapCache.py`
  - Generate taxonomy map cache for specific queries
  - `python src/tools/generateTaxMapCache.py -i src/tools/tax_map_cache_queries.json`

## Map Generation Tool

- `generateMap.py`
  - Choose supported map templates and generate maps with highlighted points and other features
    - `worldmap_5000.png`
  - `python src/tools/generateMap.py worldmap_5000.png OUTPUT_IMG --sizefactor 1 --crop [-90, -180, 90, 180] --alpha 180 --sortorder lh`

## Data Schema Tool

- `dataMapConverter.py`
  - Converts JSONL file from one data schema to another
  - `python src/tools/dataMapConverter.py -i INPUT_FILE -o OUTPUT_FILE -m MAP_FILE`

## Miscellaneous Tools

- `generateQueryId.py`
  - Generates query ID for given triplet query and extent
  - `python src/tools/generateQueryId.py -t "geo:country/ocean:Brazil" -e "full"`
- `generateReducedSummary.py`
  - Generates condensed query for `/api/summary` caches
  - `cat summary.json | python src/tools/generateReducedSummary.py`

## Couchbase Connection Tools

- `test_couchbase_connect.py`
  - Test Couchbase connection and run queries

```bash
# Run Python Tests
python src/tools/test_couchbase_connect.py

# Test 1: 0 row(s) in 0.044344 seconds
# Test 2: 47 row(s) in 0.016921 seconds
# Test 3: 99 row(s) in 0.021354 seconds
```

**Note**: A lack of an error is a success

- `test_couchbase_download.py`
  - Test Couchbase connection and download documents to tempfile
  - `python src/tools/test_couchbase_download.py`
