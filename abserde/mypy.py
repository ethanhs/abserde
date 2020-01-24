from mypy.errors import Errors
from mypy.nodes import (
     ARG_POS, MDEF, Argument, AssignmentStmt, Block, Decorator, Expression, FuncDef,
     FuncItem, NameExpr, OverloadedFuncDef, PassStmt, PlaceholderNode, SymbolTableNode, TempNode,
     TypeInfo, Var,
)
from mypy.options import Options
from mypy.types import AnyType, CallableType, Instance, Type, TypeType, TypeVarDef, TypeOfAny, NoneType, UnboundType, get_proper_type
from mypy.plugin import (
    AttributeContext, ClassDefContext, DynamicClassDefContext, FunctionContext, MethodContext, Plugin,
)
from mypy.util import get_unique_redefinition_name
from mypy.typevars import fill_typevars
from mypy.semanal import set_callable_name

from typing import Optional, Callable, List

from dataclasses import dataclass

from itertools import zip_longest

def add_decorated_method(
        ctx: ClassDefContext,
        name: str,
        args_list: List[List[Argument]],
        return_types: List[Type],
        self_types: Optional[List[Optional[Type]]] = None,
        tvar_defs: Optional[List[Optional[TypeVarDef]]] = None,
        decorators_list: Optional[List[List[Expression]]] = None,
) -> None:
    """Adds a new method to a class.

    This was copied from mypy.plugins.common and modified to support decorators and overloads.
    """
    self_types = self_types if self_types else []
    tvar_defs = tvar_defs if tvar_defs else []
    decorators_list = decorators_list if decorators_list else []
    info = ctx.cls.info

    function_type = ctx.api.named_type('__builtins__.function')

    functions: List[FuncDef] = []
    for args, return_type, self_type, tvar_def, decorators in zip_longest(args_list, return_types, self_types, tvar_defs, decorators_list):
        self_type = self_type or fill_typevars(info)
        args = [Argument(Var('self'), self_type, None, ARG_POS)] + args
        arg_types, arg_names, arg_kinds = [], [], []
        for arg in args:
            assert arg.type_annotation, 'All arguments must be fully typed.'
            arg_types.append(arg.type_annotation)
            arg_names.append(arg.variable.name)
            arg_kinds.append(arg.kind)
        signature = CallableType(arg_types, arg_kinds, arg_names, return_type, function_type)
        if tvar_def:
            signature.variables = [tvar_def]

        func = FuncDef(name, args, Block([PassStmt()]))
        func.info = info
        func.type = set_callable_name(signature, func)
        func._fullname = info.fullname + '.' + name
        func.line = info.line
        if not isinstance(self_type, Instance):
            func.is_class = True
        if decorators:
            decorator = Decorator(func, decorators, Var(name))
            functions.append(decorator)
        else:
            functions.append(func)
        
    if len(functions) == 1:
        # a single decorated function such as:
        # @classmethod
        # def t(cls, blah: int) -> Type: ...
        method = functions[0]
    elif len(functions) > 2:
        # otherwise these should be an overloaded method
        method = OverloadedFuncDef(functions)
    else:
        # if there are 2 functions something is wrong
        ctx.api.fail(f"Failed to generate decorated method {name} on class {ctx.cls.fullname}.", ctx.cls)
        return
    
    # Remove any previously generated methods with the same name
    # to avoid clashes and problems in the semantic analyzer
    if name in info.names:
        sym = info.names[name]
        if sym.plugin_generated and isinstance(sym.node, FuncDef):
            ctx.cls.defs.body.remove(sym.node)

    # NOTE: we would like the plugin generated node to dominate, but we still
    # need to keep any existing definitions so they get semantically analyzed.
    if name in info.names:
        # Get a nice unique name instead.
        r_name = get_unique_redefinition_name(name, info.names)
        info.names[r_name] = info.names[name]

    info.names[name] = SymbolTableNode(MDEF, method, plugin_generated=True)
    info.defn.defs.body.append(method)


@dataclass
class AbserdeArg:
    name: str
    type: Type

    def to_argument(self) -> Argument:
        return Argument(
            variable=Var(self.name, self.type),
            type_annotation=self.type,
            initializer=None,
            kind=ARG_POS,
        )

def make_abserde_class(ctx: ClassDefContext) -> None:
    cls = ctx.cls
    info = cls.info
    members = cls.defs.body
    args = []
    for elem in members:
        # check the members are just pairs of names and types, e.g. `a: int`     
        if not (
            isinstance(elem, AssignmentStmt)
            and len(elem.lvalues) == 1
            and isinstance(elem.lvalues[0], NameExpr)
            and isinstance(elem.rvalue, TempNode)  # TempNode means no rvalue
            and (elem.new_syntax == True)
        ):
            if isinstance(elem, (FuncItem, Decorator)):
                continue
            ctx.api.fail("Abserde member variables can only be typed variables using PEP 526 syntax.", node)
            return
        sym = cls.info.names.get(elem.lvalues[0].name)
        if sym is None:
            ctx.api.defer()
            return
        node = sym.node
        if isinstance(node, PlaceholderNode):
            # This node is not ready yet.
            ctx.api.defer()
            return
        if node.type is None:
            ctx.api.defer()
            return
        args.append(AbserdeArg(elem.lvalues[0].name, sym.type))
    # now we know the definition is sane, generate the needed magic.
    # for an abserde class, we need to generate:
    # __init__
    # __getitem__, __setitem__
    # cls.loads, instance.dumps
    # maybe some other things like __repr__?
    str_ty = ctx.api.named_type('__builtins__.str')
    add_decorated_method(ctx, '__init__', [[arg.to_argument() for arg in args]], [NoneType()])
    add_decorated_method(ctx, 'dumps', [[]], [str_ty])
    instance_ty = UnboundType(cls.name, [], original_str_expr=cls.name, original_str_fallback=cls.name)
    add_decorated_method(ctx, 'loads',  [[Argument(variable=Var('s', str_ty), type_annotation=str_ty, initializer=None, kind=ARG_POS)]], [instance_ty], self_types=[AnyType(TypeOfAny.unannotated)], decorators_list=[[NameExpr('classmethod')]])


class AbserdePlugin(Plugin):
    def __init__(self, options: Options) -> None:
        super().__init__(options)

    def get_class_decorator_hook(self, fullname: str) -> Optional[Callable[[ClassDefContext], None]]:
        if fullname == 'abserde.abserde':
            return make_abserde_class
        else:
            return None

def plugin(version):
    return AbserdePlugin