title: SPy Built-In Functions
---

<style> {
  font-family: "Lucida Console", "Courier New", monospace;
}
</style>


## Built-in Functions

### __sizeof__(type) { #markdown data-toc-label='sizeof()' }

:   Returns the size of an instance of `type` in bytes. E.g. `sizeof(i8) == 1`, `sizeof(i32) == 4`, etc.

### __COLOR__(object) -> Literal["red", "blue"] { #markdown data-toc-label='Color()' }
:   Returns the current color of the passed object. Useful in tests.

### __STATIC_TYPE__(object) { #markdown data-toc-label='\_\_STATIC_TYPE\_\_()' }
:   Returns the type of the object determined in a static context. Useful in tests, and used in some of SPy's internal machinery.

## Class and Callable Decorators

### __@struct__

:   Used to create a struct from a class definition. See the [low level memory section on structs](/llmem/#stack-allocated-structs) for more details.

### __@blue__
:   Declares that a function should be executed at [redshift time](https://antocuni.eu/2025/10/29/inside-spy-part-1-motivations-and-goals/#redshifting); that is, at the point when method and function lookups are resolved, and prior to compilation to C or WASM, if any.

### __@blue.generic__
:   Denotes that the decorated function accepts a type as its first argument. Generic functions should return a function object.

```python
  @blue.generic
  def add(T):
      def impl(x:T, y: T) -> T:
          return x + y
      return impl

  def main() -> None:
      print(add[i32](1, 2))
      print(add[str]('hello ', 'world'))
```

### __@blue.metafunc__
:   Unlike `blue.generic` functions, `metafunc`s accept one or more arguments, and return an [OpSpec]() appropriate to those arguments based on their static type.

```python
  from operator import OpSpec

  @blue.metafunc
  def myprint(m_x):
      if m_x.static_type == int:
          def myprint_int(x: int) -> None:
              print(x)
          return OpSpec(myprint_int)

      if m_x.static_type == str:
          def myprint_str(x: str) -> None:
              print(x)
          return OpSpec(myprint_str)

      raise TypeError("don't know how to print this")

  def main() -> None:
      print(42)
      myprint("hello")
      myprint(5.2)  # raises TypeError
```

