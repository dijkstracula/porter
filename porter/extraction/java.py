import re

from porter.ast import Binding, sorts, terms

from porter.ast.terms.visitor import Visitor as TermVisitor
from porter.ast.sorts.visitor import Visitor as SortVisitor

from porter.pp import Doc, Text, Line, Nest, Nil, utils
from porter.pp.utils import space

from typing import Optional

semi = Text(";")

soft_open_bracket = Text("{") + utils.soft_line
soft_close_bracket = utils.soft_line + Text("}")


def block(contents: Doc) -> Doc:
    return Text("{") + Line() + Nest(2, contents) + Line() + Text("}")


def canonicalize_identifier(s: str) -> str:
    return s \
        .replace(".", "__") \
        .replace("fml:", "") \
        .replace("ext:", "ext__")


class BoxedSort(SortVisitor[Doc]):
    def bool(self):
        return Text("Boolean")

    def bv(self, name: str, width: int):
        if width > 64:
            raise Exception("BV too wide")
        return Text("Long")

    def enum(self, name: str, discriminants: list[str]):
        return Text(name)

    def _finish_function(self, node: sorts.Function, domain: list[Doc], range: Doc):
        return Text("Action") + Text(str(len(domain) + 1))  # TODO: generics

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return Text("Integer")

    def uninterpreted(self, name: str):
        return Text("Integer")


class UnboxedSort(SortVisitor[Doc]):
    def bool(self):
        return Text("bool")

    def bv(self, name: str, width: int):
        if width > 64:
            raise Exception("BV too wide")
        return Text("long")

    def enum(self, name: str, discriminants: list[str]):
        return Text(name)

    def _finish_function(self, node: sorts.Function, _domain: list[Doc], _range: Doc):
        boxed = BoxedSort()
        type_args = [boxed.visit_sort(s) for s in node.domain + [node.range]]

        cls = Text("Function") + Text(str(len(type_args)))
        return cls + utils.enclosed("<", utils.join(type_args, ", "), ">")

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return Text("int")

    def uninterpreted(self, name: str):
        return Text("int")


class SortDeclaration(SortVisitor[Doc]):
    """Many sorts don't need explicit declarations extracted, but here are the ones that do. """

    def bool(self):
        return Nil()

    def bv(self, name: str, width: int):
        return Nil()

    def enum(self, name: str, discriminants: list[str]):
        discs = utils.join([Text(s) for s in discriminants], utils.soft_comma)
        return Text("public enum ") + Text(name) + space + block(discs)

    def _finish_function(self, node: sorts.Function, domain: list[Doc], range: Doc):
        boxed = BoxedSort()
        type_args = [boxed.visit_sort(s) for s in node.domain + [node.range]]

        cls = Text("Function") + Text(str(len(type_args)))
        return cls + utils.enclosed("<", utils.join(type_args, ", "), ">")

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return Nil()

    def uninterpreted(self, name: str):
        return Nil()


class Extractor(TermVisitor[Doc]):

    @staticmethod
    def action_sig(name: str, decl: terms.ActionDefinition) -> Doc:
        unboxed = UnboxedSort()

        if len(decl.formal_returns) > 1:
            raise Exception("TODO: I don't know how to handle tuples in return types yet")

        if len(decl.formal_returns) == 0:
            ret = Text("void")
        else:
            ret = unboxed.visit_sort(decl.formal_returns[0].decl)

        param_docs = [unboxed.visit_sort(b.decl) + space + Text(b.name) for b in decl.formal_params]
        params = utils.enclosed("(", utils.join(param_docs, ", "), ")")

        return Text("public") + space + ret + space + Text(name) + params

    def extract(self, prog: terms.Program) -> Doc:
        sort_declarer = SortDeclaration()
        unboxed = UnboxedSort()

        self.visit_program(prog)

        sorts = [sort_declarer.visit_sort(s) for name, s in self.sorts.items()]

        var_docs = []
        for binding in self.individuals:
            var = self._constant(binding.name)
            sort = unboxed.visit_sort(binding.decl)
            var_docs.append(sort + space + var + semi)

        action_docs = [b.decl for b in self.actions]

        return utils.join(sorts, "\n") + \
            Line() + \
            utils.join(var_docs, "\n") + \
            Line() + \
            utils.join(self.inits, "\n") + \
            Line() + \
            utils.join(action_docs, "\n")

    # Expressions

    def _constant(self, rep: str) -> Doc:
        return Text(canonicalize_identifier(rep))

    def _var(self, rep: str) -> Doc:
        return Text(canonicalize_identifier(rep))

    def _finish_apply(self, node: terms.Apply, relsym_ret: Doc, args_ret: list[Doc]):
        return relsym_ret + utils.enclosed("(", utils.join(args_ret, ", "), ")")

    def _finish_binop(self, node: terms.BinOp, lhs_ret: Doc, rhs_ret: Doc):
        return lhs_ret + utils.padded(node.op) + rhs_ret

    def _finish_exists(self, node: terms.Exists, vs: list[Binding[Doc]], expr: Doc):
        return Text("Exists (TODO);")

    def _finish_forall(self, node: terms.Forall, vs: list[Binding[Doc]], expr: Doc):
        return Text("Forall (TODO);")

    def _finish_ite(self, node: terms.Ite, test: Doc, then: Doc, els: Doc):
        return test + utils.padded("?") + then + utils.padded(":") + els

    def _finish_some(self, none: terms.Some, vs: list[Binding[Doc]], fmla: Doc):
        raise NotImplementedError()

    def _finish_unop(self, node: terms.UnOp, expr: Doc):
        if isinstance(expr, Text):
            return Text(node.op) + expr
        return Text(node.op) + utils.enclosed("(", expr, ")")

    # Actions

    def _finish_assert(self, act: terms.Assert, pred: Doc):
        return Text("this.assert(") + pred + Text(");")

    def _finish_assign(self, act: terms.Assign, lhs: Doc, rhs: Doc):
        return lhs + utils.padded("=") + rhs + semi

    def _finish_assume(self, act: terms.Assume, pred: Doc):
        return Text("this.assume(") + pred + Text(");")

    def _finish_call(self, act: terms.Call, app: Doc):
        return app + semi  # XXX: yes??

    def _finish_debug(self, act: terms.Debug, args: list[Doc]):
        return Text("this.debug(") + Text(act.msg) + Text(");")  # TODO: args

    def _finish_ensures(self, act: terms.Ensures, pred: Doc):
        return Text("this.ensures(") + pred + Text(")")

    def _finish_havok(self, act: terms.Havok, modifies: list[Doc]):
        return Nil()  # TODO: ???

    def _finish_if(self, act: terms.If, test: Doc, then: Doc, els: Optional[Doc]) -> Doc:
        if_block = Text("if (") + test + Text(")")
        ret = if_block + space + block(then)
        if els is not None:
            ret = ret + utils.padded(Text("else")) + block(els)
        return ret

    def _finish_let(self, act: terms.Let, scope: Doc):
        var_docs = []
        for binding in act.vardecls:
            var = self._constant(binding.name)
            sort = UnboxedSort().visit_sort(binding.decl)

            var_docs.append(sort + space + var + semi)
        return utils.join(var_docs, Line()) + Line() + scope

    def _finish_logical_assign(self, act: terms.LogicalAssign, assn: Doc):
        ret = Nil()
        for v in act.vars:
            ret = ret + Text(v.sort.name() + ".forEach(") + Text(v.rep) + Text(" => { ")
        ret = ret + assn
        for _ in act.vars:
            ret = ret + Text(" })")
        return ret

    def _finish_native(self, act: terms.Native, args: list[Doc]) -> Doc:
        pat = r"`(\d+)`"
        ret = Nil()

        # TODO: bail out if we have not translated the Native out of C++.
        curr_begin = 0
        m = re.search(pat, act.fmt[curr_begin:])
        while m:
            idx = int(m.group(1))
            ret = ret + Text(act.fmt[curr_begin: curr_begin + m.start()]) + args[idx]
            curr_begin = curr_begin + m.end()
            m = re.search(pat, act.fmt[curr_begin:])
        ret = ret + Text(act.fmt[curr_begin:])
        return ret

    def _finish_sequence(self, act: terms.Sequence, stmts: list[Doc]) -> Doc:
        return utils.join(stmts, Line())

    def _finish_action_def(self,
                           name: str,
                           defn: terms.ActionDefinition,
                           body: Doc) -> Doc:
        sig = Extractor.action_sig(name, defn)
        return sig + block(body)
