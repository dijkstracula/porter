from .quantifiers import iterate_through_varbounds
from .sorts import *
from .utils import *

from porter.ast import Binding, terms
from porter.ast.sorts import Enum, Sort, Record
from porter.ast.terms.visitor import Visitor as TermVisitor
from porter.quantifiers import bounds_for_exists, bounds_for_forall
from porter.pp import Doc, Text, Line, Nil, utils
from porter.pp.formatter import interpolate_native
from porter.pp.utils import space

from typing import Optional


class Extractor(TermVisitor[Doc]):
    def action_sig(self, name: str, decl: terms.ActionDefinition) -> Doc:
        unboxed = UnboxedSort()

        if len(decl.formal_returns) > 1:
            raise Exception("TODO: I don't know how to handle tuples in return types yet")

        # TODO: unfortunately void functions need to produce Void, since Java doesn't distinguish between void
        # and j.l.Void.  Perhaps we should have a transformation pass that implicitly adds a formal return
        # so we don't have to special-case it at extraction time?
        if len(decl.formal_returns) == 0:
            ret = Text("Void")
        else:
            ret = unboxed.visit_sort(decl.formal_returns[0].decl)

        param_docs = [unboxed.visit_sort(b.decl) + space + self._identifier(b.name) for b in decl.formal_params]
        params = utils.enclosed("(", utils.join(param_docs, ", "), ")")

        return Text("public") + space + ret + space + self._identifier(name) + params

    def action_body(self, defn: terms.ActionDefinition):
        body = self.visit_action(defn.body)
        rets = defn.formal_returns
        if len(rets) == 0:
            # return body  # This is a void function.
            ret = Binding("__void_ret", sorts.Top())
        elif len(rets) == 1:
            ret = rets[0]
        else:
            raise Exception("TODO: multiple returns")

        if ret.name not in [b.name for b in defn.formal_params]:
            retdecl = self.vardecl(ret) + semi + Line()
        else:
            retdecl = Nil()
        retstmt = Text("return ") + self._identifier(ret.name) + semi

        return retdecl + body + Line() + retstmt

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

        param_docs = [unboxed.visit_sort(b.decl) + space + self._identifier(b.name) for b in decl.formal_params]
        params = utils.enclosed("(", utils.join(param_docs, ", "), ")")

        ret_sort = decl.body.sort()
        assert ret_sort
        ret = unboxed.visit_sort(ret_sort)

        # This could be public but it's nice to just see visually what's an Action vs a Function.
        return Text("protected") + space + ret + space + self._identifier(name) + params

    def export_action(self, action: Binding[terms.ActionDefinition]) -> Doc:
        args = [ArbitraryGenerator("a").visit_sort(b.decl) for b in action.decl.formal_params]
        return Text("exported(") + \
            quoted(action.name) + utils.soft_comma + \
            Text("this::") + self._identifier(action.name) + utils.soft_comma + \
            utils.join(args, utils.soft_comma) + \
            Text(");")

    def add_conjecture(self, conj: Binding[terms.Expr]) -> Doc:
        fmla = self.visit_expr(conj.decl)
        lineno = conj.decl.pos()
        assert lineno
        return Text("conjectured(") + \
            quoted(conj.name) + Text(", ") + \
            quoted(lineno.filename.name) + Text(", ") + \
            Text(str(lineno.line)) + Text(",") + utils.soft_line + \
            Text("() => ") + fmla + \
            Text(");")

    def cstr(self,
             isolate_name: str,
             exports: list[Binding[terms.ActionDefinition]],
             conjs: list[Binding[terms.Expr]],
             inits: list[Doc]):
        exportdocs: list[Doc] = [self.export_action(e) for e in exports]
        conjdocs: list[Doc] = [self.add_conjecture(conj) for conj in conjs]

        body = [Text("super();") + Line()] + \
               exportdocs + [utils.soft_line] + \
               conjdocs + [utils.soft_line] + \
               inits
        return Text(f"public {isolate_name}(Arbitrary a)") + space + block(utils.join(body, "\n"))

    def vardecl(self, binding: Binding[Sort]):
        sort = UnboxedSort().visit_sort(binding.decl)
        var = self._identifier(binding.name)
        init = DefaultValue().visit_sort(binding.decl)

        return sort + space + var + Text(" = ") + init

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
        if isinstance(node.sort(), sorts.Function):
            # https://github.com/dijkstracula/porter/issues/
            return relsym_ret + utils.enclosed(".get(", utils.join(args_ret, ", "), ")")
        return relsym_ret + utils.enclosed("(", utils.join(args_ret, ", "), ")")

    def _finish_binop(self, node: terms.BinOp, lhs_ret: Doc, rhs_ret: Doc):
        # XXX: If this is infix + we need to ensure we bound the value according to
        # the sort's range, if it has one!
        match node.op:
            case "and":
                op = "&&"
            case "or":
                op = "||"
            case _:
                op = node.op
        return lhs_ret + utils.padded(op) + rhs_ret

    def _finish_exists(self, node: terms.Exists, expr: Doc):
        bound_vars = bounds_for_exists(node)
        return iterate_through_varbounds(bound_vars, expr) + Text(".anyMatch(b -> b)")

    def _finish_forall(self, node: terms.Forall, expr: Doc):
        bound_vars = bounds_for_forall(node)
        return iterate_through_varbounds(bound_vars, expr) + Text(".allMatch(b -> b)")

    def _finish_ite(self, node: terms.Ite, test: Doc, then: Doc, els: Doc):
        return test + utils.padded("?") + then + utils.padded(":") + els

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
            pred + Text(");")

    def _finish_assign(self, act: terms.Assign, lhs: Doc, rhs: Doc):
        return lhs + utils.padded("=") + rhs + semi

    def _finish_assume(self, act: terms.Assume, pred: Doc):
        return Text("this.assume(") + pred + Text(");")

    def _finish_call(self, act: terms.Call, app: Doc):
        return app + semi  # XXX: yes??

    def _finish_debug(self, act: terms.Debug, args: list[Doc]):
        return Text("debug(") + Text(act.msg) + Text(");")

    def _finish_ensures(self, act: terms.Ensures, pred: Doc):
        return Text("this.ensures(") + pred + Text(")")

    def _finish_field_access(self, node: terms.FieldAccess, struct: Doc, field_name: Doc) -> Optional[Doc]:
        return struct + Text(".") + field_name

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
            var_docs.append(self.vardecl(binding) + semi)
        return utils.join(var_docs, Line()) + Line() + scope

    def _finish_logical_assign(self, act: terms.LogicalAssign, assn: Doc):
        ret = Nil()
        boxed = BoxedSort()
        for v in act.vars:
            vs = v.sort()
            assert (vs)
            ret = ret + boxed.visit_sort(vs) + Text(".forEach(") + self._var(v) + Text(" => { ")
        ret = ret + assn
        for _ in act.vars:
            ret = ret + Text(" })")
        return ret

    def _finish_native_action(self, act: terms.NativeAct, args: list[Doc]) -> Doc:
        # TODO: bail out if we have not translated the Native out of C++.
        return interpolate_native(act.fmt, args)

    def _finish_sequence(self, act: terms.Sequence, stmts: list[Doc]) -> Doc:
        return utils.join(stmts, Line())

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
                return sig + space + block(self.imported_action(name, defn))
            case _:
                return sig + space + block(self.action_body(defn))

    def _finish_function_def(self,
                             name: str,
                             defn: terms.FunctionDefinition,
                             body: Doc) -> Doc:
        sig = self.function_sig(name, defn)

        if isinstance(defn.body, terms.FieldAccess):
            pass
            #body = defn.body
        body = Text("return ") + body + Text(";")
        return sig + space + block(body)
