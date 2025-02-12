#!/bin/bash

# Input: JSONL from stdin
# Output: JSONL to stdout

# Keep records with sequences only
jq -c '. | select(.record_id != null)'
