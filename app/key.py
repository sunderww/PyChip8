from abc import ABC, abstractclassmethod
from enum import Enum
from typing import Callable

class Key(Enum):
    UNKNOWN = -1

    ZERO = 0x0
    ONE = 0x1
    TWO = 0x2
    THREE = 0x3
    FOUR = 0x4
    FIVE = 0x5
    SIX = 0x6
    SEVEN = 0x7
    EIGHT = 0x8
    NINE = 0x9
    A = 0xA
    B = 0xB
    C = 0xC
    D = 0xD
    E = 0xE
    F = 0xF

KeyMapper = Callable[[any], Key]
