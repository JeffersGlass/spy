Next steps:

Variables declared inside of exec statements aren't allowed - something about how the symtables are getting merged doesn't work
Look at `vm.exec_source()`

5/22 - Fixed (maybe?) an issue with symtable updating. Now it seems that classdefs always being "const" is going to get in the way of dataclasses...

5/22 - Changing `def declare_ClassDef(self, classdef: ast.ClassDef)` to be "var" type instead of const solves this issue, except that then `item` is red but dataclass is a blue...
    - Update - classdefs can be const but we just can't reuse a name... but using a new name works with classdefs as const!