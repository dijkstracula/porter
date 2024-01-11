from . import compile_toplevel


def test_module_simple():
    mod = "module nat_pair = {" \
          "  var x: nat" \
          "  var y: nat" \
          "}"
    compile_toplevel(mod)


def test_module_parameterized():
    mod = "module pair(t) = {" \
          "  var x: t" \
          "  var y: t" \
          "}"
    print(compile_toplevel(mod))
