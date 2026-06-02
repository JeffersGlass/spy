## Plan: Implement frame-aware exec() builtin

TL;DR: Add `exec(source)` support that can run inside the current SPy frame, not only in an isolated temporary module. This requires a frame-aware helper in `SPyVM`, a special call-site path in `ASTFrame.eval_expr_Call`, and tests covering module and function-frame execution.

**Steps**
1. Update `spy/vm/vm.py`.
   - Add a frame-aware helper such as `exec_source(self, source: str, frame: Optional[AbstractFrame] = None, *, filename: Optional[str] = None) -> None`.
   - Add a small helper or VM field if needed to track the current executing SPy frame while interpreting code.
   - In `exec_source`:
     - create a pseudo-filename via `record_src_in_linecache(source, name="exec")` when one is not provided.
     - parse the string with `Parser(source, filename)` or `Parser(source, filename).parse_all()`.
     - analyze the result with `ScopeAnalyzer` and attach the symtable.
     - if a target frame is provided, execute the parsed code in that frame’s namespace instead of creating a stand-alone temp module.
     - otherwise fall back to isolated execution in a temporary module.
   - Implement a lightweight execution wrapper for the target frame:
     - add an `ExecFrame` helper that can reuse the target frame’s `symtable`, `locals`, and closure information.
     - make `ExecFrame.store_local` and `load_local` delegate to the underlying frame when appropriate, so `exec()` can mutate the current local namespace.
     - ensure module-level names written by `exec()` still update globals in the current module frame when invoked from a module context.

2. Update `spy/vm/modules/builtins.py`.
   - Define `w_exec(vm: SPyVM, src: W_Str) -> W_Object` using `@BUILTINS.builtin_func`.
   - Unwrap the source string with `src.spy_unwrap(vm)`.
   - Call `vm.exec_source` without committing to a temporary module; let the current frame select the namespace.
   - Return `B.w_None`.

3. Update `spy/vm/astframe.py`.
   - In `ASTFrame.eval_expr_Call`, special-case calls to `B.w_exec`.
   - When `exec()` is called, execute the source string immediately in the current ASTFrame/DopplerFrame using the new `vm.exec_source(..., frame=self)` helper.
   - Return `B.w_None` directly instead of going through the normal call op path.
   - This is the key step that allows `exec()` to act inside the active caller frame.

4. Reuse and extend existing analysis/execution infrastructure.
   - Use `Parser`, `ScopeAnalyzer`, and `ModFrame`/`ExecFrame` rather than inventing a separate interpreter for exec code.
   - If the parsed source is multiple statements, wrap them in a synthetic module or block AST that can be analyzed by `ScopeAnalyzer`.
   - If the target frame is a module frame, the execution should behave like module top-level `exec`, updating the module dict.
   - If the target frame is a function frame, the execution should behave like a function-local dynamic evaluation, mutating local variables in the current frame.

5. Add tests for the new behavior.
   - In `spy/tests/compiler/test_builtins.py`, add cases for:
     - `exec("x = 1")` at module level and verifying `x == 1`.
     - `exec("x = 2")` inside a function, then verify the local variable is visible after the call.
     - `exec("x = 3\nreturn x")` or similar inside a function body when permitted.
     - invalid source raising a parse error with a meaningful location.
   - Add a frame-specific test that exercises `exec()` from within a nested function or active interpreter frame, showing that the target frame’s namespace is used.
   - Optionally add a VM-level test for `vm.exec_source(..., frame=some_frame)` if direct helper coverage is needed.

**Relevant files**
- `spy/vm/vm.py` — add frame-aware exec helper and optional current-frame tracking.
- `spy/vm/astframe.py` — special-case `exec()` calls so the current frame is provided.
- `spy/vm/modules/builtins.py` — define the builtin wrapper.
- `spy/vm/modframe.py` / a new `spy/vm/execframe.py` — support execution using an existing frame’s namespace.
- `spy/analyze/scope.py` — analyze dynamically parsed exec source with the proper symbol table.
- `spy/util.py` — generate pseudo-filenames for exec source with `record_src_in_linecache`.
- `spy/tests/compiler/test_builtins.py` — add runtime tests for frame-aware exec.

**Verification**
1. Run `pytest spy/tests/compiler/test_builtins.py`.
2. Confirm module-level `exec("x = 1")` works.
3. Confirm function-level `exec("x = 1")` mutates the local namespace of the caller frame.
4. Confirm invalid exec source raises a parse error with a useful traceback location.
5. Optionally verify dynamic exec source shows up in linecache with a pseudo-filename like `<exec-0>`.

**Decision**
- Implement basic `exec(source)` semantics in the current frame; do not yet add explicit `globals`/`locals` parameters.
- Prefer a caller-frame execution path over isolated temp-module-only execution so `exec()` works within any SPy frame.

**Further considerations**
1. Later, add explicit `globals`/`locals` support.
2. If Python-compatible exec semantics are required, extend the symbol resolution logic so names assigned in `exec()` are correctly resolved as locals, globals, or closure variables depending on the frame.
3. Add support for `exec()` in class bodies and debugger evaluation contexts once the frame wrapper is stable.
