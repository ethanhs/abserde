from abserde import abserde


@abserde
class Test:
    room: int
    floor: int


@abserde
class Test2:
    name: str
    age: int
    foo: Test
