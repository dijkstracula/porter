from ivy import ivy_actions as ia
from ivy import ivy_compiler as ic
from ivy import ivy_isolate as iiso
from ivy import ivy_utils as iu


def init_parameters():
    # from ivy_to_cpp::main_int().
    iu.set_parameters({
        'coi': 'false',
        "create_imports": 'true',
        "enforce_axioms": 'true',
        'ui': 'none',
        'isolate_mode': 'test',
        'assume_invariants': 'false',
        'compile_with_invariants': 'true',
        'keep_destructors': 'true'
    })
    ia.set_determinize(True)
    iiso.set_interpret_all_sorts(True)
    ic.set_verifying(False)
