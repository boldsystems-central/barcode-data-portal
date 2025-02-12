import sys
import ujson as json


for line in sys.stdin:
    record = json.loads(line)

    print(json.dumps(record) + "\n")
