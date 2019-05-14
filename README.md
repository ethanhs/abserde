# Abserde

Leveraging [serde](https://serde.rs/) to make fast JSON (or more? see #2 on the roadmap) serializers/deserializers for Python.

The main idea is you feed in a Python stub declaring the interface you want from  and get a fast JSON parser implemented in Rust.

Note this is basically just an experiment right now, but I hope to make it production ready soon(tm).


# Roadmap

1. Benchmark and optimize

2. Write mypy plugin

3. Write documentation

999. Support more than JSON??

# Usage

You need [poetry](https://github.com/sdispater/poetry#installation) for now until packages are built.

You need [rust](https://rustup.rs/) to use this tool (but not for the final extension!)

Then you can then
```
poetry install
```

And then

```
poetry run abserde <your_stub.pyi>
```

Note for right now that previous wheels are removed from the `abserde_wheels/` directory each run.