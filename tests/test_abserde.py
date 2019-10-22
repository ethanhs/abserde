import json
import time

import orjson
import pytest
import ujson

try:
    import multiclass
except ImportError as e:
    print("You must run the tests from the environment with all of the examples built.")
    raise e

@pytest.mark.benchmark(
    group="dumps",
    max_time=5.0,
    timer=time.perf_counter,
    disable_gc=True,
    warmup=False,
)
def test_multiclass_dumps_speed(benchmark):
    n = multiclass.Test(4211, 4)
    benchmark(multiclass.dumps, n)

@pytest.mark.benchmark(
    group="loads",
    max_time=5.0,
    timer=time.perf_counter,
    disable_gc=True,
    warmup=False,
)
def test_multiclass_loads_speed(benchmark):
    n = multiclass.Test(4211, 4)
    s = multiclass.dumps(n)
    benchmark(multiclass.loads, s)

@pytest.mark.benchmark(
    group="loads",
    max_time=5.0,
    timer=time.perf_counter,
    disable_gc=True,
    warmup=False,
)
def test_orjson_loads_speed(benchmark):
    n = multiclass.Test(4211, 4)
    s = multiclass.dumps(n)
    benchmark(orjson.loads, s)

@pytest.mark.benchmark(
    group="dumps",
    max_time=5.0,
    timer=time.perf_counter,
    disable_gc=True,
    warmup=False,
)
def test_orjson_dumps_speed(benchmark):
    n = multiclass.Test(4211, 4)
    d = orjson.loads(multiclass.dumps(n))
    benchmark(orjson.dumps, d)

@pytest.mark.benchmark(
    group="loads",
    max_time=5.0,
    timer=time.perf_counter,
    disable_gc=True,
    warmup=False,
)
def test_ujson_loads_speed(benchmark):
    n = multiclass.Test(4211, 4)
    s = multiclass.dumps(n)
    benchmark(ujson.loads, s)

@pytest.mark.benchmark(
    group="dumps",
    max_time=5.0,
    timer=time.perf_counter,
    disable_gc=True,
    warmup=False,
)
def test_ujson_dumps_speed(benchmark):
    n = multiclass.Test(4211, 4)
    d = ujson.loads(multiclass.dumps(n))
    benchmark(ujson.dumps, d)

@pytest.mark.benchmark(
    group="loads",
    max_time=5.0,
    timer=time.perf_counter,
    disable_gc=True,
    warmup=False,
)
def test_json_loads_speed(benchmark):
    n = multiclass.Test(4211, 4)
    s = multiclass.dumps(n)
    benchmark(json.loads, s)

@pytest.mark.benchmark(
    group="dumps",
    max_time=5.0,
    timer=time.perf_counter,
    disable_gc=True,
    warmup=False,
)
def test_json_dumps_speed(benchmark):
    n = multiclass.Test(4211, 4)
    d = json.loads(multiclass.dumps(n))
    benchmark(json.dumps, d)
