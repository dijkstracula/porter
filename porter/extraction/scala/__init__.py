from datetime import datetime
import os
import subprocess

from .terms import SortDeclaration, Extractor
from .utils import *

from porter.ast import terms as astterms
from ...pp import Nil


def header() -> Doc:
    p = os.path.dirname(os.path.realpath(__file__))
    cwd = os.getcwd()
    try:
        os.chdir(p)
        curr_commit = subprocess.check_output("git log --oneline | head -n1", shell=True).strip().decode("utf-8")
        now = datetime.now().strftime("%d/%m/%Y at %H:%M:%S")
        return Text(f"/* Autogenerated at {now} at commit {curr_commit} */")
    except Exception as e:
        return Text(f"/* Autogenerated ({str(e)}) */")
    finally:
        os.chdir(cwd)


def extract(isolate_name: str, prog: astterms.Program) -> Doc:
    extractor = Extractor()
    extractor.visit_program(prog)

    sort_declarer = SortDeclaration()
    sorts = [sort_declarer.visit_sort(s) for name, s in extractor.sorts.items()]
    sorts = [s for s in sorts if not isinstance(s, Nil)]

    var_docs = [extractor.vardecl(binding) for binding in extractor.individuals]

    action_docs = [b.decl for b in extractor.actions]
    function_docs = [b.decl for b in extractor.functions]

    inits = extractor.initializers(
        [b for b in prog.actions if b.decl.kind == astterms.ActionKind.EXPORTED],
        prog.conjectures,
        extractor.inits)

    nlnl = Line() + Line()

    body = Nil()
    if len(sorts) > 0:
        body += utils.join(sorts, "\n") + nlnl
    if len(var_docs) > 0:
        body += utils.join(var_docs, "\n") + nlnl
    body += inits

    if len(function_docs) > 0:
        body += utils.join(function_docs, "\n") + nlnl
    if len(action_docs) > 0:
        body += utils.join(action_docs, "\n")

    return header() + Line() + Text(f"class {isolate_name}(a: Arbitrary) extends Protocol(a) ") + block(body)
