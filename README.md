# Abserde

Leveraging [serde](https://serde.rs/) to make fast JSON serializers/deserializers for Python.

The main idea is you feed in a Python stub and get a fast JSON parser implemented in Rust.

Note this is basically just a proof of concept/toy right now.


# Roadmap

1. `json` module compatibility

2. Benchmark and optimize

3. Support more than JSON??

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