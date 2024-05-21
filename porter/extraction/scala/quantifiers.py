from porter.ast.sorts.visitor import Visitor as SortVisitor
from porter.ast import terms

from porter.quantifiers.bounds import VarBounds, NumericInterval, AppIteration

from porter.pp import Doc, Text, Nil
from porter.pp.utils import soft_line

from typing import Optional


def var_bounds_to_doc(q: VarBounds) -> Doc:
    match q:
        case AppIteration(_, app, var_decls):
            return Text(app.relsym) + Text(".iter() /* TODO */")
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
            return Text(f"IntStream.rangeClosed(") + lo_doc + Text(", ") + hi_doc + Text(").boxed()")
    raise Exception(q)


def iterate_through_varbounds(vbs: list[VarBounds], expr: Doc) -> Doc:
    if len(vbs) == 0:
        return expr

    ret = Nil()
    for b in vbs[:-1]:
        ret = ret + var_bounds_to_doc(b) + Text(f".flatMap({b.var_name} -> ") + soft_line
    ret = ret + var_bounds_to_doc(vbs[-1]) + Text(f".map({vbs[-1].var_name} -> ") + soft_line

    ret = ret + expr

    for _ in vbs:
        ret = ret + Text(")")
    return ret


class IteratorDef(SortVisitor[Doc]):
    # TODO: can we elide those .boxed() calls in cases where the types do not require it?

    def bool(self):
        return Text("Stream.of(false, true).boxed()")

    def bv(self, name: str, width: int):
        return self.numeric(name, 0, 2 ** width)

    def enum(self, name: str, discriminants: list[str]):
        return Text(f"Stream.of({name}.values())")

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        # I think this is safe because if we didn't have both bounds
        # then Ivy should have yelled at us already.
        if not lo:
            lo_str = "Integer.MIN_VALUE"
        else:
            lo_str = str(lo)
        if not hi:
            hi_str = "Integer.MAX_VALUE"
        else:
            hi_str = str(hi)

        return Text(f"IntStream.rangeClosed({lo_str}, {hi_str}).boxed()")
