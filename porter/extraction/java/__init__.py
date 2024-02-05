from .terms import UnboxedSort, SortDeclaration, Extractor
from .utils import *

from porter.ast import terms as astterms
from porter.pp.utils import space


def extract(isolate_name: str, prog: astterms.Program) -> Doc:
    extractor = Extractor()
    extractor.visit_program(prog)

    unboxed = UnboxedSort()

    sort_declarer = SortDeclaration()
    sorts = [sort_declarer.visit_sort(s) for name, s in extractor.sorts.items()]

    var_docs = []
    for binding in extractor.individuals:
        var = extractor._constant(binding.name)
        sort = unboxed.visit_sort(binding.decl)
        var_docs.append(sort + space + var + semi)

    action_docs = [b.decl for b in extractor.actions]

    constructor = extractor.cstr(
        isolate_name,
        [b for b in prog.actions if b.decl.kind == astterms.ActionKind.EXPORTED],
        prog.conjectures,
        extractor.inits)

    body = utils.join(sorts, "\n") + Line() + \
           utils.join(var_docs, "\n") + Line() + Line() + \
           constructor + Line() + Line() + \
           utils.join(action_docs, "\n")

    return Text(f"public class {isolate_name} extends Protocol ") + block(body)
