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
    args: list[Sort]


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
    sort_name: str
    fields: dict[str, Sort]


@dataclass(frozen=True)
class Top(Sort):
    pass


def strip_prefixes(prefixes: list[str], sep: str, s: str) -> str:
    prefix = sep.join(prefixes) + sep
    if s.startswith(prefix):
        return s[len(prefix):]
    return s


def range_from_ivy(sort: ilog.RangeSort) -> Number:
    assert isinstance(sort.lb, ilog.Const)
    assert isinstance(sort.ub, ilog.Const)
    if not sort.lb.name.isnumeric():
        # raise Exception("TODO: haven't handled non-constant values in ranges yet")
        lo = None
    else:
        lo = int(sort.lb.name)
    if not sort.ub.name.isnumeric():
        # raise Exception("TODO: haven't handled non-constant values in ranges yet")
        hi = None
    else:
        hi = int(sort.ub.name)

    return Number(sort.name, lo, hi)


def sorts_with_members(im: imod.Module) -> dict[str, ilog.Const]:
    ret = {}
    for name, fields in im.sort_destructors.items():
        # XXX: what is the right way to do this? im.aliases does not have all aliases?
        if name.endswith(".t"):
            ret[name[:-2]] = fields
        ret[name] = fields
    return ret


def record_from_ivy(im: imod.Module, name: str) -> Record:
    fields = {}
    for c in sorts_with_members(im)[name]:
        field_name = c.name.rsplit(".", 1)[-1]
        # field_name = strip_prefixes([name], ".", c.name)
        field_sort = from_ivy(im, c.sort)
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


def from_ivy(im: imod.Module, sort) -> Sort:
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
        return from_ivy(im, sort.sort)
    if hasattr(sort, "rep"):
        if sort.rep in im.sig.interp:
            sort_or_name = im.sig.interp[sort.rep]
            if isinstance(sort_or_name, str):
                assert sort_or_name.startswith("bv[")
                width = int(sort_or_name[3:-1])
                return BitVec(width)
            else:
                return from_ivy(im, sort_or_name)
        else:
            return Uninterpreted(sort.rep)  # XXX ???
    if isinstance(sort, ilog.FunctionSort):
        domain = [from_ivy(im, s) for s in sort.domain]
        ret = from_ivy(im, sort.range)
        return Function(domain, ret)
    if isinstance(sort, ilog.RangeSort):
        return range_from_ivy(sort)
    if isinstance(sort, iast.NativeType):
        native_code = sort.args[0]
        assert isinstance(native_code, iast.NativeCode)

        # Slightly annoying: NativeTypes' args are Atoms.
        native_blob = native_code.code.strip()
        args = [from_ivy(im, arg) for arg in sort.args[1:]]
        return Native(Position.from_ivy(sort.lineno), native_blob, args)
    if isinstance(sort, ilog.TopSort):
        return Top()
    raise Exception(f"TODO {type(sort)}")
