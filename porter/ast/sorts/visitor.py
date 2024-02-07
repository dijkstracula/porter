from typing import Generic, Optional, TypeVar

from porter.ast.sorts import Bool, BitVec, Enumeration, Function, Native, Number, Record, Uninterpreted, Sort

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
            case BitVec(width):
                return self.bv(width)
            case Enumeration(name, discs):
                return self.enum(name, discs)
            case Function(domain, range):
                self._begin_function(sort)
                domain = [self.visit_sort(d) for d in domain]
                range = self.visit_sort(range)
                return self._finish_function(sort, domain, range)
            case Native(lang, fmt, args):
                return self.native(lang, fmt, args)
            case Number(name, lo, hi):
                return self.numeric(name, lo, hi)
            case Record(_name, fields):
                self._begin_record(sort)
                fields_t = {name: self.visit_sort(sort) for name, sort in fields.items()}
                return self._finish_record(sort, fields_t)
            case Uninterpreted(name):
                return self.uninterpreted(name)
        raise Exception(f"TODO: {sort}")

    def bool(self) -> T:
        raise UnimplementedASTNodeHandler(Bool)

    def bv(self, width: int) -> T:
        raise UnimplementedASTNodeHandler(BitVec)

    def enum(self, name: str, discriminants: tuple[str, ...]):
        raise UnimplementedASTNodeHandler(Enumeration)

    def _begin_function(self, node: Function):
        pass

    def _finish_function(self, node: Function, domain: list[T], range: T) -> T:
        raise UnimplementedASTNodeHandler(Function)

    def enum(self, name: str, discriminants: tuple[str, ...]):
        raise UnimplementedASTNodeHandler(Enumeration)

    def native(self, lang: str, fmt: str, args: list[str]):
        raise UnimplementedASTNodeHandler(Native)

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        raise UnimplementedASTNodeHandler(Number)

    def _begin_record(self, rec: Record):
        pass

    def _finish_record(self, rec: Record, fields: dict[str, T]):
        raise UnimplementedASTNodeHandler(Record)

    def uninterpreted(self, name: str) -> T:
        raise UnimplementedASTNodeHandler(Uninterpreted)


class MutVisitor(Visitor[None]):
    def bool(self):
        pass

    def bv(self, width: int):
        pass

    def enum(self, name: str, discriminants: tuple[str, ...]):
        pass

    def _begin_function(self, node: Function):
        pass

    def _finish_function(self, node: Function, domain: list[None], range: None) -> None:
        pass

    def enum(self, name: str, discriminants: tuple[str, ...]):
        pass

    def native(self, lang: str, fmt: str, args: list[str]):
        pass

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        pass

    def _finish_record(self, name: str, fields: dict[str, T]) -> None:
        pass

    def uninterpreted(self, name: str) -> None:
        pass
