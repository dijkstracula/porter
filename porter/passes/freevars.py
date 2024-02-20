from porter.ast import terms
from porter.ast.terms import Var
from porter.ast.terms.visitor import MutVisitor


# Produces all free Vars in an AST.
class FreeVars(MutVisitor):
    vars: set[str]

    def __init__(self):
        self.vars = set()

    def _var(self, v: Var):
        if not self._in_scope(v.rep):
            self.vars.add(v.rep)