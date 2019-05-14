from ast import AnnAssign
from ast import ClassDef
from ast import Index
from ast import Module
from ast import Name
from ast import NodeVisitor
from ast import parse
from ast import Subscript
from typing import Dict
from typing import List
from typing import NoReturn
from typing import Optional

from abserde.config import Config


LIB_USES = """
#![feature(specialization)]
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use pyo3::exceptions;
use pyo3::PyObjectProtocol;
use pyo3::types::{PyBytes, PyString};
use pyo3::create_exception;
use pyo3::PyMappingProtocol;
use pyo3::ffi::Py_TYPE;
use pyo3::types::PyType;
use pyo3::AsPyPointer;
use pyo3::types::IntoPyDict;

use serde::{Deserialize, Serialize};
"""

STRUCT_PREFIX = """
#[pyclass]
#[derive(Serialize, Deserialize)]
pub struct {name} {{
"""

PYCLASS_PREFIX = """
#[pymethods]
impl {name} {{
"""

IMPL_NEW_PREFIX = """
    #[new]
    fn new(obj: &PyRawObject, {args}) {{
        obj.init({{
            {name} {{
"""

IMPL_NEW_SUFFIX = """
            }
        });
    }
"""

OBJECT_PROTO = """
#[pyproto]
impl<'p> PyObjectProtocol<'p> for {name} {{
"""

DUNDER_STR = """
    fn __str__(&self) -> PyResult<String> {
        match serde_json::to_string(&self) {
            Ok(v) => Ok(v),
            Err(e) => Err(exceptions::ValueError::py_err(e.to_string()))
        }
    }
"""

DUNDER_BYTES = """
    fn __bytes__(&self) -> PyResult<PyObject> {
        let gil = GILGuard::acquire();
        match serde_json::to_vec(&self) {
            Ok(v) => Ok(PyBytes::new(gil.python(), &v).into()),
            Err(e) => Err(exceptions::ValueError::py_err(e.to_string()))
        }
    }
"""

DUNDER_REPR = """
    fn __repr__(&self) -> PyResult<String> {{
        Ok(format!("{name}({args})", {attrs}))
    }}
"""

MAPPING_IMPL = """
#[pyproto]
impl<'p> PyMappingProtocol<'p> for {name} {{
    fn __len__(&'p self) -> PyResult<usize> {{
        Ok({len}usize)
    }}

    fn __getitem__(&'p self, key: String) -> PyResult<PyObject> {{
        let gil = GILGuard::acquire();
        let py = gil.python();
        match key.as_ref() {{
            {getitems}
            &_ => Err(exceptions::AttributeError::py_err(format!("No such item {{}}", key))),
        }}
    }}

    fn __setitem__(&'p mut self, key: String, value: PyObject) -> PyResult<()> {{
        let gil = GILGuard::acquire();
        let py = gil.python();
        match key.as_ref() {{
            {setitems}
            &_ => Err(exceptions::AttributeError::py_err(format!("No such item {{}}", key))),
        }}
    }}

}}
"""

ENUM_IMPL_PREFIX = """
impl IntoPyObject for Classes {
    fn into_object(self, py: Python) -> PyObject {
        match self {
"""

ENUM_IMPL_SUFFIX = """
        }
    }
}


#[derive(Serialize, Deserialize)]
#[serde(untagged)]
pub enum Classes {
"""

LOADS_IMPL = """
/// loads(s, /)
/// --
///
/// Parse s into an abserde class.
/// s can be a str, byte, or bytearray.
#[pyfunction]
pub fn loads<'a>(s: PyObject) -> PyResult<Classes> {
    let gil = Python::acquire_gil();
    let py = gil.python();
    if let Ok(string) = s.cast_as::<PyString>(py) {
        match serde_json::from_slice(string.as_bytes()) {
            Ok(v) => Ok(v),
            Err(e) => Err(JSONParseError::py_err(e.to_string()))
        }
    } else if let Ok(bytes) = s.cast_as::<PyBytes>(py) {
        match serde_json::from_slice(bytes.as_bytes()) {
            Ok(v) => Ok(v),
            Err(e) => Err(JSONParseError::py_err(e.to_string()))
        }
    } else {
        let ty = unsafe {
            let p = s.as_ptr();
            let tp = Py_TYPE(p);
            PyType::from_type_ptr(py, tp)
        };
        if ty.name() == "bytearray" {
            let locals = [("bytesobj", s)].into_py_dict(py);
            let bytes = py.eval("bytes(bytesobj)", None, Some(&locals))?.downcast_ref::<PyBytes>()?;
            match serde_json::from_slice(bytes.as_bytes()) {
                Ok(v) => Ok(v),
                Err(e) => Err(JSONParseError::py_err(e.to_string()))
            }
        } else {
            Err(exceptions::ValueError::py_err(format!("loads() takes only str, bytes, or bytearray, got {}", ty)))
        }
    }

}
"""  # noqa

DUMPS_IMPL_PREFIX = """
fn dumps_impl<T>(c: &T) -> PyResult<String>
where T: Serialize
{
    match serde_json::to_string(c) {
        Ok(v) => Ok(v),
        Err(e) => Err(exceptions::ValueError::py_err(e.to_string()))
    }
}

/// dumps(s, /)
/// --
///
/// Dump abserde class s into a str.
/// For bytes, call bytes() on the object.
#[pyfunction]
pub fn dumps(c: PyObject) -> PyResult<String> {
    let gil = Python::acquire_gil();
    let py = gil.python();
"""
DUMPS_FOR_CLS = """
    if let Ok(o) = c.extract::<&{cls}>(py) {{
        dumps_impl(o)
    }}"""
DUMPS_IMPL_SUFFIX = """
    else {
        Err(exceptions::ValueError::py_err("Invalid type for dumps"))
    }
}
"""

MODULE_PREFIX = """

create_exception!({module}, JSONParseError, exceptions::ValueError);

#[pymodule]
fn {module}(_py: Python, m: &PyModule) -> PyResult<()> {{
"""

MODULE_SUFFIX = """
    m.add_wrapped(wrap_pyfunction!(loads))?;
    m.add_wrapped(wrap_pyfunction!(dumps))?;
    Ok(())
}
"""

SIMPLE_TYPE_MAP = {"str": "String", "int": "i32", "bool": "bool"}

CONTAINER_TYPE_MAP = {"List": "Vec", "Optional": "Option"}


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
        self.classes: List[str] = []

    def convert(self, typ: str, container: Optional[str] = None) -> str:
        """Utility method to convert Python annotations to Rust types"""
        if container is not None:
            try:
                return f"{CONTAINER_TYPE_MAP[container]}<{SIMPLE_TYPE_MAP[typ]}>"
            except KeyError:
                invalid_type(typ, container)
        else:
            if typ in self.classes:
                return typ
            try:
                return f"{SIMPLE_TYPE_MAP[typ]}"
            except KeyError:
                invalid_type(typ)

    def generate_lib(self, n: Module) -> str:
        self.visit(n)
        return self.lib

    def write(self, s: str) -> None:
        self.lib += s

    def writeline(self, s: str) -> None:
        self.lib += s + "\n"

    def visit_Module(self, n: Module) -> None:
        if self.config.debug:
            print(f"Generated Rust for: {self.config.filename}")
        # TODO: multiple class support?
        self.write(LIB_USES)
        self.generic_visit(n)
        module = self.config.filename.replace(".py", "")
        self.write(ENUM_IMPL_PREFIX)
        for cls in self.classes:
            self.writeline(" " * 12 + f"Classes::{cls}Class(v) => v.into_object(py),")
        self.write(ENUM_IMPL_SUFFIX)
        for cls in self.classes:
            self.writeline(" " * 4 + f"{cls}Class({cls}),")
        self.writeline("}")
        self.write(LOADS_IMPL)
        self.write(DUMPS_IMPL_PREFIX)
        self.write(" else ".join(DUMPS_FOR_CLS.format(cls=cls) for cls in self.classes))
        self.write(DUMPS_IMPL_SUFFIX)
        self.write(MODULE_PREFIX.format(module=module))
        for cls in self.classes:
            self.writeline(" " * 4 + f"m.add_class::<{cls}>()?;")
        self.write(MODULE_SUFFIX)

    def visit_ClassDef(self, n: ClassDef) -> None:
        decorators = n.decorator_list
        if (
            len(decorators) != 1
            or not isinstance(decorators[0], Name)
            or decorators[0].id != "abserde"
        ):
            if self.config.debug:
                print("Skipping class {n.name}")
            self.generic_visit(n)
            return
        # First, we write out the struct and its members
        self.write(STRUCT_PREFIX.format(name=n.name))
        self.classes.append(n.name)
        attributes: Dict[str, str] = {}
        for item in n.body:
            if isinstance(item, AnnAssign):
                assert isinstance(item.target, Name)
                name = item.target.id
                if isinstance(item.annotation, Name):
                    annotation = self.convert(item.annotation.id)
                elif isinstance(item.annotation, Subscript):
                    assert isinstance(item.annotation.value, Name)
                    assert isinstance(item.annotation.slice, Index)
                    assert isinstance(item.annotation.slice.value, Name)
                    annotation = self.convert(
                        item.annotation.slice.value.id, container=item.annotation.value.id
                    )
                attributes[name] = annotation
                self.writeline(" " * 4 + "#[pyo3(get, set)]")
                self.writeline(" " * 4 + f"pub {name}: {annotation},")
        self.writeline("}")

        # Then we write out the class implementation.
        self.write(PYCLASS_PREFIX.format(name=n.name))
        args = ", ".join(f"{name}: {typ}" for name, typ in attributes.items())
        self.write(IMPL_NEW_PREFIX.format(args=args, name=n.name))
        for name in attributes:
            self.writeline(" " * 16 + f"{name}: {name},")
        self.write(IMPL_NEW_SUFFIX)
        self.writeline("}")
        getitem = ("\n" + " " * 12).join(
            f'"{name}" => Ok(self.{name}.to_object(py)),' for name in attributes
        )
        setitem = ("\n" + " " * 12).join(
            f'"{name}" => Ok(self.{name} = value.extract(py).unwrap()),' for name in attributes
        )
        self.write(
            MAPPING_IMPL.format(
                name=n.name, len=len(attributes), getitems=getitem, setitems=setitem
            )
        )

        self.write(OBJECT_PROTO.format(name=n.name))
        self.write(DUNDER_STR)
        self.write(DUNDER_BYTES)
        repr_args = ", ".join(f"{name}: {{{name}:?}}" for name in attributes)
        names = ", ".join(f"{name} = self.{name}" for name in attributes)
        self.write(DUNDER_REPR.format(name=n.name, args=repr_args, attrs=names))
        self.writeline("}")


def gen_bindings(src: str, config: Config) -> str:
    visitor = StubVisitor(config)
    mod = parse(src)
    assert isinstance(mod, Module)
    return visitor.generate_lib(mod)
