from ast import AnnAssign
from ast import AST
from ast import ClassDef
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
#[allow(unused_imports)]
#[allow(unused_variables)]
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use pyo3::exceptions;
use pyo3::PyObjectProtocol;
use pyo3::types::{PyBytes, PyType, IntoPyDict, PyString, PyAny};
use pyo3::create_exception;
use pyo3::PyMappingProtocol;
use pyo3::ffi::Py_TYPE;
use pyo3::AsPyPointer;
use pyo3::ffi;
use pyo3::type_object::{PyTypeInfo, PyTypeCreate};

use serde::{Deserialize, Serialize};

use std::ops::Deref;
use std::fmt;
"""

STRUCT_PREFIX = """
impl AsPyPointer for {name} {{
    fn as_ptr(&self) -> *mut ffi::PyObject {{
        ref_to_ptr(self)
    }}
}}

#[pyclass(subclass)]
#[derive(Serialize, Deserialize, Clone)]
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
        let gil = GILGuard::acquire();
        let py = gil.python();
        Ok(format!("{name}({args})", {attrs}))
    }}
"""

DISPLAY_IMPL = """
impl fmt::Debug for {name} {{
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {{
        let gil = GILGuard::acquire();
        let py = gil.python();
        write!(f, "{{}}", format!("{name}({args})", {attrs}))
    }}
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
pub fn loads<'a>(s: PyObject, py: Python) -> PyResult<Classes> {
    let bytes = if let Ok(string) = s.cast_as::<PyString>(py) {
        Ok(string.as_bytes())
    } else if let Ok(bytes) = s.cast_as::<PyBytes>(py) {
        Ok(bytes.as_bytes())
    } else {
        let ty = unsafe {
            let p = s.as_ptr();
            let tp = Py_TYPE(p);
            PyType::from_type_ptr(py, tp)
        };
        if ty.name() == "bytearray" {
            let locals = [("bytesobj", s)].into_py_dict(py);
            let bytes = py.eval("bytes(bytesobj)", None, Some(&locals))?.downcast_ref::<PyBytes>()?;
            Ok(bytes.as_bytes())
        } else {
            Err(exceptions::ValueError::py_err(format!("loads() takes only str, bytes, or bytearray, got {}", ty)))
        }
    }?;
    match serde_json::from_slice(bytes) {
        Ok(v) => Ok(v),
        Err(e) => Err(JSONParseError::py_err(e.to_string()))
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
pub fn dumps(c: PyObject, py: Python) -> PyResult<String> {
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
#[allow(dead_code)]
#[allow(non_snake_case)]
#[warn(unused_variables)]
mod serde_py_wrapper {{
    use pyo3::prelude::*;
    use pyo3::type_object::{{PyTypeCreate, PyTypeInfo}};
    use serde::{{Serialize, Serializer, Deserialize, Deserializer}};
    pub fn serialize<S, T>(obj: &Py<T>, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
        T: Serialize + PyTypeInfo,
    {{
        let gil = Python::acquire_gil();
        let py = gil.python();
        let o = obj.as_ref(py);
        o.serialize(serializer)
    }}
    pub fn deserialize<'de, D, T>(deserializer: D) -> Result<Py<T>, D::Error>
    where
        D: Deserializer<'de>,
        T: PyTypeCreate + PyTypeInfo + Deserialize<'de>,
    {{
        let gil = Python::acquire_gil();
        let py = gil.python();
        let o = T::deserialize(deserializer)?;
        Ok(Py::new(py, o).unwrap())
    }}
}}


#[derive(Serialize, Deserialize)]
#[serde(transparent)]
pub struct PyWrapper<T>
where
    T: Serialize + fmt::Debug + PyTypeInfo + PyTypeCreate + Clone,
{{
    #[serde(bound(deserialize = "T: Deserialize<'de>"))]
    #[serde(with = "serde_py_wrapper")]
    inner: Py<T>,
}}

impl<T> PyWrapper<T>
where
    T: Serialize + fmt::Debug + PyTypeInfo + PyTypeCreate + Clone,
{{
    fn new(p: Py<T>) -> Self {{
        Self {{ inner: p }}
    }}
}}


impl<T> Clone for PyWrapper<T>
where
    T: Serialize + fmt::Debug + PyTypeInfo + PyTypeCreate + Clone,
{{
    fn clone(&self) -> Self {{
        let gil = GILGuard::acquire();
        let py = gil.python();
        PyWrapper::new(self.inner.clone_ref(py))
    }}
}}

impl<T> fmt::Debug for PyWrapper<T>
where
    T: Serialize + fmt::Debug + PyTypeInfo + PyTypeCreate + Clone,
{{
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {{
        let gil = Python::acquire_gil();
        let py = gil.python();
        let o = self.inner.as_ref(py);
        write!(f, "{{:?}}", o)
    }}
}}

impl<T> IntoPyObject for PyWrapper<T>
where
    T: Serialize + fmt::Debug + PyTypeInfo + PyTypeCreate + Clone,
{{
    fn into_object(self, py: Python) -> PyObject {{
        self.inner.into_object(py)
    }}
}}

impl<T> ToPyObject for PyWrapper<T>
where
    T: Serialize + fmt::Debug + PyTypeInfo + PyTypeCreate + Clone,
{{
    fn to_object(&self, py: Python) -> PyObject {{
        self.inner.to_object(py)
    }}
}}

impl<'source, T> FromPyObject<'source> for PyWrapper<T>
where
    T: AsPyPointer + Serialize + fmt::Debug + PyTypeInfo + PyTypeCreate + Clone,
{{
    fn extract(ob: &'source PyAny) -> PyResult<Self> {{
        Ok(PyWrapper::new(ob.extract()?))
    }}
}}

fn ref_to_ptr<T>(t: &T) -> *mut ffi::PyObject
where
    T: PyTypeInfo,
{{
    unsafe {{ (t as *const _ as *mut u8).offset(-T::OFFSET) as *mut _ }}
}}

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

SIMPLE_TYPE_MAP = {"str": "String", "int": "i64", "bool": "bool"}

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

    def convert(self, n: AST) -> str:
        """Turn types like List[str] into types like Vec<String>"""
        if isinstance(n, Name):
            return self._convert_simple(n.id)
        if isinstance(n, Subscript):
            return f'{CONTAINER_TYPE_MAP[n.value.id]}<{self.convert(n.slice.value)}>'

    def _convert_simple(self, typ: str) -> str:
        """Utility method to convert Python annotations to Rust types"""
        if typ in self.classes:
            return f"PyWrapper<{typ}>"
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
        self.write(LIB_USES)
        self.generic_visit(n)
        module = self.config.filename
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
        if self.config.debug:
            print(f"Generated Rust for: {self.config.filename}")

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
                annotation = self.convert(item.annotation)
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
        repr_args = ", ".join(f"{name}={{{name}:?}}" for name in attributes)
        names = ", ".join(f"{name} = self.{name}" if not typ.startswith('Py<')
                          else f"{name} = self.{name}.as_ref(py).deref()"
                          for name, typ in attributes.items())
        self.write(DUNDER_REPR.format(name=n.name, args=repr_args, attrs=names))
        self.writeline("}")
        self.write(DISPLAY_IMPL.format(name=n.name, args=repr_args, attrs=names))


def gen_bindings(src: str, config: Config) -> str:
    visitor = StubVisitor(config)
    mod = parse(src)
    assert isinstance(mod, Module)
    return visitor.generate_lib(mod)
