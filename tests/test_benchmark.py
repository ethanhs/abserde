import json
import time

import orjson
import pytest
import ujson

try:
    import multiclass
    import twitter
except ImportError as e:
    print("You must run the tests from the environment with all of the examples built.")
    raise e


@pytest.mark.benchmark(
    group="dumps", max_time=5.0, timer=time.perf_counter, disable_gc=True, warmup=False,
)
def test_abserde_dumps_speed(benchmark):
    n = multiclass.Test(4211, 4)
    benchmark(n.dumps)


@pytest.mark.benchmark(
    group="loads", max_time=5.0, timer=time.perf_counter, disable_gc=True, warmup=False,
)
def test_abserde_loads_speed(benchmark):
    n = multiclass.Test(4211, 4)
    s = multiclass.dumps(n)
    benchmark(multiclass.Test.loads, s)


@pytest.mark.benchmark(
    group="loads", max_time=5.0, timer=time.perf_counter, disable_gc=True, warmup=False,
)
def test_orjson_loads_speed(benchmark):
    n = multiclass.Test(4211, 4)
    s = multiclass.dumps(n)
    benchmark(orjson.loads, s)


@pytest.mark.benchmark(
    group="dumps", max_time=5.0, timer=time.perf_counter, disable_gc=True, warmup=False,
)
def test_orjson_dumps_speed(benchmark):
    n = multiclass.Test(4211, 4)
    d = orjson.loads(multiclass.dumps(n))
    benchmark(orjson.dumps, d)


@pytest.mark.benchmark(
    group="loads", max_time=5.0, timer=time.perf_counter, disable_gc=True, warmup=False,
)
def test_ujson_loads_speed(benchmark):
    n = multiclass.Test(4211, 4)
    s = multiclass.dumps(n)
    benchmark(ujson.loads, s)


@pytest.mark.benchmark(
    group="dumps", max_time=5.0, timer=time.perf_counter, disable_gc=True, warmup=False,
)
def test_ujson_dumps_speed(benchmark):
    n = multiclass.Test(4211, 4)
    d = ujson.loads(multiclass.dumps(n))
    benchmark(ujson.dumps, d)


@pytest.mark.benchmark(
    group="loads", max_time=5.0, timer=time.perf_counter, disable_gc=True, warmup=False,
)
def test_json_loads_speed(benchmark):
    n = multiclass.Test(4211, 4)
    s = multiclass.dumps(n)
    benchmark(json.loads, s)


@pytest.mark.benchmark(
    group="dumps", max_time=5.0, timer=time.perf_counter, disable_gc=True, warmup=False,
)
def test_json_dumps_speed(benchmark):
    n = multiclass.Test(4211, 4)
    d = json.loads(multiclass.dumps(n))
    benchmark(json.dumps, d)


@pytest.mark.benchmark(
    group="twitter_loads", max_time=5.0, timer=time.perf_counter, disable_gc=True, warmup=False,
)
def test_abserde_twitter_loads_speed(benchmark):
    with open('tests/twitter.json', encoding='utf-8') as f:
        j = f.read()
    benchmark(twitter.File.loads, j)


@pytest.mark.benchmark(
    group="twitter_loads", max_time=5.0, timer=time.perf_counter, disable_gc=True, warmup=False,
)
def test_ujson_twitter_loads_speed(benchmark):
    with open('tests/twitter.json', encoding='utf-8') as f:
        j = f.read()
    benchmark(ujson.loads, j)


@pytest.mark.benchmark(
    group="twitter_dumps", max_time=5.0, timer=time.perf_counter, disable_gc=True, warmup=False,
)
def test_abserde_twitter_dumps_speed(benchmark):
    with open('tests/twitter.json', encoding='utf-8') as f:
        j = f.read()
    data = twitter.File.loads(j)
    benchmark(data.dumps)


@pytest.mark.benchmark(
    group="twitter_dumps", max_time=5.0, timer=time.perf_counter, disable_gc=True, warmup=False,
)
def test_ujson_twitter_dumps_speed(benchmark):
    with open('tests/twitter.json', encoding='utf-8') as f:
        j = f.read()
    data = ujson.loads(j)
    benchmark(ujson.dumps, data)
