As a project in early development, much of the wisdom around the state of SPy is captured in incidental conversations rather than in formal docs. This page serves as a low-effort place to capture such tidbits; not as valuable as full docs, but also faster to update.

Info on this page may become innacurate quickly; Those adding to this page are encouraged to add a date to new entries, to help readers judge whether the info may be out-of-date.

## Writing SPy Code

### Types
- It's best to let Spy's internal mechanisms handle as much typechecking as possible; especially if you're writing a metafunction, try to avoid writing typechecks, and rely on SPy to handle them based on the types of the provided opimpls. ([discord source](https://discord.com/channels/1378402660914429992/1462123181983662264/1462125351613235281)) (2026-1-17)
- SPy doesn't yet support optional-types, because the C backend doensn't know how to render them (2026-1-7)
  - See [this discord thread](https://discord.com/channels/1378402660914429992/1458284231200473170/1458408155418726571) for discussion on possible implementation

### References
- 'Structs-by-Value' (i.e. structs allocated on the stack, not by pointer) are immutable for now, though eventually they should be mutable see [this docstring](https://github.com/spylang/spy/blob/86888c9b2c03807ab61deab99907a7c998f6d88b/spy/vm/struct.py#L130-L160) for more info.

## Implementating New Features

### New Builtins and Literals
- Some PR's to look at for inspiration:
  - list literals: [#337](https://github.com/spylang/spy/pull/337), [#339](https://github.com/spylang/spy/pull/339)
  - dict literals: [#364](https://github.com/spylang/spy/pull/364), [#370](https://github.com/spylang/spy/pull/370), [#374](https://github.com/spylang/spy/pull/337)
  - slice() and slices: [#345](https://github.com/spylang/spy/pull/345)
