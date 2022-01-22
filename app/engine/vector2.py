from __future__ import annotations
from typing import overload

class Vector2:
    def __init__(self, x: int = 0, y: int = 0) -> None:
        self.x = x
        self.y = y

    def __mul__(self, other: Vector2 | int) -> Vector2:
        if isinstance(other, Vector2):
            return Vector2(self.x * other.x, self.y * other.y)
        elif isinstance(other, int):
            return Vector2(self.x * other, self.y * other)
        else:
            return None
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Vector2):
            return self.x == other.x and self.y == other.y
        return False
    
    def __str__(self) -> str:
        return "(%d/%d)" % (self.x, self.y)
    
    def __repr__(self) -> str:
        return "Vector2(%d, %d)" % (self.x, self.y)
