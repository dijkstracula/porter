from ivy import ivy_ast as iast
from ivy import ivy_module as imod
from ivy import logic as ilog

from porter.ivy import Position
from dataclasses import dataclass
from typing import Optional


# Sorts


@dataclass(frozen=True)
class Sort:
    pass


@dataclass(frozen=True)
class Uninterpreted(Sort):
    sort_name: str


@dataclass(frozen=True)
class Bool(Sort):
    pass


@dataclass(frozen=True)
class Native(Sort):
    posn: Position
    fmt: str  # TODO: in Ivy this is a NativeCode
    args: list  # TODO: of what?


@dataclass(frozen=True)
class Number(Sort):
    sort_name: str
    lo_range: Optional[int]
    hi_range: Optional[int]

    @staticmethod
    def int_sort():
        return Number("int", None, None)

    @staticmethod
    def nat_sort():
        return Number("nat", 0, None)

    def name(self):
        return self.sort_name


@dataclass(frozen=True)
class BitVec(Sort):
    width: int


@dataclass(frozen=True)
class Enum(Sort):
    sort_name: str
    discriminants: tuple[str, ...]


@dataclass(frozen=True)
class Function(Sort):
    domain: list[Sort]
    range: Sort


@dataclass(frozen=True)
class Record(Sort):
    name: str
    fields: dict[str, Sort]


@dataclass(frozen=True)
class Top(Sort):
    pass


def strip_prefixes(prefixes: list[str], sep: str, s: str) -> str:
    prefix = sep.join(prefixes) + sep
    if s.startswith(prefix):
        return s[len(prefix):]
    return s


def record_from_ivy(im: imod.Module, name: str) -> Record:
    if name not in im.sort_destructors:
        raise Exception(f"is {name} the name of a class?")

    fields = {}
    for c in im.sort_destructors[name]:
        field_name = c.name.rsplit(".", 1)[-1]
        #field_name = strip_prefixes([name], ".", c.name)
        field_sort = from_ivy(c.sort)
        assert isinstance(field_sort, Function)
        fields[field_name] = field_sort.range

    # Ivy will flatten out methods for us.
    # actions = []
    # for (action_name, action) in im.actions.items():
    #    if not action_name.startswith(name):
    #        continue
    #    action_name = strip_prefixes([name], ".", action_name)
    #    action = action_def_from_ivy(im, action_name, action)
    #    actions.append(Binding(action_name, action))

    return Record(name, fields)


def from_ivy(sort) -> Sort:
    if hasattr(sort, "name"):
        name = sort.name
        if name == "bool":
            return Bool()
        if name == "int":
            return Number.int_sort()
        if name == "nat":
            return Number.nat_sort()
        if isinstance(sort, ilog.UninterpretedSort):
            return Uninterpreted(name)
        if isinstance(sort, ilog.EnumeratedSort):
            discriminants = tuple([str(x) for x in sort.extension])
            return Enum(name, discriminants)
    if hasattr(sort, "sort"):
        return from_ivy(sort.sort)
    if isinstance(sort, ilog.FunctionSort):
        domain = [from_ivy(s) for s in sort.domain]
        ret = from_ivy(sort.range)
        return Function(domain, ret)
    if isinstance(sort, iast.NativeType):
        native_code = sort.args[0]
        assert isinstance(native_code, iast.NativeCode)
        native_blob = native_code.code.strip()
        args = [str(arg) for arg in sort.args[1:]]
        return Native(Position.from_ivy(sort.lineno), native_blob, args)
    if isinstance(sort, ilog.TopSort):
        return Top()
    raise Exception(f"TODO {type(sort)}")
