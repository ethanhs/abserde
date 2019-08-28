from __future__ import annotations

from pathlib import Path

import click

from abserde.config import Config
from abserde.gen_crate import generate_crate
from abserde.gen_lib import gen_bindings


@click.command()
@click.argument("file")
@click.option("-d", "--debug", "debug", is_flag=True, help="Print more output.")
@click.option("-n", "--name", "name", help="Name for package.")
@click.option("-e", "--email", "email", help="Email for package.")
def main(file: str, debug: bool, name: str, email: str) -> None:
    file_name = Path(file).name.replace(".pyi", "").replace(".py", "")
    config = Config(file_name, debug, name, email)
    with open(file) as f:
        src = f.read()
    mod = gen_bindings(src, config)
    if config.debug:
        print(mod)
    generate_crate(mod, config)
