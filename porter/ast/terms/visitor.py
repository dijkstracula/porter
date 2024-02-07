from typing import Generic

from porter.ast.sorts import Bool, BitVec, Enumeration, Function, Number, Uninterpreted
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

    scopes: list[str] = []

    def visit_program(self, prog: Program):
        self._begin_program(prog)

        self.sorts = {b.name: b.decl for b in prog.sorts}
        self.individuals = prog.individuals
        self.inits = [self.visit_action(a) for a in prog.inits]

        self.actions = []
        for binding in prog.actions:
            name = binding.name
            action = binding.decl

            self._begin_action_def(name, action)
            body = self.visit_action(action.body)

            self.scopes.append(name)
            self.actions.append(Binding(name, self._finish_action_def(name, action, body)))
            self.scopes.pop()

        self.functions = []
        for binding in prog.functions:
            name = binding.name
            func = binding.decl

            self._begin_function_def(name, func)
            body = self.visit_expr(func.body)

            self.scopes.append(name)
            self.functions.append(Binding(name, self._finish_function_def(name, func, body)))
            self.scopes.pop()

    def _begin_program(self, prog: Program):
        pass

    # Lambda-oids

    def _begin_action_def(self, name: str, defn: ActionDefinition):
        pass

    def _finish_action_def(self,
                           name: str,
                           defn: ActionDefinition,
                           body: T) -> T:
        raise UnimplementedASTNodeHandler(ActionDefinition)

    def _begin_function_def(self, name: str, defn: FunctionDefinition):
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
                self._begin_apply(node)
                relsym = self._constant(relsym)
                args = [self.visit_expr(arg) for arg in args]
                return self._finish_apply(node, relsym, args)
            case BinOp(_, lhs, _op, rhs):
                self._begin_binop(node)
                lhs_ret = self.visit_expr(lhs)
                rhs_ret = self.visit_expr(rhs)
                return self._finish_binop(node, lhs_ret, rhs_ret)
            case Constant(_, rep):
                return self._constant(rep)
            case Var(_, rep):
                return self._var(rep)
            case Exists(_, vars, expr):
                self._begin_exists(node)
                expr = self.visit_expr(expr)
                return self._finish_exists(node, expr)
            case Forall(_, vars, expr):
                self._begin_forall(node)
                expr = self.visit_expr(expr)
                return self._finish_forall(node, expr)
            case Ite(_, test, then, els):
                self._begin_ite(node)
                test = self.visit_expr(test)
                then = self.visit_expr(then)
                els = self.visit_expr(els)
                return self._finish_ite(node, test, then, els)
            case Some(_, vars, fmla, _strat):
                self._begin_some(node)
                fmla = self.visit_expr(fmla)
                return self._finish_some(node, fmla)
            case UnOp(_, _op, expr):
                self._begin_unop(node)
                expr = self.visit_expr(expr)
                return self._finish_unop(node, expr)
        raise Exception(f"TODO: {node}")

    def _constant(self, rep: str) -> T:
        raise UnimplementedASTNodeHandler(Constant)

    def _var(self, rep: str) -> T:
        raise UnimplementedASTNodeHandler(Var)

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

    def _finish_exists(self, node: Exists, expr: T):
        raise UnimplementedASTNodeHandler(Exists)

    def _begin_forall(self, node: Forall):
        pass

    def _finish_forall(self, node: Forall, expr: T):
        raise UnimplementedASTNodeHandler(Forall)

    def _begin_ite(self, node: Ite):
        pass

    def _finish_ite(self, node: Ite, test: T, then: T, els: T) -> T:
        raise UnimplementedASTNodeHandler(Ite)

    def _begin_some(self, node: Some):
        pass

    def _finish_some(self, node: Some, fmla: T):
        raise UnimplementedASTNodeHandler(Some)

    def _begin_unop(self, node: UnOp):
        pass

    def _finish_unop(self, node: UnOp, expr: T):
        raise UnimplementedASTNodeHandler(UnOp)

    # Actions

    def visit_action(self, node: Action) -> T:
        match node:
            case Assert(_, pred):
                self._begin_assert(node)
                pred = self.visit_expr(pred)
                return self._finish_assert(node, pred)
            case Assign(_, lhs, rhs):
                self._begin_assign(node)
                lhs = self.visit_expr(lhs)
                rhs = self.visit_expr(rhs)
                return self._finish_assign(node, lhs, rhs)
            case Assume(_, pred):
                self._begin_assume(node)
                pred = self.visit_expr(pred)
                return self._finish_assume(node, pred)
            case Call(_, app):
                self._begin_call(node)
                app = self.visit_expr(app)
                return self._finish_call(node, app)
            case Debug(_, _msg, args):
                self._begin_debug(node)
                args = [Binding(b.name, self.visit_expr(b.decl)) for b in args]
                return self._finish_debug(node, args)
            case Ensures(_, pred):
                self._begin_ensures(node)
                pred = self.visit_expr(pred)
                return self._finish_ensures(node, pred)
            case Havok(_, modifies):
                self._begin_havok(node)
                modifies = [self.visit_expr(e) for e in modifies]
                return self._finish_havok(node, modifies)
            case If(_, test, then, els):
                self._begin_if(node)
                test = self.visit_expr(test)
                then = self.visit_action(then)
                if els is not None:
                    els = self.visit_action(els)
                return self._finish_if(node, test, then, els)
            case Let(_, _vardecls, scope):
                self._begin_let(node)
                scope = self.visit_action(scope)
                return self._finish_let(node, scope)
            case LogicalAssign(_, _vardecls, assign):
                self._begin_logical_assign(node)
                assign = self.visit_action(assign)
                return self._finish_logical_assign(node, assign)
            case Native(_, _lang, _fmt, args):
                self._begin_native(node)
                args = [self.visit_expr(arg) for arg in args]
                return self._finish_native(node, args)
            case Requires(_, pred):
                self._begin_requires(node)
                pred = self.visit_expr(pred)
                return self._finish_requires(node, pred)
            case Sequence(_, stmts):
                self._begin_sequence(node)
                stmts = [self.visit_action(stmt) for stmt in stmts]
                return self._finish_sequence(node, stmts)
            case While(_, test, decreases, do):
                self._begin_while(node)
                test = self.visit_expr(test)
                if decreases is not None:
                    decreases = self.visit_expr(decreases)
                do = self.visit_action(do)
                return self._finish_while(node, test, decreases, do)
        raise Exception(f"TODO: {node}")

    def _begin_assert(self, act: Assert):
        pass

    def _finish_assert(self, act: Assert, pred: T):
        raise UnimplementedASTNodeHandler(Assert)

    def _begin_assign(self, act: Assign):
        pass

    def _finish_assign(self, act: Assign, lhs: T, rhs: T):
        raise UnimplementedASTNodeHandler(Assign)

    def _begin_assume(self, act: Assume):
        pass

    def _finish_assume(self, act: Assume, pred: T):
        raise UnimplementedASTNodeHandler(Assume)

    def _begin_call(self, act: Call):
        pass

    def _finish_call(self, act: Call, app: T):
        raise UnimplementedASTNodeHandler(Call)

    def _begin_debug(self, act: Debug):
        pass

    def _finish_debug(self, act: Debug, args: list[Binding[T]]):
        raise UnimplementedASTNodeHandler(Debug)

    def _begin_ensures(self, act: Ensures):
        pass

    def _finish_ensures(self, act: Ensures, pred: T):
        raise UnimplementedASTNodeHandler(Ensures)

    def _begin_havok(self, act: Havok):
        pass

    def _finish_havok(self, act: Havok, modifies: list[T]):
        raise UnimplementedASTNodeHandler(Havok)

    def _begin_if(self, act: If):
        pass

    def _finish_if(self, act: If, test: T, then: T, els: Optional[T]):
        raise UnimplementedASTNodeHandler(If)

    def _begin_let(self, act: Let):
        pass

    def _finish_let(self, act: Let, scope: T):
        raise UnimplementedASTNodeHandler(Let)

    def _begin_logical_assign(self, act: LogicalAssign):
        pass

    def _finish_logical_assign(self, act: LogicalAssign, assn: T):
        raise UnimplementedASTNodeHandler(LogicalAssign)

    def _begin_native(self, act: Native):
        pass

    def _finish_native(self, act: Native, args: list[T]):
        raise UnimplementedASTNodeHandler(Native)

    def _begin_requires(self, act: Requires):
        pass

    def _finish_requires(self, act: Requires, pred: T):
        raise UnimplementedASTNodeHandler(Requires)

    def _begin_sequence(self, act: Sequence):
        pass

    def _finish_sequence(self, act: Sequence, stmts: list[T]):
        raise UnimplementedASTNodeHandler(Sequence)

    def _begin_while(self, act: While):
        pass

    def _finish_while(self, act: While, test: T, decreases: Optional[T], do: T):
        raise UnimplementedASTNodeHandler(While)


class MutVisitor(Visitor[None]):
    " A base class for mutating visitors, where all operations are procedures and default to no-ops."

    # Expressions

    def _constant(self, rep: str):
        pass

    def _var(self, rep: str):
        pass

    def _finish_apply(self, node: Apply, relsym_ret: None, args_ret: list[None]):
        pass

    def _finish_binop(self, node: BinOp, lhs_ret: None, rhs_ret: None):
        pass

    def _finish_exists(self, node: Exists, expr: None):
        pass

    def _finish_forall(self, node: Forall, expr: None):
        pass

    def _finish_ite(self, node: Ite, test: None, then: None, els: None):
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

    def _finish_logical_assign(self, act: LogicalAssign, assn: None):
        pass

    def _finish_native(self, act: Native, args: list[None]):
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
