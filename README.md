[![Actions Status](https://github.com/ethanhs/abserde/workflows/CI/badge.svg)](https://github.com/ethanhs/abserde/actions)

# Abserde

Leveraging [serde](https://serde.rs/) to make fast JSON serializers/deserializers for Python.

The main idea is you feed in a Python stub declaring the interface you want and get a fast JSON parser implemented in Rust.

Note abserde is basically usable, but I have not stablized the API yet.


# Roadmap

1. Design API and features ✅

2. Write documentation ✅

3. Write tests ✅

4. Write mypy plugin

# Usage

You need [poetry](https://github.com/sdispater/poetry#installation) for now until packages are built.

You need [rust nightly](https://rustup.rs/) to use this tool (but not for the final extension!)

Then you can then
```
$ git clone https://github.com/ethanhs/abserde.git
$ cd abserde
$ poetry install
```

And then

```
$ poetry run abserde examples/multiclass.pyi
```

The multiclass stub file looks like this:

```python
from abserde import abserde
from typing import Any

@abserde
class Test:
    room: int
    floor: int


@abserde
class Test2:
    name: Any
    age: int
    foo: Test
```

You should find a wheel which you can install via:
```
$ poetry run pip install dist/multiclass-*.whl
```

And run Python in the environment with:
```
$ poetry run python
```

You should now be able to import the `multiclass` module, which you can use to serialize and deserialize with Python.

```python
# modules are called the name of the stub
>>> import multiclass
# you can load objects from a string as you would expect
>>> t = multiclass.Test.loads('{"room": 3, "floor": 9}')
# and dump them
>>> t.dumps()
'{"room":3,"floor":9}'
# they display nicely
>>> t
Test(room=3, floor=9)
# members can be accessed as attributes
>>> t.room
3
# you can also set them
>>> t.floor = 5
>>> t
Test(room=3, floor=5)
# you can use subscripts if you prefer
>>> t['floor']
5
# you can create instances the usual way
>>> t2 = multiclass.Test2(name='Guido',age=63,foo=t)
>>> t2
Test2(age=39, name=6, foo=Test(room=3, floor=4))
# types annotated Any, such as "name" here, can be any JSON type
# I am not a number, I'm a free man!
>>> t2['name'] = "The Prisoner"
```

# Performance

Initial rough benchmarks (see `tests/test_benchmark.py`) give the following results compared to `ujson`, `orjson` and the stdlib `json`.

```
-------------------------------------------------------------------------------------------- benchmark 'dumps': 4 tests -------------------------------------------------------------------------------------------
Name (time in ns)                   Min                    Max                  Mean                StdDev                Median               IQR             Outliers  OPS (Kops/s)            Rounds  Iterations
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_ujson_dumps_speed         400.0000 (1.0)      36,900.0000 (1.0)        511.3573 (1.0)        642.2686 (1.0)        500.0000 (1.0)      0.0000 (inf)      675;65593    1,955.5797 (1.0)      609757           1
test_abserde_dumps_speed       500.0000 (1.25)     76,100.0000 (2.06)       608.4186 (1.19)       695.1262 (1.08)       600.0000 (1.20)     0.0000 (inf)      223;39768    1,643.6053 (0.84)     185186           1
test_orjson_dumps_speed        800.0000 (2.00)     49,000.0000 (1.33)       929.4947 (1.82)       916.7784 (1.43)       900.0000 (1.80)     0.0000 (inf)      753;78532    1,075.8534 (0.55)     400001           1
test_json_dumps_speed        2,000.0000 (5.00)     41,100.0000 (1.11)     2,290.2692 (4.48)     1,421.9851 (2.21)     2,200.0000 (4.40)     0.0000 (1.0)    1577;139981      436.6299 (0.22)     373135           1
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

--------------------------------------------------------------------------------------------- benchmark 'loads': 4 tests ---------------------------------------------------------------------------------------------
Name (time in ns)                   Min                     Max                  Mean                StdDev                Median                 IQR             Outliers  OPS (Kops/s)            Rounds  Iterations
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_ujson_loads_speed         400.0000 (1.0)       36,800.0000 (1.0)        489.9098 (1.0)        672.4337 (1.0)        500.0000 (1.0)      100.0000 (>1000.0)    269;363    2,041.1920 (1.0)       71634           1
test_abserde_loads_speed       600.0000 (1.50)      62,400.0000 (1.70)       703.8580 (1.44)       732.7207 (1.09)       700.0000 (1.40)     100.0000 (>1000.0)   384;8016    1,420.7411 (0.70)     268818           1
test_orjson_loads_speed        600.0000 (1.50)      54,000.0000 (1.47)       720.7119 (1.47)       819.9132 (1.22)       700.0000 (1.40)       0.0000 (1.0)      761;73156    1,387.5171 (0.68)     277778           1
test_json_loads_speed        2,100.0000 (5.25)     545,100.0000 (14.81)    2,404.9490 (4.91)     1,722.4939 (2.56)     2,300.0000 (4.60)       0.0000 (2.00)   1674;135227      415.8092 (0.20)     409837           1
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------- benchmark 'twitter_dumps': 2 tests ----------------------------------------------------------------------------------------
Name (time in us)                           Min                   Max                  Mean             StdDev                Median                 IQR            Outliers       OPS            Rounds  Iterations
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_abserde_twitter_dumps_speed       919.0000 (1.0)      1,638.9000 (1.0)      1,070.8982 (1.0)      83.7800 (1.17)     1,074.4000 (1.0)      136.3000 (1.62)      1683;24  933.7956 (1.0)        4700           1
test_ujson_twitter_dumps_speed       2,493.6000 (2.71)     3,126.7000 (1.91)     2,611.4613 (2.44)     71.5545 (1.0)      2,593.7500 (2.41)      84.1500 (1.0)        485;49  382.9274 (0.41)       1864           1
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------- benchmark 'twitter_loads': 2 tests ------------------------------------------------------------------------------
Name (time in ms)                       Min               Max              Mean            StdDev            Median               IQR            Outliers       OPS            Rounds  Iterations
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_abserde_twitter_loads_speed     1.3502 (1.0)      2.1092 (1.0)      1.5121 (1.0)      0.0917 (1.0)      1.4928 (1.0)      0.1455 (1.0)        664;13  661.3275 (1.0)        2031           1
test_ujson_twitter_loads_speed       3.5005 (2.59)     4.6023 (2.18)     3.6952 (2.44)     0.1408 (1.54)     3.6511 (2.45)     0.1562 (1.07)       307;44  270.6178 (0.41)       1150           1
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
```


# LICENSE

Abserde is dual licensed Apache 2.0 and MIT.

# Code of Conduct

Abserde is under the Contributor Covenant Code of Conduct. I will enforce it.

# Thank you

Thanks to the amazing efforts of the developers of Rust, Serde, and PyO3. Without any of these, this project would not be possible.
