from .quantifiers import iterate_through_varbounds
from .sorts import *
from .helpers import commented, quoted

from . import helpers as h
from porter.ast import Binding, terms
from porter.ast.sorts import Enum, Sort
from porter.ast.terms.visitor import Visitor as TermVisitor
from porter.quantifiers import bounds_for_exists, bounds_for_forall
from porter.pp.formatter import interpolate_native
from porter.pp.utils import *

from typing import Optional


class Extractor(TermVisitor[Doc]):
    def action_sig(self, name: str, decl: terms.ActionDefinition) -> Doc:
        ub = UnboxedSort()

        if len(decl.formal_returns) > 1:
            raise Exception("TODO: I don't know how to handle tuples in return types yet")
        if len(decl.formal_returns) == 0:
            ret = Text("Unit")
        else:
            ret = ub.visit_sort(decl.formal_returns[0].decl)

        param_docs = [h.typeannot(self._identifier(b.name), ub.visit_sort(b.decl)) for b in decl.formal_params]
        return h.func_sig(self._identifier(name), param_docs, ret)

    def action_body(self, defn: terms.ActionDefinition):
        body = self.visit_action(defn.body)

        ret: Optional[Binding[Sort]] = None
        if len(defn.formal_returns) == 1:
            ret = defn.formal_returns[0]
        elif len(defn.formal_returns) > 1:
            raise Exception("TODO: multiple returns???")

        retstmt = Nil()
        if ret is not None:
            retstmt = self._identifier(ret.name)

        return body + Line() + retstmt

    def imported_action(self, name: str, defn: terms.ActionDefinition):
        assert defn.kind == terms.ActionKind.IMPORTED

        # This should always be true...
        if name.startswith("imp__"):
            name = name[len("imp__"):]

        ret = Text("debug(") + quoted(name)
        for arg in defn.formal_params:
            ret = ret + Text(", ") + self._identifier(arg.name)
        ret = ret + Text(")")
        return ret

    # XXX: This is pretty similar to action_sig.
    def function_sig(self, name: str, decl: terms.FunctionDefinition) -> Doc:
        unboxed = UnboxedSort()
        param_docs = [h.typeannot(self._identifier(b.name), unboxed.visit_sort(b.decl)) for b in decl.formal_params]

        ret_sort = decl.body.sort()
        assert ret_sort
        ret = unboxed.visit_sort(ret_sort)

        return h.func_sig(self._identifier(name), param_docs, ret)

    def export_action(self, action: Binding[terms.ActionDefinition]) -> Doc:
        arb_args = [ArbitraryGenerator("a").visit_sort(b.decl) for b in action.decl.formal_params]
        ret = Text("Unit") if len(action.decl.formal_returns) == 0 else BoxedSort().visit_sort(action.decl.formal_returns[0].decl)

        gen_args = [BoxedSort().visit_sort(b.decl) for b in action.decl.formal_params] + [ret]
        tvars = h.typelist(gen_args)
        args = h.arglist([
            quoted(action.name),
            self._identifier(action.name),
            *arb_args
        ])
        return Text("exported") + tvars + args

    def add_conjecture(self, conj: Binding[terms.Expr]) -> Doc:
        fmla = self.visit_expr(conj.decl)
        lineno = conj.decl.pos()
        assert lineno
        return Text("conjectured(") + \
            quoted(conj.name) + Text(", ") + \
            quoted(lineno.filename.name) + Text(", ") + \
            Text(str(lineno.line)) + Text(",") + utils.soft_line + \
            Text("() => ") + block(fmla) + \
            Text(")")

    def initializers(self,
                     exports: list[Binding[terms.ActionDefinition]],
                     conjs: list[Binding[terms.Expr]],
                     inits: Doc):
        exportdocs: list[Doc] = [self.export_action(e) for e in exports]
        conjdocs: list[Doc] = [self.add_conjecture(conj) for conj in conjs]

        body = Nil()
        if len(exportdocs) > 0:
            body += commented("Exports") + utils.join(exportdocs, "\n") + Line()
        if len(conjdocs) > 0:
            body += commented("Conjectures") + utils.join(conjdocs, "\n") + Line()
        if len(inits) > 0:
            body += commented("Inits") + utils.join(inits, "\n") + Line()
        return body

    def vardecl(self, binding: Binding[Sort]):
        var = self._identifier(binding.name)
        sort = UnboxedSort().visit_sort(binding.decl)
        init = DefaultValue().visit_sort(binding.decl)

        return h.local_decl(var, sort, init, True)

    # Expressions

    def _identifier(self, s: str) -> Doc:
        return Text(canonicalize_identifier(s))

    def _constant(self, c: terms.Constant) -> Doc:
        ident = self._identifier(c.rep)
        sort = c.sort()
        match sort:
            case Enum(sort_name, _discriminants):
                return Text(sort_name) + Text(".") + ident
            case _:
                return ident

    def _var(self, c: terms.Var) -> Doc:
        ident = self._identifier(c.rep)
        sort = c.sort()
        match sort:
            case Enum(sort_name, _discriminants):
                return Text(sort_name) + Text(".") + ident
            case _:
                return ident

    def _finish_apply(self, node: terms.Apply, relsym_ret: Doc, args_ret: list[Doc]):
        if len(node.args) == 0:
            return relsym_ret
        return relsym_ret + utils.enclosed("(", utils.join(args_ret), ")")

    def _finish_binop(self, node: terms.BinOp, lhs_ret: Doc, rhs_ret: Doc):
        match node.op:
            case "and":
                return h.binop(lhs_ret, "&&", rhs_ret)
            case "or":
                return h.binop(lhs_ret, "||", rhs_ret)
                op = "||"
            case "+" | "-" | "*" | "/":
                sort = node.sort()
                if isinstance(sort, sorts.Number):
                    doc = lhs_ret + utils.padded(node.op) + rhs_ret
                    saturated = doc
                    if sort.lo_range is not None:
                        # doc < lo ? lo : doc
                        lo = Text(str(sort.lo_range))
                        saturated = Text("if") + utils.padded(utils.enclosed("(", doc + utils.padded("<") + lo, ")")) + \
                                    lo + utils.padded("else") + saturated
                    if sort.hi_range is not None:
                        # doc > hi ? hi : doc
                        hi = Text(str(sort.hi_range))
                        saturated = Text("if") + utils.padded(utils.enclosed("(", doc + utils.padded(">") + hi, ")")) + \
                                    hi + utils.padded("else") + saturated
                    return saturated
                else:
                    return h.binop(lhs_ret, node.op, rhs_ret)
            case op:
                return h.binop(lhs_ret, op, rhs_ret)

    def _finish_exists(self, node: terms.Exists, expr: Doc):
        bound_vars = bounds_for_exists(node)
        return iterate_through_varbounds(bound_vars, expr, "exists")

    def _finish_forall(self, node: terms.Forall, expr: Doc):
        bound_vars = bounds_for_forall(node)
        return iterate_through_varbounds(bound_vars, expr, "forall")

    def _finish_ite(self, node: terms.Ite, test: Doc, then: Doc, els: Doc):
        if_block = Text("if") + utils.padded(utils.enclosed("(", test, ")"))
        ret = if_block + block(then)
        ret = ret + utils.padded(Text("else")) + block(els)
        return ret

    def _finish_native_expr(self, node: terms.NativeExpr, args: list[Doc]) -> Doc:
        return interpolate_native(node.fmt, args)

    def _finish_some(self, node: terms.Some, fmla: Doc):
        return Text("TODO???")

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
        lineno = act.pos()
        assert lineno
        return Text("assertThat(") + \
            quoted(lineno.filename.name) + Text(", ") + \
            Text(str(lineno.line)) + Text(", ") + \
            pred + Text(")")

    def _finish_assign(self, act: terms.Assign, lhs: Doc, rhs: Doc):
        return h.assign(lhs, rhs)

    def _finish_assume(self, act: terms.Assume, pred: Doc):
        return Text("this.assume(") + pred + Text(")")

    def _finish_call(self, act: terms.Call, app: Doc):
        return app  # XXX: yes??

    def _finish_debug(self, act: terms.Debug, args: list[Doc]):
        return Text("debug(") + Text(act.msg) + Text(")")

    def _finish_ensures(self, act: terms.Ensures, pred: Doc):
        return Text("this.ensures(") + pred + Text(")")

    def _finish_field_access(self, node: terms.FieldAccess, struct: Doc, field_name: Doc) -> Optional[Doc]:
        return struct + Text(".") + field_name

    def _finish_havok(self, act: terms.Havok, modifies: list[Doc]):
        return Nil()  # TODO: ???

    def _finish_if(self, act: terms.If, test: Doc, then: Doc, els: Optional[Doc]) -> Doc:
        if_block = Text("if") + utils.padded(utils.enclosed("(", test, ")"))
        ret = if_block + block(then)
        if els is not None:
            ret = ret + utils.padded(Text("else")) + block(els)
        return ret

    def _finish_init(self, act: terms.Init, doc: Doc):
        ret = Nil()
        if len(act.params) == 0:
            return doc
        for param in act.params:
            # The assert will ensure that inhabitants() will return Some(Iterator).
            assert isinstance(param.decl, sorts.Number)

            varname = self._identifier(param.name)
            sortname = self._identifier(param.decl.sort_name)
            ret = ret + sortname
            ret = ret + Text(f".inhabitants.get.foreach(") + varname + Text(" => {") + Line()
        ret = ret + Nest(4, doc)
        for _ in act.params:
            ret = ret + Line() + Text("})")
        return ret

    def _finish_let(self, act: terms.Let, scope: Doc):
        var_docs = [self.vardecl(b) for b in act.vardecls]
        return sum(var_docs, start=Nil()) + Line() + scope

    def _finish_logical_assign(self, act: terms.LogicalAssign, relsym: Doc, args: list[Doc], assn: Doc):
        # Special case for when the logical assignment is to _every_ logical
        # variable in the domain; semantically we want to zap out the Map and
        # replace the range supplier.
        if all([isinstance(a, terms.Var) for a in act.vars]):
            return relsym + Text(".initWithDefault(() => ") + assn + Text(")")

        ret = relsym + Text(".iterator collect { case (")
        ret = ret + utils.join(args)
        ret = ret + Text(") => ")
        ret = ret + relsym + utils.enclosed("(", utils.join(args), ")") + Text(" = ") + assn
        ret = ret + Text(" }")
        return ret

    def _finish_native_action(self, act: terms.NativeAct, args: list[Doc]) -> Doc:
        # TODO: bail out if we have not translated the Native out of C++.
        return interpolate_native(act.fmt, args)

    def _finish_sequence(self, act: terms.Sequence, stmts: list[Doc]) -> Doc:
        return sum(stmts, start=Nil())

    def _finish_while(self, act: terms.While, test: Doc, decreases: Optional[Doc], do: Doc):
        while_block = Text("while (") + test + Text(")")
        ret = while_block + space + block(do)
        return ret

    def _finish_action_def(self,
                           name: str,
                           defn: terms.ActionDefinition,
                           body: Doc) -> Doc:
        sig = self.action_sig(name, defn)
        match defn.kind:
            case terms.ActionKind.IMPORTED:
                return h.assign(sig, block(self.imported_action(name, defn)))
            case _:
                return h.assign(sig, block(self.action_body(defn)))

    def _finish_function_def(self,
                             name: str,
                             defn: terms.FunctionDefinition,
                             body: Doc) -> Doc:
        sig = self.function_sig(name, defn)

        if isinstance(defn.body, terms.FieldAccess):
            pass
            # body = defn.body
        return h.assign(sig, block(body))
