import unittest

from app.engine.pyglet_engine_handler import PygletEngineHandler
from app.engine.vector2 import Vector2
from app.constants import SCREEN_SIZE

from app.renderer import Renderer

class TestRenderer(unittest.TestCase):

    def setUp(self) -> None:
        engine = PygletEngineHandler(size=Vector2(64, 32))
        self.renderer: Renderer = Renderer(engine, 10, (100, 100, 100))
    
    def tearDown(self) -> None:
        self.renderer = None
    
    def test_clear_pixels(self):
        self.renderer.pixels[Vector2(5, 5)] = True
        self.renderer.pixels[Vector2(30, 14)] = True
        self.renderer.clear_pixels()
        self.assertNotEqual(self.renderer.pixels.get(Vector2(5, 5)), True)
        self.assertNotEqual(self.renderer.pixels.get(Vector2(30, 14)), True)
        self.assertNotEqual(self.renderer.pixels.get(Vector2(5, 14)), True)

    def test_toggle_pixel(self):
        pos = Vector2(16, 15)
        self.renderer.toggle_pixel(pos)
        self.assertEqual(self.renderer.pixels[pos], True)

    def test_toggle_pixel_wrapping(self):
        pos = SCREEN_SIZE + Vector2(5, 6)
        self.renderer.toggle_pixel(pos)
        self.assertNotEqual(self.renderer.pixels.get(pos), True)
        self.assertEqual(self.renderer.pixels.get(Vector2(5, 6)), True)

        self.renderer.toggle_pixel(Vector2(-1, -1))
        self.assertNotEqual(self.renderer.pixels.get(Vector2(-1, -1)), True)
        self.assertEqual(self.renderer.pixels.get(SCREEN_SIZE - Vector2(1, 1)), True)
