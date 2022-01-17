from time import sleep, time
from typing import Tuple
from app.constants import SCREEN_SIZE
from app.cpu import CPU
from app.engine.engine_handler import EngineHandler
from app.engine.pyglet_engine_handler import PygletEngineHandler
from app.keyboard import Keyboard
from app.renderer import Renderer

import logging

from app.speaker import Speaker


class Emulator:

    def __init__(self, 
        cpu_cycles_per_frame: int, 
        scale: int = 10, 
        color: Tuple[int, int, int] = (200, 40, 40), 
        sound: int = 440, 
        fps: int = 60) -> None:

        logging.basicConfig(level=logging.INFO)
        
        self.fps = fps
        self.engine: EngineHandler = PygletEngineHandler(size=SCREEN_SIZE * scale)
        
        renderer: Renderer = Renderer(self.engine, scale, color)
        keyboard: Keyboard = Keyboard(self.engine)
        speaker: Speaker = Speaker(self.engine, sound)

        self.cpu: CPU = CPU(cpu_cycles_per_frame, renderer, keyboard, speaker)


    def run_rom(self, rom_path: str) -> None:
        logging.info('Running rom %s' % rom_path)
        self.cpu.load_rom(rom_path)
        self.engine.start()
        self.main_loop()
    
    def main_loop(self) -> None:
        step = 1.0 / self.fps

        running = True
        while running:
            start = time()

            # Do logic
            running = self.engine.update()
            self.cpu.update()

            end = time()
            elapsed = end - start
            wait = step - elapsed
            if wait > 0:
                sleep(wait)
    
