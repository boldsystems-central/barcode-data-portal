import sys
import pathlib

sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
from dao import _get_cb_cluster

from couchbase.options import QueryOptions


def test_query_1(cluster):
    query = "SELECT * FROM `BCDM`._default.`primary` WHERE processid = 'AAPL001-10'"
    result = cluster.query(query, QueryOptions(metrics=True))
    for _ in result.rows():
        pass
    return result


def test_query_2(cluster):
    query = (
        "SELECT * FROM `BCDM`._default.`primary` WHERE `country/ocean` = 'Venezuela'"
    )
    result = cluster.query(query, QueryOptions(metrics=True))
    for _ in result.rows():
        pass
    return result


def test_query_3(cluster):
    query = "SELECT * FROM `BCDM`._default.`primary` WHERE ANY code IN bold_recordset_code_arr SATISFIES code = 'DATASET-DHJDR1' END"
    result = cluster.query(query, QueryOptions(metrics=True))
    for _ in result.rows():
        pass
    return result


def test_queries():
    cluster = _get_cb_cluster()

    results1 = test_query_1(cluster)
    print(
        f"Test 1: {int(results1.metadata().metrics().result_count())} row(s) in {results1.metadata().metrics().execution_time().total_seconds()} seconds"
    )

    results2 = test_query_2(cluster)
    print(
        f"Test 2: {int(results2.metadata().metrics().result_count())} row(s) in {results2.metadata().metrics().execution_time().total_seconds()} seconds"
    )

    results3 = test_query_3(cluster)
    print(
        f"Test 3: {int(results3.metadata().metrics().result_count())} row(s) in {results3.metadata().metrics().execution_time().total_seconds()} seconds"
    )


if __name__ == "__main__":
    test_queries()
