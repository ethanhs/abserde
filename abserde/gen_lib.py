from ast import parse, NodeVisitor, Module, ClassDef, dump, AnnAssign, Name, Subscript

from typing import Optional, NoReturn

from abserde.config import Config

__all__ = ['parse_stub']

LIB_USES = '''
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use pyo3::exceptions;

use serde::{Deserialize, Serialize};
'''

PYCLASS_PREFIX = '''
#[pyclass]
#[derive(Serialize, Deserialize)]
pub struct {name} {{
'''

MODULE = '''
#[pyfunction]
pub fn loads(s: &str) -> PyResult<{cls}> {{
    match serde_json::from_str(s) {{
        Ok(v) => Ok(v),
        Err(e) => Err(exceptions::ValueError::py_err(e.to_string()))
    }}
}}

#[pyfunction]
pub fn dumps(c: &{cls}) -> PyResult<String> {{
    match serde_json::to_string(c) {{
        Ok(v) => Ok(v),
        Err(e) => Err(exceptions::ValueError::py_err(e.to_string()))
    }}
}}

#[pymodule]
fn {module}(_py: Python, m: &PyModule) -> PyResult<()> {{
    m.add_class::<{cls}>()?;
    m.add_wrapped(wrap_pyfunction!(loads))?;
    m.add_wrapped(wrap_pyfunction!(dumps))?;
    Ok(())
}}
'''

SIMPLE_TYPE_MAP = {
    "str": "String",
    "int": "i32",
    "bool": "bool",
}

CONTAINER_TYPE_MAP = {
    "List": "Vec",
    "Optional": "Option",
}


class InvalidTypeError(Exception):
    pass


def invalid_type(typ: str, container: Optional[str] = None) -> NoReturn:
    if container is not None:
        msg = f"The type {container}[{typ}] is not valid."
    else:
        msg = f"The type {typ} is not valid."
    raise InvalidTypeError(msg)

class StubVisitor(NodeVisitor):
    def __init__(self, config: Config):
        self.config = config
        self.lib = ""
        self.classes = []

    def convert(self, typ: str, container: Optional[str] = None) -> str:
        """Utility method to convert Python annotations to Rust types"""
        if container is not None:
            try:
                return f'{CONTAINER_TYPE_MAP[container]}<{SIMPLE_TYPE_MAP[typ]}>'
            except KeyError:
                invalid_type(typ, container)
        else:
            try:
                return f'{SIMPLE_TYPE_MAP[typ]}'
            except KeyError:
                invalid_type(typ)

    def generate_lib(self, n: Module) -> str:
        self.visit(n)
        return self.lib

    def write(self, s: str) -> None:
        self.lib += s

    def writeline(self, s: str) -> None:
        self.lib += s + '\n'

    def visit_Module(self, n: Module) -> None:
        if self.config.debug:
            print(f'Generated Rust for: {self.config.filename}')
        # TODO: multiple class support?
        self.write(LIB_USES)
        self.generic_visit(n)
        module = self.config.filename.replace('.py', '')
        self.write(MODULE.format(module=module, cls=self.classes[0]))

    def visit_ClassDef(self, n: ClassDef) -> None:
        self.write(PYCLASS_PREFIX.format(name=n.name))
        self.classes.append(n.name)
        for item in n.body:
            if isinstance(item, AnnAssign):
                name = item.target.id
                if isinstance(item.annotation, Name):
                    annotation = self.convert(item.annotation.id)
                elif isinstance(item.annotation, Subscript):
                    annotation = self.convert(item.annotation.slice.value.id, container=item.annotation.value.id)

                self.writeline(' ' * 4 + f'pub {name}: {annotation},')
        self.writeline('}')

        # TODO: impl


def gen_bindings(src: str, config: Config) -> str:
    visitor = StubVisitor(config)
    return visitor.generate_lib(parse(src))
