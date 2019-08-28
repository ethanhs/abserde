from abserde import abserde
from typing import List

@abserde
class Nested:
    attr: List[List[str]]
