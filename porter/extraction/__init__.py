from ivy import ivy_actions as ia
from ivy import ivy_module as im


class Extractor:
    def extract(self, imod: im.Module) -> str:
        actions = "\n".join([self.extract_action(a) for a in imod.actions])
        types = "\n".join(self.extract_type(t) for t in imod.native_types)
        return "\n".join([actions, types])

    def extract_action(self, a: ia.Action):
        return "TODO"

    def extract_types(self, t):
        return "TODO"
