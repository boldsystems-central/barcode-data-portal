import math
import time

from fastapi import APIRouter

from dao import _get_cb_cluster

route = APIRouter(tags=["test"])


@route.get("/test/sum")
async def test_sum(num_1: int, num_2: int):
    """
    Test endpoint to sum to integers and return result.

    - **num_1**: Integer 1
    - **num_2**: Integer 2
    """
    sum = num_1 + num_2

    return {"sum": sum}


@route.get("/test/square")
async def test_square(iterations: int):
    """
    Test endpoint to square integers for a set amount of iterations.
    Will square integers from 0 to iterations - 1 and return time taken

    - **iterations**: Number of square iterations to run
    """
    start = time.time()
    for i in range(iterations):
        _ = i**2
    end = time.time()

    return {"time": end - start, "iterations": iterations}


@route.get("/test/sqrt")
async def test_sqrt(iterations: int):
    """
    Test endpoint to take the square root of integers for a set amount of iterations.
    Will take the square root of integers from 0 to iterations - 1 and return time taken

    - **iterations**: Number of square root iterations to run
    """
    start = time.time()
    for i in range(iterations):
        _ = math.sqrt(i)
    end = time.time()

    return {"time": end - start, "iterations": iterations}
