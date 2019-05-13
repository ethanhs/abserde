from typing import List
from abserde import abserde

@abserde
class Test:
    name: str
    age: int
    foo: List[str]

@abserde
class Test2:
    room: int
    floor: int
