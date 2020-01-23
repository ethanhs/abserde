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

Initial rough benchmarks (see `tests/test_benchmark.py`) give the following results:

```
---------------------------------------------------------------------------------------------- benchmark 'dumps': 4 tests ----------------------------------------------------------------------------------------------
Name (time in ns)                      Min                     Max                  Mean                StdDev                Median                 IQR            Outliers  OPS (Kops/s)            Rounds  Iterations
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_ujson_dumps_speed            400.0000 (1.0)       48,100.0000 (1.08)       492.8983 (1.0)        612.5846 (1.0)        500.0000 (1.0)        0.0000 (1.0)    559;141032    2,028.8161 (1.0)      555556           1
test_multiclass_dumps_speed       500.0000 (1.25)      44,600.0000 (1.0)        594.7104 (1.21)       640.0888 (1.04)       600.0000 (1.20)     100.0000 (>1000.0)  602;8771    1,681.4908 (0.83)     413224           1
test_orjson_dumps_speed           800.0000 (2.00)     129,100.0000 (2.89)       892.9659 (1.81)       873.1125 (1.43)       900.0000 (1.80)     100.0000 (>1000.0)  334;7070    1,119.8636 (0.55)     240385           1
test_json_dumps_speed           2,000.0000 (5.00)     136,900.0000 (3.07)     2,262.4586 (4.59)     1,344.7016 (2.20)     2,200.0000 (4.40)     100.0000 (>1000.0)1407;11733      441.9970 (0.22)     393701           1
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------------------------ benchmark 'loads': 4 tests -----------------------------------------------------------------------------------------------
Name (time in ns)                      Min                       Max                  Mean                 StdDev                Median                 IQR            Outliers  OPS (Kops/s)            Rounds  Iterations
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_ujson_loads_speed            400.0000 (1.0)         37,800.0000 (1.0)        480.9942 (1.0)         620.9897 (1.0)        500.0000 (1.0)      100.0000 (1.0)       386;550    2,079.0274 (1.0)      117648           1
test_multiclass_loads_speed       600.0000 (1.50)        45,600.0000 (1.21)       684.0327 (1.42)        686.8092 (1.11)       700.0000 (1.40)     100.0000 (1.00)     381;3059    1,461.9185 (0.70)     234742           1
test_orjson_loads_speed           600.0000 (1.50)     9,113,500.0000 (241.10)     775.2557 (1.61)     27,318.1054 (43.99)      700.0000 (1.40)     100.0000 (1.00)      12;3223    1,289.8970 (0.62)     111359           1
test_json_loads_speed           2,100.0000 (5.25)        54,700.0000 (1.45)     2,335.0432 (4.85)      1,353.3376 (2.18)     2,200.0000 (4.40)     100.0000 (1.00)   1065;12298      428.2576 (0.21)     299402           1
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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
