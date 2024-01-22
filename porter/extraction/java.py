from porter.ast import Binding, sorts, terms
from porter.ast.visitor import Visitor
from porter.pp import Doc, Text, Nest, Concat, Choice

from typing import Optional


class JavaExtractor(Visitor[Doc]):
    # Sorts

    def bool(self):
        raise NotImplementedError()

    def bv(self):
        raise NotImplementedError()

    def enum(self, discriminants: list[str]):
        raise NotImplementedError()

    def _finish_function(self, node: sorts.Function, domain: list[Doc], range: Doc):
        raise NotImplementedError()

    def numeric(self, lo: Optional[int], hi: Optional[int]):
        raise NotImplementedError()

    def uninterpreted(self):
        raise NotImplementedError()

    # Expressions

    def _constant(self, rep: str) -> Doc:
        return Text(rep)

    def _finish_apply(self, node: terms.Apply, relsym_ret: Doc, args_ret: list[Doc]):
        raise NotImplementedError()

    def _finish_binop(self, node: terms.BinOp, lhs_ret: Doc, rhs_ret: Doc):
        raise NotImplementedError()

    def _finish_exists(self, node: terms.Exists, vs: list[Binding[Doc]], expr: Doc):
        raise NotImplementedError()

    def _finish_forall(self, node: terms.Forall, vs: list[Binding[Doc]], expr: Doc):
        raise NotImplementedError()

    def _finish_ite(self, node: terms.Ite, test: Doc, then: Doc, els: Doc):
        raise NotImplementedError()

    def _finish_some(self, none: terms.Some, vs: list[Binding[Doc]], fmla: Doc):
        raise NotImplementedError()

    def _finish_unop(self, node: terms.UnOp, expr: Doc):
        raise NotImplementedError()

    # Actions

    def _finish_assert(self, act: terms.Assert, pred: Doc):
        raise NotImplementedError()

    def _finish_assign(self, act: terms.Assign, lhs: Doc, rhs: Doc):
        raise NotImplementedError()

    def _finish_assume(self, act: terms.Assume, pred: Doc):
        raise NotImplementedError()

    def _finish_call(self, act: terms.Call, app: Doc):
        raise NotImplementedError()

    def _finish_debug(self, act: terms.Debug, args: list[Doc]):
        raise NotImplementedError()

    def _finish_ensures(self, act: terms.Ensures, pred: Doc):
        raise NotImplementedError()

    def _finish_havok(self, act: terms.Havok, modifies: list[Doc]):
        raise NotImplementedError()

    def _finish_if(self, act: terms.If, test: Doc, then: list[Doc], els: Optional[Doc]):
        raise NotImplementedError()

    def _finish_let(self, act: terms.Let, vardecls: list[Binding[Doc]], scope: Doc):
        raise NotImplementedError()

    def _finish_sequence(self, act: terms.Sequence, stmts: list[Doc]):
        raise NotImplementedError()
