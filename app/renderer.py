import logging
from typing import Mapping, Tuple
from app.constants import SCREEN_SIZE
from app.engine.engine_handler import EngineHandler
from app.engine.vector2 import Vector2

class Renderer():
    def __init__(self, engine: EngineHandler, scale: int, color: Tuple[int, int, int]) -> None:
        self.engine = engine
        self.scale = Vector2(scale, scale)
        self.color = color

        self.pixels: Mapping[Vector2, bool] = {}
        self.clear_pixels()
    
    def clear_pixels(self) -> None:
        for x in range(SCREEN_SIZE.x):
            for y in range(SCREEN_SIZE.y):
                self.pixels[Vector2(x, y)] = False
        self.engine.clear_window()
    
    def toggle_pixel(self, pos: Vector2) -> bool:
        """ 
            toggle pixel at position pos.
            Note that if pos is not contained in SCREEN_SIZE, this method will wrap it inside
            return True if pixel at pos was erased
        """
        logging.debug("toggle pixel at pos %s" % pos)
        wrapped_pos = Vector2(pos.x % SCREEN_SIZE.x, pos.y % SCREEN_SIZE.y)
        self.pixels[wrapped_pos] = not self.pixels.get(wrapped_pos, False)
        return not self.pixels[wrapped_pos]
    
    def render(self) -> None:
        logging.debug("render()")
        self.engine.clear_window()
        for pos, value in self.pixels.items():
            if value:
                self.engine.draw_rect(pos * self.scale, self.scale, self.color)
        self.engine.draw()
        
