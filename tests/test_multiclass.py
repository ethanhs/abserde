import pytest

try:
    import multiclass
except ImportError as e:
    print("You must run the tests from the environment with all of the examples built.")
    raise e


def test_init():
    t = multiclass.Test(5, 2)
    assert t.room == 5
    assert t.floor == 2
    with pytest.raises(TypeError):
        tt = multiclass.Test('fail!', 5.5)
    t2 = multiclass.Test2(8.8, 30, t)
    assert t2.name == 8.8
    assert t2.age == 30
    assert t2.foo == t
    with pytest.raises(TypeError):
        tt2 = multiclass.Test2(6, 6, 6)


def test_loads():
    t = multiclass.Test.loads('{"room": 4, "floor": 10}')
    assert t.room == 4
    assert t.floor == 10
    with pytest.raises(multiclass.JSONParseError):
        tt = multiclass.Test.loads('{"invalid":')
    with pytest.raises(multiclass.JSONParseError):
        tt = multiclass.Test.loads('{"room": "invalid", "floor": 5}')
    t2 = multiclass.Test2.loads('{"age": 4, "name": "Will", "foo": {"room": 4, "floor": 10}}')
    assert t2.name == "Will"
    assert t2.age == 4
    assert t2.foo == t
    with pytest.raises(multiclass.JSONParseError):
        tt2 = multiclass.Test2.loads('{"age": 4, "name": 5, "foo": {"room": None, "floor": 10}}')


def test_dumps():
    t = multiclass.Test(5, 2)
    assert t.dumps() == '{"room":5,"floor":2}'
    t2 = multiclass.Test2(8.8, 30, t)
    assert t2.dumps() == '{"name":8.8,"age":30,"foo":{"room":5,"floor":2}}'


def test_access():
    t = multiclass.Test(5, 2)
    assert t['room'] == 5
    t['floor'] = 10
    assert t.floor == 10
    t.room = 100
    assert t['room'] == 100


def test_str():
    t = multiclass.Test(5, 2)
    assert(str(t) == t.dumps())


def test_any_mutation():
    t = multiclass.Test(5, 2)
    t2 = multiclass.Test2(8.8, 30, t)
    s = "I can be a string!"
    t2.name = s
    assert t2.name == s
    lst = [1, '']
    t2.name = lst
    assert t2.name == lst
