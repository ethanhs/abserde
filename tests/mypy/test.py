from forward import Example, Test

e = Example(1, Test("hi!"))
reveal_type(e.a)
reveal_type(e.dumps())
reveal_type(e.loads)