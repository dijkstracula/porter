from ivy import ivy_compiler as ic
from ivy import ivy_module as imod
from ivy import ivy_isolate as iiso

import io


def isolate_boilerplate(contents: str) -> str:
    return "\n".join(["#lang ivy1.8",
                      "include numbers",
                      f"{contents}"])


def test_trivial():
    mod = "module nat_pair = {" \
          "  var x: nat" \
          "  var y: nat" \
          "}"

    with imod.Module() as im:
        iso = isolate_boilerplate(mod)
        ic.ivy_load_file(io.StringIO(iso), create_isolate=False)
        iiso.create_isolate('this')
        ic.ivy_new()
