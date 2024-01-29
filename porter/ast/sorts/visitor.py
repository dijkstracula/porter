from typing import Generic, Optional, TypeVar

from porter.ast.sorts import Bool, BitVec, Enumeration, ExtensionalRelation, Function, Number, Uninterpreted, Sort

T = TypeVar("T")


class UnimplementedASTNodeHandler(Exception):
    def __init__(self, cls: type):
        self.cls = cls

    def __str__(self):
        return f"Unimplemented AST visitor for {self.cls.__module__}.{self.cls.__name__}"


# noinspection PyMethodMayBeStatic,PyShadowingBuiltins
class Visitor(Generic[T]):
    # Sorts

    def visit_sort(self, sort: Sort) -> T:
        match sort:
            case Bool():
                return self.bool()
            case BitVec(name, width):
                return self.bv(name, width)
            case Enumeration(name, discs):
                return self.enum(name, discs)
            case ExtensionalRelation(domain, range):
                self._begin_extensional(sort)
                domain = [self.visit_sort(d) for d in domain]
                range = self.visit_sort(range)
                return self._finish_extensional(sort, domain, range)
            case Function(domain, range):
                self._begin_function(sort)
                domain = [self.visit_sort(d) for d in domain]
                range = self.visit_sort(range)
                return self._finish_function(sort, domain, range)
            case Number(name, lo, hi):
                return self.numeric(name, lo, hi)
            case Uninterpreted(name):
                return self.uninterpreted(name)
        raise Exception(f"TODO: {sort}")

    def bool(self) -> T:
        raise UnimplementedASTNodeHandler(Bool)

    def bv(self, name: str, width: int) -> T:
        raise UnimplementedASTNodeHandler(BitVec)

    def enum(self, name: str, discriminants: tuple[str, ...]):
        raise UnimplementedASTNodeHandler(Enumeration)

    def _begin_extensional(self, node: ExtensionalRelation):
        pass

    def _finish_extensional(self, node: ExtensionalRelation, domain: list[T], range: T) -> T:
        raise UnimplementedASTNodeHandler(ExtensionalRelation)

    def _begin_function(self, node: Function):
        pass

    def _finish_function(self, node: Function, domain: list[T], range: T) -> T:
        raise UnimplementedASTNodeHandler(Function)

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        raise UnimplementedASTNodeHandler(Number)

    def uninterpreted(self, name: str) -> T:
        raise UnimplementedASTNodeHandler(Uninterpreted)
