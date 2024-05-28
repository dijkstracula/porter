from porter.ast.sorts.visitor import Visitor as SortVisitor
from porter.ast import terms, Binding

from porter.quantifiers.bounds import VarBounds, NumericInterval, AppIteration

from porter.pp import Doc, Text, Nil
from porter.pp.utils import soft_line

from typing import Optional


def var_bounds_to_doc(q: VarBounds) -> Doc:
    match q:
        case AppIteration(_, app, var_decls):
            return Text(app.relsym) + Text(".iterator")
        case NumericInterval(_, lo, hi):
            lo_doc = Nil()
            hi_doc = Nil()
            match lo:
                case i if isinstance(i, int):
                    lo_doc = Text(str(i))
                case terms.Constant(_, rep) | terms.Var(_, rep):
                    lo_doc = Text(rep)
            match hi:
                case i if isinstance(i, int):
                    hi_doc = Text(str(i))
                case terms.Constant(_, rep) | terms.Var(_, rep):
                    hi_doc = Text(rep)
            return Text(f"Range(") + lo_doc + Text(", ") + hi_doc + Text(")")
    raise Exception(q)


def iterate_through_varbounds(vbs: list[Binding[VarBounds]], expr: Doc, combinator: str) -> Doc:
    if len(vbs) == 0:
        return expr

    ret = Nil()
    for b in vbs:
        ret = ret + var_bounds_to_doc(b) + Text(f".{combinator}({b.var_name} => ") + soft_line

    ret = ret + expr

    for _ in vbs:
        ret = ret + Text(")")
    return ret


class IteratorDef(SortVisitor[Doc]):
    # TODO: can we elide those .boxed() calls in cases where the types do not require it?

    def bool(self):
        return Text("Bool().iterator")

    def bv(self, name: str, width: int):
        return Text(name)

    def enum(self, name: str, discriminants: list[str]):
        return Text(name)

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return Text(name)
