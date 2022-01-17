from typing import Mapping
from app.engine.engine_handler import EngineHandler
from app.key import Key
import logging

class Keyboard:
    def __init__(self, engine: EngineHandler) -> None:
        self.engine = engine
        self.pressed_keys: Mapping[Key, bool] = {}
    
        @self.engine.keydown
        def _handle_keydown(key: Key) -> None:
            self._on_key_pressed(key)

        @self.engine.keyup
        def _handle_keyup(key: Key) -> None:
            self._on_key_pressed(key, False)
        
        
    def _on_key_pressed(self, key: Key, down: bool = True) -> None:
        logging.debug("%s pressed" % key)
        self.pressed_keys[key] = down
    
    def is_key_pressed(self, key: Key) -> bool:
        return self.pressed_keys.get(key, False)
