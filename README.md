# Abserde

Leveraging [serde](https://serde.rs/) to make fast JSON (or more? see #4 on the roadmap) serializers/deserializers for Python.

The main idea is you feed in a Python stub declaring the interface you want from  and get a fast JSON parser implemented in Rust.

Note this is basically just an experiment right now, but I hope to make it production ready soon(tm).


# Roadmap

1. Benchmark and optimize

2. Write mypy plugin

3. Write documentation

999. Support more than JSON??

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
$ cd examples/
$ poetry run abserde nested_example.pyi
```

You should find a wheel which you can install via:
```
$ pip install dist/nested_example-*.whl
```

You should now be able to import the `nested_example` module, which you can use to serialize and deserialize with Python.

# LICENSE

Note that part of the generated code comes from PyO3, the binding library used to make the generated code usable from Python, thus the end product must be compatible with the Apache-2 license (see LICENSE-APACHE-2.0).

# Thank you

Thanks to the amazing efforts of the developers of Rust, Serde, and PyO3. Without any of these, this project would not be possible.