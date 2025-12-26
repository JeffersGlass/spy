from typing import TYPE_CHECKING, Annotated, Any, Optional

from spy.vm.b import BUILTINS, B
from spy.vm.builtin import builtin_method
from spy.vm.object import W_Object, W_Type
from spy.vm.opspec import W_MetaArg, W_OpSpec
from spy.vm.primitive import W_I32

if TYPE_CHECKING:
    from spy.vm.vm import SPyVM


@B.builtin_type("Slice")
class W_Slice(W_Object):
    __spy_storage_category__ = "value"

    start: int
    stop: int
    step: int

    def __init__(self, start: W_I32, stop: W_I32, step: W_I32) -> None:
        self.start = start
        self.stop = stop
        self.step = step

    def spy_unwrap(self, vm: "SPyVM") -> tuple:
        return slice(
            vm.unwrap_i32(self.start),
            vm.unwrap_i32(self.stop),
            vm.unwrap_i32(self.step),
        )

    def spy_key(self, vm: "SPyVM") -> Any:
        return (
            "slice",
            self.start,
            self.stop,
            self.step,
        )

    def __repr__(self) -> str:
        return f"W_Slice({self.start}, {self.stop}, {self.step})"

    @builtin_method("__new__", color="blue", kind="metafunc")
    @staticmethod
    def w_NEW(
        vm: "SPyVM", w_start: W_MetaArg, w_stop: W_MetaArg, w_step: W_MetaArg
    ) -> W_OpSpec:
        def w_new(vm: "SPyVM", *args_w: W_I32) -> W_Slice:
            return W_Slice(w_start, w_stop, w_step)

        return W_OpSpec(w_new, list(w_start, w_stop, w_step))
        ...
