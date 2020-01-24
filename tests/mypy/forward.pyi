from abserde import abserde
from typing import overload
from typing_extensions import Literal

@abserde
class Example:
    a: int
    b: Test

@abserde
class Test:
    c: str