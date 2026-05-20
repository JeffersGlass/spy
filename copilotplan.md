## Plan: Implement exec() builtin

TL;DR: Add a new VM helper to parse and execute source strings in a temporary module, expose it as `builtins.exec`, and cover it with runtime and error tests.

**Steps**
1. Update `spy/vm/vm.py`.
   - Add a counter field for temporary exec module names.
   - Add a method like `exec_source(self, source: str, *, filename: Optional[str] = None) -> None`.
   - In that method:
     - create a pseudo-filename via `record_src_in_linecache(source, name="exec")` when one is not provided.
     - parse the string with `Parser(source, filename)`.
     - analyze the result with `ScopeAnalyzer(temp_modname, module)` and attach the symtable.
     - create a temporary module name such as `__exec__0` and instantiate `ModFrame(self, FQN(modname), module)`.
     - run the module frame.
   - Keep execution isolated in its own temp module because the current VM/runtime does not expose caller-frame namespace injection.

2. Add the builtin in `spy/vm/modules/builtins.py`.
   - Define `w_exec(vm: SPyVM, w_src: W_Str) -> None` using `@BUILTINS.builtin_func`.
   - Unwrap the source string with `vm.unwrap_str(w_src)`.
   - Call the new `vm.exec_source` helper.
   - Return `B.w_None`.

3. Add tests for the new behavior.
   - In `spy/tests/compiler/test_builtins.py`, add cases that:
     - call `exec("x = 1")` and succeed at runtime.
     - raise a parse error when the exec source is invalid.
   - Optionally add a VM-level test in `spy/tests/vm/test_builtin.py` for `vm.exec_source(...)` if direct helper coverage is desired.

**Relevant files**
- `spy/vm/vm.py` — add temp exec module bookkeeping and the source execution helper.
- `spy/vm/modules/builtins.py` — add the `exec` builtin wrapper.
- `spy/analyze/scope.py` / `spy/vm/modframe.py` — reuse existing module analysis and execution pipeline.
- `spy/util.py` — use `record_src_in_linecache` for pseudo-filename support.
- `spy/tests/compiler/test_builtins.py` — add runtime tests for `exec`.

**Verification**
1. Run the new builtin through `pytest spy/tests/compiler/test_builtins.py`.
2. Confirm `exec("x = 1")` executes without raising.
3. Confirm invalid `exec` source raises a parse error with a meaningful location.
4. Optionally verify `exec` code is recorded in linecache with a pseudo-filename like `<exec-0>`.

**Decision**
- Implement only basic `exec(source)` semantics for now, not full `globals`/`locals` support.
- The code will execute in a new temporary module because the VM does not currently provide caller-frame namespace injection.

**Further considerations**
1. If later required, extend this to accept an explicit execution namespace and/or dynamic imports by expanding `ImportAnalyzer` or adding a `globals`/`locals` mechanism.
