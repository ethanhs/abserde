import os
import subprocess
import sys
from distutils.dir_util import copy_tree
from pathlib import Path

from abserde.config import Config


def generate_crate(mod: str, config: Config) -> None:
    dir = Path.cwd() / "build" / "abserde"
    template_dir = Path(__file__).parent / "template_crate"
    crate_name = config.filename
    crate_dir = dir / crate_name
    copy_tree(str(template_dir), str(crate_dir))
    with open(crate_dir / "Cargo.toml.in") as c:
        src = c.read()
        formatted = src.format(file=crate_name, name=config.name, email=config.email)
        if config.debug:
            print("Cargo.toml:")
            print(formatted)
    with open(crate_dir / "Cargo.toml", "w") as w:
        w.write(formatted)

    with open(crate_dir / "src" / "lib.rs", "w+") as lib:
        lib.write(mod)
    cmd = ["maturin", "build", "-i", sys.executable, "--manylinux", "1-unchecked"]
    env = os.environ.copy()
    if not config.debug:
        cmd.append("--release")
        env['RUSTFLAGS'] = "-C target-cpu=native"
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=crate_dir, env=env)
    sys.stdout.write(p.stdout)
    sys.stdout.write(b'\n')
    sys.stderr.write(p.stderr)
    sys.stderr.write(b'\n')
    wheelhouse = crate_dir / "target" / "wheels"
    if config.debug:
        print("Generated wheel")
        print(*wheelhouse.iterdir())
    built_wheel = Path.cwd() / "dist"
    copy_tree(str(wheelhouse), str(built_wheel))
