from typing import TYPE_CHECKING, Any

from spy.vm.b import B
from spy.vm.object import W_Object
from spy.vm.opspec import W_MetaArg

if TYPE_CHECKING:
    from spy.vm.vm import SPyVM


@B.builtin_type("Slice")
class W_Slice(W_Object):
    __spy_storage_category__ = "value"

    start: W_MetaArg
    stop: W_MetaArg
    step: W_MetaArg

    def __init__(self, start: W_MetaArg, stop: W_MetaArg, step: W_MetaArg) -> None:
        self.start = start
        self.stop = stop
        self.step = step

    def spy_unwrap(self, vm: "SPyVM") -> slice:
        return slice(self.start, self.stop, self.step)

    def spy_key(self, vm: "SPyVM") -> Any:
        return ("slice", self.start, self.stop, self.step)

    def __repr__(self) -> str:
        return f"W_Slice({self.start}, {self.stop}, {self.step})"
