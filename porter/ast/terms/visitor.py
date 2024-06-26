from typing import Generic

from porter.ast import AST
from porter.ast.sorts import Bool, Number
from porter.ast.sorts.visitor import Visitor as SortVisitor
from porter.ast.terms import *

T = TypeVar("T")


class UnimplementedASTNodeHandler(Exception):
    def __init__(self, cls: type):
        self.cls = cls

    def __str__(self):
        return f"Unimplemented AST visitor for {self.cls.__module__}.{self.cls.__name__}"


# noinspection PyMethodMayBeStatic,PyShadowingBuiltins
class Visitor(Generic[T]):
    # Technically the Ivy program should give us these trivial sorts too, but manually inserting them here
    # simplifies writing tests that only operate on subprograms.
    sorts: dict[str, Sort] = {"int": Number.int_sort(), "nat": Number.nat_sort(), "bool": Bool()}

    # These are all the fields in a Program.  Feels weird to accumulate them
    # up mutably like this, but ooooh well.
    individuals: list[Binding[Sort]]
    inits: list[T]
    actions: list[Binding[T]]
    functions: list[Binding[T]]

    scopes: list[list[str]] = []

    def _in_scope(self, v: str):
        for scope in self.scopes:
            if v in scope: return True
        return False

    @staticmethod
    def visit_program_sorts(prog: Program, visitor: SortVisitor[Sort]):
        # TODO: this is a dumb place for this to live.
        prog.sorts = {name: visitor.visit_sort(s) for name, s in prog.sorts.items()}
        prog.individuals = [Binding(b.name, visitor.visit_sort(b.decl)) for b in prog.individuals]

        for binding in prog.functions:
            f = binding.decl
            f.formal_params = [Binding(b.name, visitor.visit_sort(b.decl)) for b in f.formal_params]
            f.body._sort = visitor.visit_sort(f.body.sort())

        for binding in prog.actions:
            f = binding.decl
            f.formal_params = [Binding(b.name, visitor.visit_sort(b.decl)) for b in f.formal_params]
            if f.body.sort():
                f.body._sort = visitor.visit_sort(f.body.sort())

    def visit_program(self, prog: Program):
        self._begin_program(prog)

        self.sorts = prog.sorts
        self.individuals = prog.individuals
        self.inits = [self.visit_action(a) for a in prog.inits]

        self.actions = []
        for binding in prog.actions:
            name = binding.name
            action = binding.decl

            bret = self._begin_action_def(name, action)
            if bret is not None:
                self.actions.append(bret)
                continue

            body = self.visit_action(action.body)
            self.scopes.append([name])
            self.actions.append(Binding(name, self._finish_action_def(name, action, body)))
            self.scopes.pop()

        self.functions = []
        for binding in prog.functions:
            name = binding.name
            func = binding.decl

            self._begin_function_def(name, func)
            body = self.visit_expr(func.body)

            self.scopes.append([name])
            self.functions.append(Binding(name, self._finish_function_def(name, func, body)))
            self.scopes.pop()

    def _begin_program(self, prog: Program) -> Optional[T]:
        pass

    # Lambda-oids

    def _begin_action_def(self, name: str, defn: ActionDefinition) -> Optional[T]:
        pass

    def _finish_action_def(self,
                           name: str,
                           defn: ActionDefinition,
                           body: T) -> T:
        raise UnimplementedASTNodeHandler(ActionDefinition)

    def _begin_function_def(self, name: str, defn: FunctionDefinition) -> Optional[T]:
        pass

    def _finish_function_def(self,
                             name: str,
                             defn: FunctionDefinition,
                             body: T) -> T:
        raise UnimplementedASTNodeHandler(FunctionDefinition)

    # Expressions

    def visit_expr(self, node: Expr) -> T:
        match node:
            case Apply(_, relsym, args):
                bret = self._begin_apply(node)
                if bret is not None: return bret

                relsym = self._identifier(relsym)
                args = [self.visit_expr(arg) for arg in args]
                return self._finish_apply(node, relsym, args)
            case BinOp(_, lhs, _op, rhs):
                bret = self._begin_binop(node)
                if bret is not None: return bret

                lhs_ret = self.visit_expr(lhs)
                rhs_ret = self.visit_expr(rhs)
                return self._finish_binop(node, lhs_ret, rhs_ret)
            case Constant(_, _):
                return self._constant(node)
            case Var(_, _):
                return self._var(node)
            case Exists(_, vardecls, expr):
                bret = self._begin_exists(node)
                if bret is not None: return bret

                self.scopes.append([b.name for b in vardecls])
                expr = self.visit_expr(expr)
                ret = self._finish_exists(node, expr)
                self.scopes.pop()
                return ret
            case FieldAccess(_, struct, field_name):
                bret = self._begin_field_access(node)
                if bret is not None:
                    return bret
                struct_t = self.visit_expr(struct)
                field_name_t = self._identifier(field_name)
                return self._finish_field_access(node, struct_t, field_name_t)
            case Forall(_, vardecls, expr):
                bret = self._begin_forall(node)
                if bret is not None: return bret

                self.scopes.append([b.name for b in vardecls])
                expr = self.visit_expr(expr)
                ret = self._finish_forall(node, expr)
                self.scopes.pop()
                return ret
            case Ite(_, test, then, els):
                bret = self._begin_ite(node)
                if bret is not None: return bret

                test = self.visit_expr(test)
                then = self.visit_expr(then)
                els = self.visit_expr(els)
                return self._finish_ite(node, test, then, els)
            case NativeExpr(_, _lang, _fmt, args):
                bret = self._begin_native_expr(node)
                if bret is not None: return bret

                args = [self.visit_expr(arg) for arg in args]
                return self._finish_native_expr(node, args)
            case Some(_, vardecls, fmla, _strat):
                bret = self._begin_some(node)
                if bret is not None: return bret

                self.scopes.append([b.name for b in vardecls])
                fmla = self.visit_expr(fmla)
                ret = self._finish_some(node, fmla)
                self.scopes.pop()
                return ret
            case UnOp(_, _op, expr):
                bret = self._begin_unop(node)
                if bret is not None: return bret

                expr = self.visit_expr(expr)
                return self._finish_unop(node, expr)
        raise Exception(f"TODO: {node}")

    def _identifier(self, s: str) -> T:
        raise UnimplementedASTNodeHandler(str)

    def _constant(self, c: Constant) -> T:
        return self._identifier(c.rep)

    def _var(self, v: Var) -> T:
        return self._identifier(v.rep)

    def _begin_apply(self, node: Apply) -> Optional[T]:
        pass

    def _finish_apply(self, node: Apply, relsym_ret: T, args_ret: list[T]) -> T:
        raise UnimplementedASTNodeHandler(Apply)

    def _begin_binop(self, node: BinOp) -> Optional[T]:
        pass

    def _finish_binop(self, node: BinOp, lhs_ret: T, rhs_ret: T) -> T:
        raise UnimplementedASTNodeHandler(BinOp)

    def _begin_exists(self, node: Exists) -> Optional[T]:
        pass

    def _finish_exists(self, node: Exists, expr: T):
        raise UnimplementedASTNodeHandler(Exists)

    def _begin_field_access(self, node: FieldAccess) -> Optional[T]:
        pass

    def _finish_field_access(self, node: FieldAccess, struct: T, field_name: T) -> T:
        raise UnimplementedASTNodeHandler(FieldAccess)

    def _begin_forall(self, node: Forall) -> Optional[T]:
        pass

    def _finish_forall(self, node: Forall, expr: T) -> T:
        raise UnimplementedASTNodeHandler(Forall)

    def _begin_ite(self, node: Ite) -> Optional[T]:
        pass

    def _finish_ite(self, node: Ite, test: T, then: T, els: T) -> T:
        raise UnimplementedASTNodeHandler(Ite)

    def _begin_native_expr(self, node: NativeExpr) -> Optional[T]:
        pass

    def _finish_native_expr(self, node: NativeExpr, args: list[T]) -> T:
        raise UnimplementedASTNodeHandler(NativeExpr)

    def _begin_some(self, node: Some) -> Optional[T]:
        pass

    def _finish_some(self, node: Some, fmla: T):
        raise UnimplementedASTNodeHandler(Some)

    def _begin_unop(self, node: UnOp) -> Optional[T]:
        pass

    def _finish_unop(self, node: UnOp, expr: T) -> T:
        raise UnimplementedASTNodeHandler(UnOp)

    # Actions

    def visit_action(self, node: Action) -> T:
        match node:
            case Assert(_, pred):
                bret = self._begin_assert(node)
                if bret is not None: return bret

                pred = self.visit_expr(pred)
                return self._finish_assert(node, pred)
            case Assign(_, lhs, rhs):
                bret = self._begin_assign(node)
                if bret is not None: return bret

                lhs = self.visit_expr(lhs)
                rhs = self.visit_expr(rhs)
                return self._finish_assign(node, lhs, rhs)
            case Assume(_, pred):
                bret = self._begin_assume(node)
                if bret is not None: return bret

                pred = self.visit_expr(pred)
                return self._finish_assume(node, pred)
            case Call(_, app):
                bret = self._begin_call(node)
                if bret is not None: return bret

                app = self.visit_expr(app)
                return self._finish_call(node, app)
            case Debug(_, _msg, args):
                bret = self._begin_debug(node)
                if bret is not None: return bret

                args = [Binding(b.name, self.visit_expr(b.decl)) for b in args]
                return self._finish_debug(node, args)
            case Ensures(_, pred):
                bret = self._begin_ensures(node)
                if bret is not None: return bret

                pred = self.visit_expr(pred)
                return self._finish_ensures(node, pred)
            case Havok(_, modifies):
                bret = self._begin_havok(node)
                if bret is not None: return bret

                modifies = [self.visit_expr(e) for e in modifies]
                return self._finish_havok(node, modifies)
            case If(_, test, then, els):
                bret = self._begin_if(node)
                if bret is not None: return bret

                test = self.visit_expr(test)
                then = self.visit_action(then)
                if els is not None:
                    els = self.visit_action(els)
                return self._finish_if(node, test, then, els)
            case Init(_, params, act):
                bret = self._begin_init(node)
                if bret is not None: return bret

                self.scopes.append([b.name for b in params])
                act = self.visit_action(act) 
                ret = self._finish_init(node, act)
                self.scopes.pop()
                return ret
            case Let(_, vardecls, scope):
                bret = self._begin_let(node)
                if bret is not None: return bret

                self.scopes.append([b.name for b in vardecls])

                scope = self.visit_action(scope)
                ret = self._finish_let(node, scope)
                self.scopes.pop()
                return ret
            case LogicalAssign(_, relsym, args, assignee):
                bret = self._begin_logical_assign(node)
                if bret is not None: return bret

                relsym = self._identifier(relsym)
                args = [self.visit_expr(a) for a in args]
                assignee = self.visit_expr(assignee)
                return self._finish_logical_assign(node, relsym, args, assignee)
            case NativeAct(_, _lang, _fmt, args):
                bret = self._begin_native_action(node)
                if bret is not None: return bret

                args = [self.visit_expr(arg) for arg in args]
                return self._finish_native_action(node, args)
            case Requires(_, pred):
                bret = self._begin_requires(node)
                if bret is not None: return bret

                pred = self.visit_expr(pred)
                return self._finish_requires(node, pred)
            case Sequence(_, stmts):
                bret = self._begin_sequence(node)
                if bret is not None: return bret

                stmts = [self.visit_action(stmt) for stmt in stmts]
                return self._finish_sequence(node, stmts)
            case While(_, test, decreases, do):
                bret = self._begin_while(node)
                if bret is not None: return bret

                test = self.visit_expr(test)
                if decreases is not None:
                    decreases = self.visit_expr(decreases)
                do = self.visit_action(do)
                return self._finish_while(node, test, decreases, do)
        raise Exception(f"TODO: {node}")

    def _begin_assert(self, act: Assert) -> Optional[T]:
        pass

    def _finish_assert(self, act: Assert, pred: T) -> T:
        raise UnimplementedASTNodeHandler(Assert)

    def _begin_assign(self, act: Assign) -> Optional[T]:
        pass

    def _finish_assign(self, act: Assign, lhs: T, rhs: T) -> T:
        raise UnimplementedASTNodeHandler(Assign)

    def _begin_assume(self, act: Assume) -> Optional[T]:
        pass

    def _finish_assume(self, act: Assume, pred: T) -> T:
        raise UnimplementedASTNodeHandler(Assume)

    def _begin_call(self, act: Call) -> Optional[T]:
        pass

    def _finish_call(self, act: Call, app: T) -> T:
        raise UnimplementedASTNodeHandler(Call)

    def _begin_debug(self, act: Debug) -> Optional[T]:
        pass

    def _finish_debug(self, act: Debug, args: list[Binding[T]]) -> T:
        raise UnimplementedASTNodeHandler(Debug)

    def _begin_ensures(self, act: Ensures) -> Optional[T]:
        pass

    def _finish_ensures(self, act: Ensures, pred: T) -> T:
        raise UnimplementedASTNodeHandler(Ensures)

    def _begin_havok(self, act: Havok) -> Optional[T]:
        return None

    def _finish_havok(self, act: Havok, modifies: list[T]):
        raise UnimplementedASTNodeHandler(Havok)

    def _begin_if(self, act: If) -> Optional[T]:
        return None

    def _finish_if(self, act: If, test: T, then: T, els: Optional[T]):
        raise UnimplementedASTNodeHandler(If)

    def _begin_init(self, act: Init) -> Optional[T]:
        pass

    def _finish_init(self, act: Init, act_t: T) -> T:
        raise UnimplementedASTNodeHandler(Init)

    def _begin_let(self, act: Let) -> Optional[T]:
        return None

    def _finish_let(self, act: Let, scope: T) -> T:
        raise UnimplementedASTNodeHandler(Let)

    def _begin_logical_assign(self, act: LogicalAssign) -> Optional[T]:
        return None

    def _finish_logical_assign(self, act: LogicalAssign, relsym: T, args: list[T], assn: T) -> T:
        raise UnimplementedASTNodeHandler(LogicalAssign)

    def _begin_native_action(self, act: NativeAct) -> Optional[T]:
        return None

    def _finish_native_action(self, act: NativeAct, args: list[T]) -> T:
        raise UnimplementedASTNodeHandler(NativeAct)

    def _begin_requires(self, act: Requires) -> Optional[T]:
        return None

    def _finish_requires(self, act: Requires, pred: T) -> T:
        raise UnimplementedASTNodeHandler(Requires)

    def _begin_sequence(self, act: Sequence) -> Optional[T]:
        return None

    def _finish_sequence(self, act: Sequence, stmts: list[T]) -> T:
        raise UnimplementedASTNodeHandler(Sequence)

    def _begin_while(self, act: While) -> Optional[T]:
        return None

    def _finish_while(self, act: While, test: T, decreases: Optional[T], do: T) -> T:
        raise UnimplementedASTNodeHandler(While)


class ImmutVisitor(Visitor[AST]):
    """ A base class for immutable visitors, that consume and produce a new tree.
    Since we require stronger typing guarantees than each T being an AST, we fall back
    to some dynamic typechecks here.
    """

    def _finish_action_def(self, name: str, defn: ActionDefinition, body):
        assert isinstance(body, Action)
        return ActionDefinition(defn.ivy_node, defn.kind, defn.formal_params, defn.formal_returns, body)

    def _finish_function_def(self, name: str, defn: FunctionDefinition, body):
        assert isinstance(body, Expr)
        return FunctionDefinition(defn.ivy_node, defn.formal_params, body)

    # Expressions

    def _identifier(self, s: str) -> str:
        return s

    def _constant(self, c: Constant):
        return c

    def _var(self, v: Var):
        return v

    def _finish_apply(self, node: Apply, relsym_ret: str, args_ret: list[Expr]):
        assert isinstance(args_ret, list)
        assert all([isinstance(elem, Expr) for elem in args_ret])
        ret = Apply(node.ivy_node, relsym_ret, args_ret)
        ret._sort = node.sort()
        return ret

    def _finish_binop(self, node: BinOp, lhs: Expr, rhs: Expr) -> BinOp:
        assert isinstance(lhs, Expr)
        assert isinstance(rhs, Expr)
        ret = BinOp(node.ivy_node, lhs, node.op, rhs)
        ret._sort = node.sort()
        return ret

    def _finish_exists(self, node: Exists, expr: Expr) -> Exists:
        assert isinstance(expr, Expr)
        ret = Exists(node.ivy_node, [v for v in node.vars], expr)
        ret._sort = node.sort()
        return ret

    def _finish_field_access(self, node: FieldAccess, struct: Expr, field_name: str):
        assert isinstance(struct, Expr)
        ret = FieldAccess(node.ivy_node, struct, field_name)
        ret._sort = node.sort()
        return ret

    def _finish_forall(self, node: Forall, expr: Expr) -> Forall:
        assert isinstance(expr, Expr)
        ret = Forall(node.ivy_node, [v for v in node.vars], expr)
        ret._sort = node.sort()
        return ret

    def _finish_init(self, node: Init, act_t: Action) -> Init:
        assert isinstance(act_t, Action)
        ret = Init(node.ivy_node, [p for p in node.params], act_t)
        ret._sort = node.sort()
        return ret


    def _finish_ite(self, node: Ite, test: Expr, then: Expr, els: Expr) -> Ite:
        assert isinstance(test, Expr)
        assert isinstance(then, Expr)
        assert isinstance(els, Expr)
        ret = Ite(node.ivy_node, test, then, els)
        ret._sort = node.sort()
        return ret

    def _finish_native_expr(self, node: NativeExpr, args: list[Expr]) -> NativeExpr:
        assert isinstance(args, list)
        assert all([isinstance(elem, Expr) for elem in args])
        ret = NativeExpr(node.ivy_node, node.lang, node.fmt, args)
        ret._sort = node.sort()
        return ret

    def _finish_some(self, node: Some, fmla: Expr) -> Some:
        assert isinstance(fmla, Expr)
        ret = Some(node.ivy_node, node.vars, fmla, node.strat)
        ret._sort = node.sort()
        return ret

    def _finish_unop(self, node: UnOp, expr: Expr) -> UnOp:
        assert isinstance(expr, Expr)
        ret = UnOp(node.ivy_node, node.op, expr)
        ret._sort = node.sort()
        return ret

    # Actions

    def _finish_assert(self, act: Assert, pred: Expr) -> Assert:
        ret = Assert(act.ivy_node, pred)
        ret._sort = act.sort()
        return ret

    def _finish_assign(self, act: Assign, lhs: Expr, rhs: Expr) -> Assign:
        ret = Assign(act.ivy_node, lhs, rhs)
        ret._sort = act.sort()
        return ret

    def _finish_assume(self, act: Assume, pred: Expr) -> Assume:
        ret = Assume(act.ivy_node, pred)
        ret._sort = act.sort()
        return ret

    def _finish_call(self, act: Call, app: Apply) -> Call:
        ret = Call(act.ivy_node, app)
        ret._sort = act.sort()
        return ret

    def _finish_debug(self, act: Debug, args: list[Binding[Expr]]) -> Debug:
        assert isinstance(act, Debug)
        assert isinstance(args, list)
        assert all([isinstance(x, Binding) for x in args])
        ret = Debug(act.ivy_node, act.msg, act.args)
        ret._sort = act.sort()
        return ret

    def _finish_ensures(self, act: Ensures, args: Expr) -> Ensures:
        assert isinstance(act, Ensures)
        assert isinstance(args, Expr)
        ret = Ensures(act.ivy_node, args)
        ret._sort = act.sort()
        return ret

    def _finish_havok(self, act: Havok, modifies: list[Expr]):
        assert isinstance(act, Havok)
        assert isinstance(modifies, list)
        assert all([isinstance(elem, Expr) for elem in modifies])
        ret = Havok(act.ivy_node, modifies)
        ret._sort = act.sort()
        return ret

    def _finish_if(self, act, test, then, els):
        assert isinstance(act, If)
        assert isinstance(test, Expr)
        assert isinstance(then, Action)
        assert isinstance(els, Optional[Action])
        ret = If(act.ivy_node, test, then, els)
        ret._sort = act.sort()
        return ret

    def _finish_let(self, act: Let, scope):
        assert isinstance(scope, Action)
        ret = Let(act.ivy_node, act.vardecls, scope)
        ret._sort = act.sort()
        return ret

    def _finish_logical_assign(self, act: LogicalAssign, relsym, args, assn) -> LogicalAssign:
        assert isinstance(assn, Expr)
        ret = LogicalAssign(act.ivy_node, act.relsym, act.vars, act.assign)
        ret._sort = act.sort()
        return ret

    def _finish_native_action(self, act: NativeAct, args) -> NativeAct:
        assert isinstance(args, list)
        assert all([isinstance(elem, Expr) for elem in args])
        ret = NativeAct(act.ivy_node, act.lang, act.fmt, args)
        ret._sort = act.sort()
        return ret

    def _finish_requires(self, act: Requires, pred):
        assert isinstance(pred, Expr)
        ret = Requires(act.ivy_node, pred)
        ret._sort = act.sort()
        return ret

    def _finish_sequence(self, act: Sequence, stmts):
        assert isinstance(stmts, list)
        assert all([isinstance(elem, Action) for elem in stmts])
        ret = Sequence(act.ivy_node, stmts)
        ret._sort = act.sort()
        return ret

    def _finish_while(self, act: While, test, decreases, do):
        assert isinstance(test, Expr)
        # assert isinstance(decreases, Optional[Expr])
        assert isinstance(do, Action)
        ret = While(act.ivy_node, test, decreases, do)
        ret._sort = act.sort()
        return ret


class MutVisitor(Visitor[None]):
    " A base class for mutating visitors, where all operations are procedures and default to no-ops."

    # Expressions

    def _identifier(self, s: str) -> T:
        pass

    def _finish_apply(self, node: Apply, relsym_ret: None, args_ret: list[None]):
        pass

    def _finish_binop(self, node: BinOp, lhs_ret: None, rhs_ret: None):
        pass

    def _finish_exists(self, node: Exists, expr: None):
        pass

    def _finish_field_access(self, node: FieldAccess, struct: None, field_name: None):
        pass

    def _finish_forall(self, node: Forall, expr: None):
        pass

    def _finish_ite(self, node: Ite, test: None, then: None, els: None):
        pass

    def _finish_native_expr(self, node: NativeExpr, args: list[None]):
        pass

    def _finish_some(self, node: Some, fmla: None):
        pass

    def _finish_unop(self, node: UnOp, expr: None):
        pass

    # Actions

    def _finish_assert(self, act: Assert, pred: None):
        pass

    def _finish_assign(self, act: Assign, lhs: None, rhs: None):
        pass

    def _finish_assume(self, act: Assume, pred: None):
        pass

    def _finish_call(self, act: Call, app: None):
        pass

    def _finish_debug(self, act: Debug, args: list[Binding[None]]):
        pass

    def _finish_ensures(self, act: Ensures, pred: None):
        pass

    def _finish_havok(self, act: Havok, modifies: list[None]):
        pass

    def _finish_if(self, act: If, test: None, then: None, els: Optional[None]):
        pass

    def _finish_let(self, act: Let, scope: None):
        pass

    def _finish_logical_assign(self, act: LogicalAssign, relsym: None, args: list[None], assn: None):
        pass

    def _finish_native_action(self, act: NativeAct, args: list[None]):
        pass

    def _finish_requires(self, act: Requires, pred: None):
        pass

    def _finish_sequence(self, act: Sequence, stmts: list[None]):
        pass

    def _finish_while(self, act: While, test: None, decreases: Optional[None], do: None):
        pass

    def _finish_action_def(self, name: str, defn: ActionDefinition, body: None):
        pass

    def _finish_function_def(self, name: str, defn: FunctionDefinition, body: None):
        pass


class SortVisitorOverTerms(MutVisitor):
    sort_visitor: SortVisitor[Sort]

    def __init__(self, sv: SortVisitor[Sort]):
        self.sort_visitor = sv

    def patch_sort(self, a: AST):
        a._sort = self.sort_visitor.visit_sort(a.sort())

    def _constant(self, c: Constant) -> T:
        self.patch_sort(c)

    def _var(self, v: Var) -> T:
        self.patch_sort(v)

    ##

    def _finish_binop(self, node: BinOp, lhs_ret: None, rhs_ret: None):
        self.patch_sort(node)

    def _finish_apply(self, node: Apply, relsym_ret: None, args_ret: list[None]):
        for arg in node.args:
            s = arg.sort()
            if s:
                self.patch_sort(arg)

    def _finish_exists(self, node: Exists, expr: None):
        node.vars = [Binding(b.name, self.sort_visitor.visit_sort(b.decl)) for b in node.vars]

    def _finish_forall(self, node: Forall, expr: None):
        node.vars = [Binding(b.name, self.sort_visitor.visit_sort(b.decl)) for b in node.vars]

    def _finish_let(self, act: Let, scope: None):
        act.vardecls = [Binding(b.name, self.sort_visitor.visit_sort(b.decl)) for b in act.vardecls]

    def _finish_init(self, act: Init, act_t: None) -> None:
        act.params = [Binding(b.name, self.sort_visitor.visit_sort(b.decl)) for b in act.params]

    def _finish_function_def(self, name: str, defn: FunctionDefinition, body: None):
        defn.formal_params = [Binding(b.name, self.sort_visitor.visit_sort(b.decl)) for b in defn.formal_params]

    def _finish_action_def(self, name: str, defn: ActionDefinition, body: None):
        defn.formal_params = [Binding(b.name, self.sort_visitor.visit_sort(b.decl)) for b in defn.formal_params]
        defn.formal_returns = [Binding(b.name, self.sort_visitor.visit_sort(b.decl)) for b in defn.formal_returns]
        pass
