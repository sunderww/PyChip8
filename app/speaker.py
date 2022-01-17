from app.engine.engine_handler import EngineHandler

class Speaker:
    def __init__(self, engine: EngineHandler, pitch: int) -> None:
        self.engine = engine
        self.pitch = 440 # Hz
    
    def play(self) -> None:
        self.engine.play_sound(self.pitch)
    
    def stop(self) -> None:
        self.engine.stop_sound()
