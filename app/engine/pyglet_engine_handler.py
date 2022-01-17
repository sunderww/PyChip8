
from typing import Tuple
import pyglet
import logging

from pyglet.media.player import Player

from app.engine.engine_handler import EngineHandler
from app.engine.vector2 import Vector2
from app.key import Key

def pyglet_to_pico8_key(symbol) -> Key:
    mapping = {
        pyglet.window.key.DOUBLEQUOTE: Key.ONE,
        None: Key.TWO,
        pyglet.window.key.AMPERSAND: Key.THREE,
        pyglet.window.key.APOSTROPHE: Key.C,

        pyglet.window.key.A: Key.FOUR,
        pyglet.window.key.Z: Key.FIVE,
        pyglet.window.key.E: Key.SIX,
        pyglet.window.key.R: Key.D,

        pyglet.window.key.Q: Key.SEVEN,
        pyglet.window.key.S: Key.EIGHT,
        pyglet.window.key.D: Key.NINE,
        pyglet.window.key.F: Key.E,

        pyglet.window.key.W: Key.A,
        pyglet.window.key.X: Key.ZERO,
        pyglet.window.key.C: Key.B,
        pyglet.window.key.V: Key.F,
    }

    if not symbol in mapping.keys():
        logging.info("Unkown symbol %s" % symbol)
    return mapping.get(symbol, Key.UNKNOWN)


class PygletEngineHandler(EngineHandler):
    def __init__(self, size: Vector2) -> None:
        super().__init__(size=size)

        self.window = pyglet.window.Window(self.size.x, self.size.y)
        self.batch = pyglet.graphics.Batch()
        self.sound_player: Player = Player()
        self.sound_player.loop = True
        self.shapes: list = []
        self.open: bool = True

        @self.window.event
        def on_key_press(symbol, _):
            key: Key = pyglet_to_pico8_key(symbol)
            if key != Key.UNKNOWN:
                self._handle_key_press(key)
        
        @self.window.event
        def on_key_release(symbol, _):
            key: Key = pyglet_to_pico8_key(symbol)
            if key != Key.UNKNOWN:
                self._handle_key_press(key, down=False)
        
        @self.window.event
        def on_close():
            self.open = False
    
    def start(self) -> None:
        # pyglet.app.run()
        logging.info("Pyglet application started")
    
    def clear_window(self) -> None:
        logging.debug("Clearing window")
        self.window.clear()
        self.batch = pyglet.graphics.Batch()
        self.shapes = []
    
    def draw_rect(self, pos: Vector2, size: Vector2, color: Tuple[int, int, int]) -> None:
        self.shapes.append(pyglet.shapes.Rectangle(pos.x, pos.y, size.x, size.y, color, self.batch))

    def draw(self) -> None:
        logging.debug("Drawing shapes")
        self.batch.draw()

    def play_sound(self, frequency: int) -> None:
        """ Plays a square wave of a given frequency indefinitely """
        sound = pyglet.media.synthesis.Square(-1, frequency)
        if not self.sound_player.playing:
            self.sound_player.queue(sound)
            self.sound_player.play()
    
    def stop_sound(self) -> None:
        self.sound_player.next_source()
        self.sound_player.pause()
    
    def update(self) -> bool:
        if not self.open:
            return False

        pyglet.clock.tick()

        for window in pyglet.app.windows:
            window.switch_to()
            window.dispatch_events()
            window.flip()
        
        return True

