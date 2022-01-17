from abc import ABC, abstractmethod
from typing import Callable, Tuple
from app.engine.vector2 import Vector2
from app.key import Key

KeyPressedFunc = Callable[[Key], None]

class EngineHandler(ABC):
    def __init__(self, size: Vector2) -> None:
        self.size = size
        self.keydown_callbacks: list[KeyPressedFunc] = []
        self.keyup_callbacks: list[KeyPressedFunc] = []

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def clear_window(self) -> None:
        pass
    
    @abstractmethod
    def draw_rect(self, pos: Vector2, size: Vector2, color: Tuple[int, int, int]) -> None:
        pass

    @abstractmethod
    def draw(self) -> None:
        pass

    @abstractmethod
    def play_sound(self, frequency: int) -> None:
        pass
    
    @abstractmethod
    def stop_sound(self) -> None:
        pass
    
    @abstractmethod
    def update(self) -> bool:
        """ Return false in order to quit """
        pass

    def keyup(self, func: KeyPressedFunc) -> KeyPressedFunc:
        self.keyup_callbacks.append(func)
        return func
    
    def keydown(self, func: KeyPressedFunc) -> KeyPressedFunc:
        self.keydown_callbacks.append(func)
        return func
    
    def _handle_key_press(self, key: Key, down: bool = True) -> None:
        for callback in (self.keydown_callbacks if down else self.keyup_callbacks):
            callback(key)
