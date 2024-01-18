from typing import Generic, TypeVar

from .sorts import *
from .terms import *

T = TypeVar("T")


class UnimplementedASTNodeHandler(Exception):
    def __init__(self, cls):
        self.cls = cls

    def __str__(self):
        return f"Unimplemented AST visitor for {str(self.cls)}"


# noinspection PyMethodMayBeStatic,PyShadowingBuiltins
class Visitor(Generic[T]):
    def visit_sort(self, sort: Sort) -> T:
        match sort:
            case Bool():
                return self.bool()
            case BitVec(width):
                return self.bv(width)
            case Enum(discs):
                return self.enum(discs)
            case Function(domain, range):
                self.begin_function(sort)
                domain = [self.visit_sort(sort, d) for d in domain]
                range = self.visit_sort(range)
                return self.finish_function(sort, domain, range)
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

    def begin_function(self, node: Function):
        pass

    def finish_function(self, node: Function, domain: list[T], range: T) -> T:
        raise UnimplementedASTNodeHandler(Function)

    def numeric(self, lo: Optional[int], hi: Optional[int]):
        raise UnimplementedASTNodeHandler(Numeric)

    def uninterpreted(self) -> T:
        raise UnimplementedASTNodeHandler(Uninterpreted)

    #

    def visit_expr(self, node: Expr) -> T:
        match node:
            case Apply(_, relsym, args):
                self.begin_apply(node)
                relsym = self.visit_expr(relsym)
                args = [self.visit_expr(arg) for arg in args]
                return self.finish_apply(node, relsym, args)
            case BinOp(_, lhs, _op, rhs):
                self.begin_binop(node)
                lhs_ret = self.visit_expr(lhs)
                rhs_ret = self.visit_expr(rhs)
                return self.finish_binop(node, lhs_ret, rhs_ret)
            case Constant(_, rep):
                return self.constant(rep)
            case Exists(_, vars, expr):
                self.begin_exists(node)
                vars = [Binding(b.name, self._visit_sort(b.decl)) for b in vars]
                expr = self.visit_expr(expr)
                return self.finish_exists(node, vars, expr)
            case Forall(_, vars, expr):
                self.begin_forall(node)
                vars = [Binding(b.name, self._visit_sort(b.decl)) for b in vars]
                expr = self.visit_expr(expr)
                return self.finish_forall(node, vars, expr)
            case Ite(_, test, then, els):
                self.begin_ite(node)
                test = self.visit_expr(test)
                then = self.visit_expr(then)
                els = self.visit_expr(els)
                return self.finish_ite(node, test, then, els)
            case Some(_, vars, fmla, _strat):
                self.begin_some(node)
                vars = [self.visit_expr(var) for var in vars]
                fmla = self.visit_expr(fmla)
                return self.finish_some(node, vars, fmla)
            case UnOp(_, _op, expr):
                self.begin_unop(node)
                expr = self.visit_expr(expr)
                return self.finish_unop(node, expr)
        raise Exception(f"TODO: {node}")

    # Terminals

    def constant(self, rep: str) -> T:
        raise UnimplementedASTNodeHandler(Constant)

    # Non-terminal exprs

    def begin_apply(self, node: Apply):
        pass

    def finish_apply(self, node: Apply, relsym_ret: T, args_ret: list[T]) -> T:
        raise UnimplementedASTNodeHandler(Apply)

    def begin_binop(self, node: BinOp):
        pass

    def finish_binop(self, node: BinOp, lhs_ret: T, rhs_ret: T) -> T:
        raise UnimplementedASTNodeHandler(BinOp)

    def begin_exists(self, node: Exists):
        pass

    def finish_exists(self, node: Exists, vars: list[Binding[T]], expr: T):
        raise UnimplementedASTNodeHandler(Exists)

    def begin_forall(self, node: Forall):
        pass

    def finish_forall(self, node: Forall, vars: list[T], expr: T):
        raise UnimplementedASTNodeHandler(Forall)

    def begin_ite(self, node: Ite):
        pass

    def finish_ite(self, node: Ite, test: T, then: T, els: T) -> T:
        raise UnimplementedASTNodeHandler(Ite)

    def begin_some(self, node: Some):
        pass

    def finish_some(self, node: Some, vars: list[T], fmla: T):
        raise UnimplementedASTNodeHandler(Some)

    def begin_unop(self, node: UnOp):
        pass

    def finish_unop(self, node: UnOp, expr: T):
        raise UnimplementedASTNodeHandler(Some)
