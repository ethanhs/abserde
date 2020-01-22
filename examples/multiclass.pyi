from abserde import abserde
from typing import Any

@abserde
class Test:
    room: int
    floor: int


@abserde
class Test2:
    name: Any
    age: int
    foo: Test
