__version__ = '0.1.0'

from typing import Type, TypeVar

T = TypeVar('T')

def abserde(c: Type[T]) -> Type[T]:
    return c