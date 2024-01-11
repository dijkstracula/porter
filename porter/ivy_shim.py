import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ivy import ivy_art as iart
from ivy import ivy_actions as iact
from ivy import ivy_compiler as ic
from ivy import ivy_isolate as iiso
from ivy import ivy_logic as il
from ivy import logic as ilog
from ivy import ivy_module as imod

from . import ast
from .ast import Binding, Sort


def compile_progtext(path: Path) -> iart.AnalysisGraph:
    logging.info(f"Compiling {path}")
    cwd = os.getcwd()
    os.chdir(path.parent)
    with open(path) as f:
        ic.ivy_load_file(f, create_isolate=False)
        iiso.create_isolate('this')
    os.chdir(cwd)

    # Records

    @dataclass
    class Record:
        fields: list[Binding[Sort]]

    return ic.ivy_new()


def handle_isolate(path: Path):
    with imod.Module() as im:
        ag = compile_progtext(path)
        print(im.sort_destructors)
        import pdb;
        pdb.set_trace()


def binding_from_ivy_const(im: imod.Module, c: ilog.Const) -> ast.Binding[Sort]:
    name = c.name
    sort = sort_from_ivy(im, c.sort)
    return ast.Binding(name, sort)


def strip_prefixes(pref: list[str], sep: str, s: str) -> str:
    pref = sep.join(pref) + sep
    if s.startswith(pref):
        return s[len(pref):]
    return s


def action_from_ivy(im: imod.Module, iaction: iact.Action) -> ast.ActionDefinition:
    formal_params = []
    for p in iaction.formal_params:
        binding = binding_from_ivy_const(im, p)
        binding.name = strip_prefixes(["fml"], ":", binding.name)
        formal_params.append(binding)

    formal_returns = []
    for p in iaction.formal_returns:
        binding = binding_from_ivy_const(im, p)
        binding.name = strip_prefixes(["fml"], ":", binding.name)
        formal_returns.append(binding)

    body = []
    for a in iaction.args:
        pass  # body.append(action_from_ivy(im, a))
    return ast.ActionDefinition(formal_params, formal_returns, body)


def record_from_ivy(im: imod.Module, name: str) -> ast.Record:
    if name not in im.sort_destructors:
        raise Exception(f"is {name} the name of a class?")

    # TODO: we should accumulate scopes, I think - nested classes may require more than one name
    # to be stripped.  Should name instead be a scoping context, maybe of type [str]?

    fields = []
    for c in im.sort_destructors[name]:
        f = binding_from_ivy_const(im, c)
        f.name = strip_prefixes([name], ".", f.name)
        assert isinstance(f.decl, ast.FunctionSort)
        f.decl = f.decl.range
        fields.append(f)

    actions = []
    for (action_name, action) in im.actions.items():
        if not action_name.startswith(name):
            continue
        action_name = strip_prefixes([name], ".", action_name)
        action = action_from_ivy(im, action)
        actions.append(Binding(action_name, action))

    return ast.Record(fields, actions)


def sort_from_ivy(im: imod.Module, sort) -> ast.Sort:
    if hasattr(sort, "name"):
        name = sort.name
        if name == "bool":
            return ast.BoolSort()
        if name == "int":
            return ast.NumericSort.int_sort()
        if name == "nat":
            return ast.NumericSort.nat_sort()
        if isinstance(sort, ilog.UninterpretedSort):
            return ast.UninterpretedSort(name)
    else:
        if isinstance(sort, ilog.EnumeratedSort):
            discriminants = [str(x) for x in sort.extension]
            return ast.EnumSort(discriminants)
        if isinstance(sort, ilog.FunctionSort):
            domain = [sort_from_ivy(im, s) for s in sort.domain]
            ret = sort_from_ivy(im, sort.range)
            return ast.FunctionSort(domain, ret)
    raise Exception(f"TODO {type(sort)}")
