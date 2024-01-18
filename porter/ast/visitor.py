from typing import Generic, TypeVar

from .sorts import *
from .terms import *

T = TypeVar("T")


class UnimplementedASTNodeHandler(Exception):
    def __init__(self, cls: type):
        self.cls = cls

    def __str__(self):
        return f"Unimplemented AST visitor for {self.cls.__module__}.{self.cls.__name__}"


# noinspection PyMethodMayBeStatic,PyShadowingBuiltins
class Visitor(Generic[T]):

    # Sorts

    def visit_sort(self, sort: Sort) -> T:
        match sort:
            case Bool():
                return self.bool()
            case BitVec(width):
                return self.bv(width)
            case Enum(discs):
                return self.enum(discs)
            case Function(domain, range):
                self._begin_function(sort)
                domain = [self.visit_sort(d) for d in domain]
                range = self.visit_sort(range)
                return self._finish_function(sort, domain, range)
            case Numeric(lo, hi):
                return self.numeric(lo, hi)
            case Uninterpreted():
                return self.uninterpreted()
        raise Exception(f"TODO: {sort}")

    def bool(self) -> T:
        raise UnimplementedASTNodeHandler(Bool)

    def bv(self, width: int) -> T:
        raise UnimplementedASTNodeHandler(BitVec)

    def enum(self, discriminants: list[str]):
        raise UnimplementedASTNodeHandler(Enum)

    def _begin_function(self, node: Function):
        pass

    def _finish_function(self, node: Function, domain: list[T], range: T) -> T:
        raise UnimplementedASTNodeHandler(Function)

    def numeric(self, lo: Optional[int], hi: Optional[int]):
        raise UnimplementedASTNodeHandler(Numeric)

    def uninterpreted(self) -> T:
        raise UnimplementedASTNodeHandler(Uninterpreted)

    # Expressions

    def visit_expr(self, node: Expr) -> T:
        match node:
            case Apply(_, relsym, args):
                self._begin_apply(node)
                relsym = self.visit_expr(relsym)
                args = [self.visit_expr(arg) for arg in args]
                return self._finish_apply(node, relsym, args)
            case BinOp(_, lhs, _op, rhs):
                self._begin_binop(node)
                lhs_ret = self.visit_expr(lhs)
                rhs_ret = self.visit_expr(rhs)
                return self._finish_binop(node, lhs_ret, rhs_ret)
            case Constant(_, rep):
                return self._constant(rep)
            case Exists(_, vars, expr):
                self._begin_exists(node)
                vars = [Binding(b.name, self.visit_sort(b.decl)) for b in vars]
                expr = self.visit_expr(expr)
                return self._finish_exists(node, vars, expr)
            case Forall(_, vars, expr):
                self._begin_forall(node)
                vars = [Binding(b.name, self.visit_sort(b.decl)) for b in vars]
                expr = self.visit_expr(expr)
                return self._finish_forall(node, vars, expr)
            case Ite(_, test, then, els):
                self._begin_ite(node)
                test = self.visit_expr(test)
                then = self.visit_expr(then)
                els = self.visit_expr(els)
                return self._finish_ite(node, test, then, els)
            case Some(_, vars, fmla, _strat):
                self._begin_some(node)
                vars = [Binding(b.name, self.visit_sort(b.decl)) for b in vars]
                fmla = self.visit_expr(fmla)
                return self._finish_some(node, vars, fmla)
            case UnOp(_, _op, expr):
                self._begin_unop(node)
                expr = self.visit_expr(expr)
                return self._finish_unop(node, expr)
        raise Exception(f"TODO: {node}")

    def _constant(self, rep: str) -> T:
        raise UnimplementedASTNodeHandler(Constant)

    def _begin_apply(self, node: Apply):
        pass

    def _finish_apply(self, node: Apply, relsym_ret: T, args_ret: list[T]) -> T:
        raise UnimplementedASTNodeHandler(Apply)

    def _begin_binop(self, node: BinOp):
        pass

    def _finish_binop(self, node: BinOp, lhs_ret: T, rhs_ret: T) -> T:
        raise UnimplementedASTNodeHandler(BinOp)

    def _begin_exists(self, node: Exists):
        pass

    def _finish_exists(self, node: Exists, vars: list[Binding[T]], expr: T):
        raise UnimplementedASTNodeHandler(Exists)

    def _begin_forall(self, node: Forall):
        pass

    def _finish_forall(self, node: Forall, vars: list[T], expr: T):
        raise UnimplementedASTNodeHandler(Forall)

    def _begin_ite(self, node: Ite):
        pass

    def _finish_ite(self, node: Ite, test: T, then: T, els: T) -> T:
        raise UnimplementedASTNodeHandler(Ite)

    def _begin_some(self, node: Some):
        pass

    def _finish_some(self, node: Some, vars: list[Binding[T]], fmla: T):
        raise UnimplementedASTNodeHandler(Some)

    def _begin_unop(self, node: UnOp):
        pass

    def _finish_unop(self, node: UnOp, expr: T):
        raise UnimplementedASTNodeHandler(Some)

    # Actions

