from dataclasses import dataclass

@dataclass
class Config:
    filename: str
    debug: bool
    name: str
    email: str
