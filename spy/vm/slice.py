from typing import TYPE_CHECKING, Annotated, Any, Optional

from spy.vm.b import BUILTINS, B
from spy.vm.builtin import builtin_method
from spy.vm.object import W_Object, W_Type

if TYPE_CHECKING:
    from spy.vm.opspec import W_MetaArg, W_OpSpec
    from spy.vm.vm import SPyVM


@B.builtin_type("Slice")
class W_Slice(W_Object):
    __spy_storage_category__ = "value"

    start: int | None
    stop: int | None
    step: int | None

    def __init__(self, start: int | None, stop: int | None, step: int | None) -> None:
        self.start = start
        self.stop = stop
        self.step = step

    def spy_unwrap(self, vm: "SPyVM") -> tuple:
        return slice(self.start, self.stop, self.step)

    def spy_key(self, vm: "SPyVM") -> Any:
        return ("slice", self.start, self.stop, self.step)

    def __repr__(self) -> str:
        return f"W_Slice({self.start}, {self.stop}, {self.step})"
