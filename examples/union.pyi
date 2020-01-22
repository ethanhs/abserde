from abserde import abserde

@abserde
class Test:
    room: int
    floor: int


@abserde
class Test2:
    age: int
    foo: Union[Test, int]
