from ast import AnnAssign
from ast import AST
from ast import ClassDef
from ast import Module
from ast import Name
from ast import NodeVisitor
from ast import parse
from ast import Subscript
from typing import Dict
from typing import Tuple
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
use pyo3::type_object::PyTypeInfo;
use pyo3::PyTryFrom;
use pyo3::types::PyDict;

use serde::{Deserialize, Serialize};

use std::ops::Deref;
use std::fmt;
"""

STRUCT_PREFIX = """

impl<'source> pyo3::FromPyObject<'source> for {name} {{
    fn extract(ob: &'source PyAny) -> pyo3::PyResult<{name}> {{
        let cls: &{name} = PyTryFrom::try_from(ob)?;
        Ok(cls.clone())
    }}
}}

#[pyclass(dict)]
#[derive(Serialize, Deserialize, Clone)]
pub struct {name} {{
"""

PYCLASS_PREFIX = """
#[pymethods]
impl {name} {{
    fn dumps(&self) -> PyResult<String> {{
        dumps_impl(self)
    }}

    #[classmethod]
    fn loads(_cls: &PyType, s: &PyString) -> PyResult<Self> {{
        match serde_json::from_str::<{name}>(&s.to_string_lossy()) {{
            Ok(v) => Ok(v),
            Err(e) => Err(exceptions::ValueError::py_err(e.to_string())),
        }}
    }}
"""

IMPL_NEW_PREFIX = """
    #[new]
    fn new({args}) -> Self {{
        {{
            {name} {{
"""

IMPL_NEW_SUFFIX = """
            }
        }
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
impl IntoPy<PyObject> for Classes {
    fn into_py(self, py: Python) -> PyObject {
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
/// loads(s, /)
/// --
///
/// Parse s into an abserde class.
/// s can be a str, byte, or bytearray.
#[pyfunction]
pub fn loads<'a>(s: PyObject, py: Python) -> PyResult<Classes> {{
    let bytes = if let Ok(string) = s.cast_as::<PyString>(py) {{
        string.as_bytes()
    }} else if let Ok(bytes) = s.cast_as::<PyBytes>(py) {{
        Ok(bytes.as_bytes())
    }} else {{
        let ty = unsafe {{
            let p = s.as_ptr();
            let tp = Py_TYPE(p);
            PyType::from_type_ptr(py, tp)
        }};
        if ty.name() == "bytearray" {{
            let locals = [("bytesobj", s)].into_py_dict(py);
            let bytes = py.eval("bytes(bytesobj)", None, Some(&locals))?.downcast_ref::<PyBytes>()?;
            Ok(bytes.as_bytes())
        }} else {{
            Err(exceptions::ValueError::py_err(format!("loads() takes only str, bytes, or bytearray, got {{}}", ty)))
        }}
    }}?;
    match serde_json::from_slice::<Classes>(bytes) {{
        Ok(v) => Ok(v),
        Err(e) => Err(JSONParseError::py_err(e.to_string())),
    }}
}}

#[derive(Serialize, Deserialize, Clone)]
#[serde(transparent)]
pub struct JsonValue(serde_json::Value);

impl fmt::Debug for JsonValue {{
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {{
        write!(f, "{{}}", self.0)
    }}
}}

impl IntoPy<PyObject> for JsonValue {{
    fn into_py(self, py: Python) -> PyObject {{
        match self.0 {{
            serde_json::Value::Null => py.None(),
            serde_json::Value::Bool(b) => b.into_py(py),
            serde_json::Value::Number(n) => {{
                if n.is_i64() {{
                    // should never fail since we just checked it
                    n.as_i64().unwrap().into_py(py)
                }} else {{
                    // should never fail since it isn't an integer?
                    n.as_f64().unwrap().into_py(py)
                }}
            }},
            serde_json::Value::String(s) => s.into_py(py),
            serde_json::Value::Array(v) => {{
                let vec: Vec<JsonValue> = v.iter().map(|i| JsonValue(i.clone()).into_py(py)).collect();
                vec.into_py(py)
            }},
            serde_json::Value::Object(m) => {{
                let d = PyDict::new(py);
                for (k, v) in m.iter() {{
                    let key = PyString::new(py, &*k);
                    let value: PyObject = JsonValue(v.clone()).into_py(py);
                    d.set_item(key, value).unwrap();
                }}
                d.into_py(py)
            }}
        }}
    }}
}}

impl<'source> pyo3::FromPyObject<'source> for JsonValue {{
    fn extract(ob: &'source PyAny) -> pyo3::PyResult<JsonValue> {{
        if let Ok(s) = ob.extract::<String>() {{
            Ok(JsonValue(serde_json::Value::String(s)))
        }} else if let Ok(n) = ob.extract::<i64>() {{
            Ok(JsonValue(serde_json::Value::Number(n.into())))
        }} else if let Ok(f) = ob.extract::<f64>() {{
            let flt = match serde_json::Number::from_f64(f) {{
                Some(v) => Ok(v),
                None => Err(JSONParseError::py_err("Cannot convert NaN or inf to JSON")),
            }};
            Ok(JsonValue(serde_json::Value::Number(flt?)))
        }} else if let Ok(b) = ob.extract::<bool>() {{
            Ok(JsonValue(serde_json::Value::Bool(b)))
        }} else if let Ok(l) = ob.extract::<Vec<JsonValue>>() {{
            Ok(JsonValue(serde_json::Value::Array(l.into_iter().map(|i| i.0).collect())))
        }} else if let Ok(d) = ob.extract::<&PyDict>() {{
            let mut m = serde_json::Map::with_capacity(d.len());
            for (k, v) in d.iter() {{
                let key: String = k.extract()?;
                let value: JsonValue = v.extract()?;
                m.insert(key, value.0);
            }}
            Ok(JsonValue(serde_json::Value::Object(m)))
        }} else if ob.extract::<PyObject>()?.is_none() {{
            Ok(JsonValue(serde_json::Value::Null))
        }} else {{
            Err(JSONParseError::py_err("Could not convert object to JSON"))
        }}
    }}
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

SIMPLE_TYPE_MAP = {"str": "String", "int": "i64", "bool": "bool", "float": "f64", "Any": "JsonValue"}

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
        self.classes_attrs: Set[Tuple[str, str]] = set()

    def convert(self, n: AST) -> str:
        """Turn types like List[str] into types like Vec<String>"""
        if isinstance(n, Name):
            return self._convert_simple(n.id)
        if isinstance(n, Subscript):
            return f'{CONTAINER_TYPE_MAP[n.value.id]}<{self.convert(n.slice.value)}>'

    def _convert_simple(self, typ: str) -> str:
        """Utility method to convert Python annotations to Rust types"""
        if typ in self.classes:
            return f"{typ}"
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
            self.writeline(" " * 12 + f"Classes::{cls}Class(v) => v.into_py(py),")
        self.write(ENUM_IMPL_SUFFIX)
        for cls in self.classes:
            self.writeline(" " * 4 + f"{cls}Class({cls}),")
        self.writeline("}")
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
        attributes: Set[Tuple[str, str]] = set()
        for item in n.body:
            if isinstance(item, AnnAssign):
                assert isinstance(item.target, Name)
                name = item.target.id
                annotation = self.convert(item.annotation)
                self.classes_attrs.add((name, annotation))
                attributes.add((name, annotation))
                self.writeline(" " * 4 + "#[pyo3(get, set)]")
                self.writeline(" " * 4 + f"pub {name}: {annotation},")
        self.writeline("}")
        self.classes.append(n.name)
        # Then we write out the class implementation.
        self.write(PYCLASS_PREFIX.format(name=n.name))
        args = ", ".join(f"{name}: {typ}" for name, typ in attributes)
        self.write(IMPL_NEW_PREFIX.format(args=args, name=n.name))
        for pair in attributes:
            name = pair[0]
            self.writeline(" " * 16 + f"{name}: {name},")
        self.write(IMPL_NEW_SUFFIX)
        self.writeline("}")
        getitem = ("\n" + " " * 12).join(
            f'"{name}" => Ok(self.{name}.clone().into_py(py)),' for name, _ in attributes
        )
        setitem = ("\n" + " " * 12).join(
            f'"{name}" => Ok(self.{name} = value.extract(py)?),' for name, _ in attributes
        )
        self.write(
            MAPPING_IMPL.format(
                name=n.name, len=len(attributes), getitems=getitem, setitems=setitem
            )
        )
        self.write(OBJECT_PROTO.format(name=n.name))
        self.write(DUNDER_STR)
        self.write(DUNDER_BYTES)
        repr_args = ", ".join(f"{name}={{{name}:?}}" for name, _ in attributes)
        names = ", ".join(f"{name} = self.{name}" if not typ.startswith('Py<')
                          else f"{name} = self.{name}.as_ref(py).deref()"
                          for name, typ in attributes)
        self.write(DUNDER_REPR.format(name=n.name, args=repr_args, attrs=names))
        self.writeline("}")
        self.write(DISPLAY_IMPL.format(name=n.name, args=repr_args, attrs=names))


def gen_bindings(src: str, config: Config) -> str:
    visitor = StubVisitor(config)
    mod = parse(src)
    assert isinstance(mod, Module)
    return visitor.generate_lib(mod)
