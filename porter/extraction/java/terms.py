import re

from .sorts import *
from .utils import *

from porter.ast import Binding, terms

from porter.ast.terms.visitor import Visitor as TermVisitor

from porter.pp import Doc, Text, Line, Nil, utils
from porter.pp.utils import space

from typing import Optional


class Extractor(TermVisitor[Doc]):

    def action_sig(self, name: str, decl: terms.ActionDefinition) -> Doc:
        unboxed = UnboxedSort()

        if len(decl.formal_returns) > 1:
            raise Exception("TODO: I don't know how to handle tuples in return types yet")

        if len(decl.formal_returns) == 0:
            ret = Text("void")
        else:
            ret = unboxed.visit_sort(decl.formal_returns[0].decl)

        param_docs = [unboxed.visit_sort(b.decl) + space + self._constant(b.name) for b in decl.formal_params]
        params = utils.enclosed("(", utils.join(param_docs, ", "), ")")

        return Text("public") + space + ret + space + self._constant(name) + params

    def export_action(self, action: Binding[terms.ActionDefinition]) -> Doc:
        arity = len(action.decl.formal_params) + len(action.decl.formal_returns)
        args = [self._constant(action.name)]
        return Text(f"exportAction{arity}") + Text("(") + utils.join(args, ",") + Text(");")

    def add_conjecture(self, conj: Binding[terms.Expr]) -> Doc:
        name = '"' + conj.name + '"'
        fmla = self.visit_expr(conj.decl)
        return Text(f"addConjecture({name}, () => ") + fmla + Text(");")

    def cstr(self,
             isolate_name: str,
             exports: list[Binding[terms.ActionDefinition]],
             conjs: list[Binding[terms.Expr]],
             inits: list[Doc]):
        exports = [self.export_action(e) for e in exports]
        conjs = [self.add_conjecture(conj) for conj in conjs]

        body = exports + [utils.soft_line] + \
               conjs + [utils.soft_line] + \
               inits
        return Text(f"public {isolate_name}()") + space + block(utils.join(body, "\n"))

    # Expressions

    def _constant(self, rep: str) -> Doc:
        return Text(canonicalize_identifier(rep))

    def _var(self, rep: str) -> Doc:
        return Text(canonicalize_identifier(rep))

    def _finish_apply(self, node: terms.Apply, relsym_ret: Doc, args_ret: list[Doc]):
        return relsym_ret + utils.enclosed("(", utils.join(args_ret, ", "), ")")

    def _finish_binop(self, node: terms.BinOp, lhs_ret: Doc, rhs_ret: Doc):
        # XXX: If this is infix + we need to ensure we bound the value according to
        # the sort's range, if it has one!
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
        match node.op:
            case "~":
                op = "!"
            case "-":
                op = "-"
            case _:
                raise Exception(f"Unknown op: {node.op}")

        if isinstance(expr, Text):
            return Text(op) + expr
        return Text(op) + utils.enclosed("(", expr, ")")

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

        for line in act.fmt.split("\n"):
            # line = line.strip()

            # TODO: bail out if we have not translated the Native out of C++.
            curr_begin = 0
            m = re.search(pat, line[curr_begin:])
            while m:
                idx = int(m.group(1))
                text = line[curr_begin: curr_begin + m.start()].strip()
                ret = ret + Text(text) + args[idx]

                curr_begin = curr_begin + m.end()
                m = re.search(pat, line[curr_begin:])

            ret = ret + Text(line[curr_begin:]) + Line()
        return ret

    def _finish_sequence(self, act: terms.Sequence, stmts: list[Doc]) -> Doc:
        return utils.join(stmts, Line())

    def _finish_action_def(self,
                           name: str,
                           defn: terms.ActionDefinition,
                           body: Doc) -> Doc:
        sig = self.action_sig(name, defn)
        return sig + space + block(body)
