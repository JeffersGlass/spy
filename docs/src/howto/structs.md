title: Struct Classes
---

Struct classes (currently the only classes in SPy) are immutable data structures analagous to C structs. 

## Declaration

Struct classes are declared with the `@struct` decorator on the class definition. Their fixed list of fields follows with type annotations. Note that default values for these fields are not currently supported.

```py
@struct
class Person:
    name: str
    age: int

def main() -> None:
    p = Person('Alice', 99)
    print(p.name, "is", p.age, "years old")
```

Struct classes may also be defined with the [generic class syntax](../howto/generics.md#generic-class-syntax), which is syntactic sugar for a generic function which defines an internal struct. See the [generics](../howto/generics.md) documentation for more info.

## Attributes

Attributes of struct classes do not support assignment after creation. Using the same `point` class from above:

```py
def main() -> None:
    p = Person('Alice', 99)
    p.name = 'Bob' # TypeError: type `Person` does not support assignment to attribute 'name'
```

However, objects which are attributes of struct classes may be mutated:

```py
@struct
class Person:
    name: str
    age: int
    books: list[str]


def main() -> None:
    p = Person('Alice', 99, [])
    print(p.name, "has", len(p.books), "book(s)") # Alice has 0 book(s)

    p.books.append("An Introduction to Python")
    print(p.name, "has", len(p.books), "book(s)") # Alice has 1 book(s)
```

## Constructors

Struct classes use a default constructor which populates all their attributes in-order, and all attributes must be provided each time the default constructor is called. E.g. the example above, the constructor `p = Person('Alice', 99, [])` requires an empty list to be passed for the `books` attribute. We can call this constructor explicitly using the `__make__` method:

```py
@struct
class Person:
    name: str
    age: int
    books: list[str]

def main() -> None:
    p = Person.__make__('Bob', 6, [])
    print(p.age) # 6
```

User-facing constructors can be customized by overwriting the `__new__` method; the `__make__` must be called within to handle the initialization of the complete struct. Note that `__new__` functions like a staticmethod (it does not take a `self` parameter)

```py
@struct
class Person:
    name: str
    age: int
    books: list[str]

    def __new__(name: str, age: int) -> Person:
        _books: list[str] = []
        return Person.__make__(name, age, _books)

def main() -> None:
    p = Person('Alice', 99)
    print(p.name, "has", len(p.books), "books") # Alice has 0 books
```

<!-- 
    TODO Add notes about metafuncs as constructors. This may be more or less useful once typing for things
    like `str | None` is available.
-->

## Methods

Struct classes may have methods defined inside their class body; the struct object itself is passed as the first parameter (usually called `self`), just as in CPython:

```py
@struct
class Person:
    name: str
    
    def say_hi_to(self, other: Person) -> None:
        print("Hi " + other.name + "! My name is " + self.name)

    def is_teenager(self) -> bool:
        return 13 <= self.age and self.age <= 19

def main() -> None:
    c = Person("Charlie", 55)
    c.say_hi_to(Person("Donna", 57))     # Hi Donna! My name is Charlie
    print(c.is_teenager())               # False
```

Methods may also be [blue functions](../reference/spy_builtin_functions.md#blue), [generic blue functions](../reference/spy_builtin_functions.md#bluegeneric), or [metafunctions](../reference/spy_builtin_functions.md#bluemetafunc).

## Special Methods

Struct classes may have the following double-underscope methods overridden:

### `__str__(self) -> str`

Called to implement the builtin [`str()`](../reference/python_builtins.md#strobject) is called on this object.

### `__repr__(self) -> str`

Called to implement the builtin [`repr()`](../reference/python_builtins.md#reprobject) is called on this object, either explicitly or as part of printing another object.

### `__len__(self) -> int`

Called to implement the builtin [`len()`](../reference/python_builtins.md#lenobject) is called on this object; represents the number of objects in a container:

### `__getitem__(self, i: int) -> Object`

Called to implement subscription; that is, `self[subscript]`. Often used to retrieve the i-th object in a collection. In SPy, the return value is often typed as part of a [Generic Class](../howto/generics.md#generic-class-syntax):

```py
@struct
class LabeledData[T]:
    label: str
    data: T

@struct
class LabeledContainer[T]:
    items: list[LabeledData[T]]

    def __getitem__(self, i: int) -> LabeledData[T]:
        return self.items[i]

def main() -> None:
    cont = LabeledContainer[float]([])
    cont.items.append(LabeledData[float]('temperature', 98.6))
    cont.items.append(LabeledData[float]('humidity', 43.2))
    for i in range(len(cont.items)):
        print(cont[i].label, ":", cont[i].data)

    # temperature : 98.6
    # humidity : 43.2
```

### `__setitem__(self, i: int, value: Object ) -> Object`

Set the i-th object in a collection. In SPy, the return value is often typed as part of a [Generic Class](../howto/generics.md#generic-class-syntax).

## Conversion Methods

### `__convert_to__(m_expT, m_gotT, m_x) -> Object`
### `__convert_from__(m_expT, m_gotT, m_x) -> Object`

Both `__convert_to__` and `__convert_from__` are Metafuncs which may be defined on a type to provide an explicit method of conversion to another type.

```py
from operator import OpSpec

@struct
class SillyInt:
    # A string which can act like an integer of it's own length. How silly!
    content: str

    @blue.metafunc
    def __convert_to__(m_expT, m_gotT, m_x):
        expT = m_expT.blueval  # expected type
        if expT == int:
            def conv(s: SillyInt) -> int:
                return len(s.content)

            return OpSpec(conv, [m_x])

        return OpSpec.NULL

    @blue.metafunc
    def __convert_from__(m_expT, m_gotT, m_x):
        gotT = m_gotT.blueval  # got type
        if gotT == int:

            def conv(x: int) -> SillyInt:
                return SillyInt("a" * x)

            return OpSpec(conv, [m_x])

        return OpSpec.NULL

def add_one(x: int) -> int:
    return x + 1

def main() -> None:
    silly = SillyInt("This string acts like the number 35")
    print(add_one(silly)) # 36

    sillier: SillyInt = 5
    print(sillier.content) # aaaa
```

## `__call__(self, [args])`

Called when the instance is called as a function.

```py
@struct
class CallablePerson:
    name: str

    def __call__(self) -> None:
        print("Ring ring! You called", self.name)

def main() -> None:
    p = CallablePerson("Edgar")
    p() # Ring ring! You called Edgar
```

## Binary Operators

The following double-underscore binary operators may be overridden; their behavior is the same as in [CPython](https://docs.python.org/3/reference/datamodel.html#basic-customization): `__sub__`, `__mul__`, `__div__`, `__floordiv__`, `__mod__`, `__lshift__`, `__rshift__`, `__and__`, `__or__`, `__xor__`, `__eq__`, `__ne__`, `__lt__`, `__le__`, `__gt__`, `__ge__`, 

## Unary Operators

The following double-underscore unary operators may be overridden; their behavior is the same as in [CPython](): `__neg__`.

## Attribute Access

### `__getattribute__(self, name: str)`

### `__getattr__(self, name: str)`

<!-- 

#### `__get__(self, v: )

Comment from operator/attrop.py

def default_getattribute(
    vm: "SPyVM", wam_obj: W_MetaArg, wam_name: W_MetaArg, name: str
) -> W_OpSpec:
    # default logic for objects which don't implement __getattribute__. This
    # is the equivalent of CPython's object.c:PyObject_GenericGetAttr, and
    # corresponds more or less to object.__getattribute__.
    #
    # There is a big difference compared to Python, though.
    #   <python>
    #     1. try to find a data descriptor on the type
    #     2. try to look inside obj.__dict__
    #     3. try to find a non-data descriptor on the type
    #     4. try to find a normal attribute on the type
    #     5. AttributeError
    #   </python>
    #
    # This means that e.g. an instance can override methods via its __dict__.
    #
    # The SPy logic must be different, because we want to be able to resolve
    # the getattribute during redshift: in particular, during redshift we know
    # the static types but we DO NOT know the content of obj.__dict__ (if obj
    # is red). So, we tweak the logic:
    #   <spy>
    #     1. try to find a descriptor on the type
    #     2. try to find a normal attribute on the type
    #     3. try to look inside obj.__dict__ (if present)
    #     4. AttributeError
    #   </spy>
    #
    # This means that individual instances can NEVER override attributes
    # provided by their type. This also means that we no longer need the
    # distinction between data and non-data descriptors (as all descriptors
    # have the precedence anyway).
    #
    # Also note that contrarily to Python, in SPy instances don't have a
    # __dict__ by default. (__dict__ support not implemented yet ATM).

--->