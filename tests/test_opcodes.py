import unittest
from unittest.mock import MagicMock, Mock

from app.cpu import CPU
from app.engine.pyglet_engine_handler import PygletEngineHandler
from app.engine.vector2 import Vector2
from app.keyboard import Keyboard

from app.renderer import Renderer
from app.speaker import Speaker

class TestCPUOpcodes(unittest.TestCase):

    def setUp(self) -> None:
        engine = PygletEngineHandler(size=Vector2(64, 32))
        renderer: Renderer = Renderer(engine, 10, (100, 100, 100))
        keyboard: Keyboard = Keyboard(engine)
        speaker: Speaker = Speaker(engine, 440)
        self.cpu: CPU = CPU(1, renderer, keyboard, speaker)
    
    def tearDown(self) -> None:
        self.cpu = None
    
    def test_execute_opcode_with_invalid_opcode(self):
        invalid_opcodes = [0x0000, 0x00EF, 0x8FFA, 0x867F, 0xE19F, 0xEFA2, 0xE000, 0xF808, 0xFA1A, 0xF444, 0xF0E3]
        self.cpu.nop = MagicMock()
        for opcode in invalid_opcodes:
            self.cpu.execute_opcode(opcode)
            self.cpu.nop.assert_called_with(opcode)

    def test_function_call(self):
        """ Should test that opcodes are calling the correct functions """
        for func_name in self.cpu.get_all_opcodes():
            setattr(self.cpu, func_name, MagicMock(name=func_name))
        
        calls = {
            0x00E0: self.cpu.opcode_CLR,
            0x00EE: self.cpu.opcode_RET,
            0x1FF0: self.cpu.opcode_JMP,
            0x2ABC: self.cpu.opcode_CALL,
            0x3123: self.cpu.opcode_SE_byte,
            0x4FFE: self.cpu.opcode_SNE_byte,
            0x5555: self.cpu.opcode_SE_reg,
            0x6C01: self.cpu.opcode_LD_byte,
            0x789A: self.cpu.opcode_ADD_byte,
            0x8120: self.cpu.opcode_LD_reg,
            0x8341: self.cpu.opcode_OR,
            0x8562: self.cpu.opcode_AND,
            0x8783: self.cpu.opcode_XOR,
            0x89A4: self.cpu.opcode_ADD_reg,
            0x8BC5: self.cpu.opcode_SUB,
            0x8DE6: self.cpu.opcode_SHR,
            0x8F07: self.cpu.opcode_SUBN,
            0x8E1E: self.cpu.opcode_SHL,
            0x9D20: self.cpu.opcode_SNE_reg,
            0xAC38: self.cpu.opcode_LDI,
            0xB8B4: self.cpu.opcode_JMP_v0,
            0xC58A: self.cpu.opcode_RND,
            0xD000: self.cpu.opcode_DRW,
            0xEF9E: self.cpu.opcode_SKP,
            0xE0A1: self.cpu.opcode_SKNP,
            0xF107: self.cpu.opcode_LD_dt_in_reg,
            0xF20A: self.cpu.opcode_LD_key,
            0xF315: self.cpu.opcode_LD_reg_in_dt,
            0xF418: self.cpu.opcode_LD_reg_in_st,
            0xF51E: self.cpu.opcode_ADD_i,
            0xF629: self.cpu.opcode_LD_i_char_sprite,
            0xF733: self.cpu.opcode_LD_bcd,
            0xF855: self.cpu.opcode_LD_reg_to_mem,
            0xF965: self.cpu.opcode_LD_mem_to_reg,
        }

        for opcode, m in calls.items():
            mock: Mock = m
            self.cpu.execute_opcode(opcode)
            mock.assert_called_once_with(opcode)

    ###################
    # Testing Opcodes #
    ###################

    def test_JMP(self):
        self.cpu.opcode_JMP(0x1234)
        self.assertEqual(self.cpu.pc, 0x234)
        self.cpu.opcode_JMP(0x1FF0)
        self.assertEqual(self.cpu.pc, 0xFF0)
    
    def test_CALL(self):
        self.cpu.opcode_CALL(0x2FFF)
        self.assertEqual(self.cpu.pc, 0xFFF)
        self.assertEqual(self.cpu.sp, 1)
        self.cpu.opcode_CALL(0x2345)
        self.assertEqual(self.cpu.pc, 0x345)
        self.assertEqual(self.cpu.sp, 2)
    
    def test_RET(self):
        """ Expects opcode CALL to function correctly """
        self.cpu.pc = 0x800
        self.cpu.opcode_CALL(0x25A5)
        self.cpu.opcode_CALL(0x2EEE)
        self.cpu.opcode_RET(0x00EE)
        self.assertEqual(self.cpu.pc, 0x5A5)
        self.assertEqual(self.cpu.sp, 1)
        self.cpu.opcode_RET(0x00EE)
        self.assertEqual(self.cpu.pc, 0x800)
        self.assertEqual(self.cpu.sp, 0)

if __name__ == '__main__':
    unittest.main()
