[![Actions Status](https://github.com/ethanhs/abserde/workflows/CI/badge.svg)](https://github.com/ethanhs/abserde/actions)

# Abserde

Leveraging [serde](https://serde.rs/) to make fast JSON serializers/deserializers for Python.

The main idea is you feed in a Python stub declaring the interface you want and get a fast JSON parser implemented in Rust.

Note it is still early days, but I am working on making this usable.


# Roadmap

1. Design API and features (basically done)

2. Write documentation (basically done)

3. Write tests

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
# they print nicely
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

# LICENSE

Abserde is dual licensed Apache 2.0 and MIT.

# Code of Conduct

Abserde is under the Contributor Covenant Code of Conduct. I will enforce it.

# Thank you

Thanks to the amazing efforts of the developers of Rust, Serde, and PyO3. Without any of these, this project would not be possible.
