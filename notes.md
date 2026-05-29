Next steps:

Variables declared inside of exec statements aren't allowed - something about how the symtables are getting merged doesn't work
Look at `vm.exec_source()`

5/22 - Fixed (maybe?) an issue with symtable updating. Now it seems that classdefs always being "const" is going to get in the way of dataclasses...

5/22 - Changing `def declare_ClassDef(self, classdef: ast.ClassDef)` to be "var" type instead of const solves this issue, except that then `item` is red but dataclass is a blue...
    - Update - classdefs can be const but we just can't reuse a name... but using a new name works with classdefs as const!

5/22 - May need to store locals to make @struct classdefs work in exec. See current structure of `d1.spy` and `dtest.spy`

5/27 - Forward-declare all classdegs in exec_source helps with the issue of classdefs. We can now declare a class within exec.
5/27 - I don't know if there is a way to get the annotations from class in SPy yet, which would be the next step in dataclasses I think.
5/27 - Can't assign new attributes to classes, but could dynamically create new class with exec?

5/27 - Can now exec statements in spdb by default! Only statements, not expressions yet...

5/29 - Wrote some tests, exec roughly works. It doesn't work for things that break 
5/29 - Branch pyrepl-rough-closurevars has some work with a new test in `test_builtins`, trying to get `exec`'d functions to close over outer variables...but it breaks things...