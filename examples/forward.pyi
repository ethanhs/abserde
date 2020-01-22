from abserde import abserde

@abserde
class Example:
    a: int
    b: Test

@abserde
class Test:
    c: str
