from porter.ast import terms
from porter.ast.terms.visitor import MutVisitor


# Produces all free Vars in an AST.
class FreeVars(MutVisitor):
    vars: set[str]

    scopes: list[list[str]]

    def _in_scope(self, v: str):
        for scope in self.scopes:
            if v in scope: return True
        return False

    def __init__(self):
        self.vars = set()

    def _var(self, rep: str):
        if not self._in_scope(rep):
            self.vars.add(rep)

    # Certain nodes bind Vars in the context.  Keep track of these binders so we add only free ones!

    def _begin_exists(self, node: terms.Exists):
        self.scopes.append([b.name for b in node.vars])

    def _finish_exists(self, node: terms.Exists, expr: None):
        self.scopes.pop()

    def _begin_forall(self, node: terms.Forall):
        self.scopes.append([b.name for b in node.vars])

    def _finish_forall(self, node: terms.Forall, expr: None):
        self.scopes.pop()

    def _begin_some(self, node: terms.Some):
        self.scopes.append([b.name for b in node.vars])

    def _finish_some(self, node: terms.Some, expr: None):
        self.scopes.pop()
