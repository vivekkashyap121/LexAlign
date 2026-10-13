from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    token_type: str
    value: str
    start: int
    end: int
    line: int
    column: int
