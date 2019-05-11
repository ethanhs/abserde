from __future__ import annotations

import click

from abserde.gen_lib import gen_bindings
from abserde.gen_crate import generate_crate
from abserde.config import Config


@click.command()
@click.argument('file')
@click.option('-d', '--debug', 'debug', is_flag=True, help="Print more output.")
@click.option('-n', '--name', 'name', help="Name for package.")
@click.option('-e', '--email', 'email', help="Email for package.")
def main(file: str, debug: bool, name: str, email: str) -> None:
    config = Config(file, debug, name, email)
    with open(file) as f:
        src = f.read()
    mod = gen_bindings(src, config)
    if config.debug:
        print(mod)
    generate_crate(mod, config)