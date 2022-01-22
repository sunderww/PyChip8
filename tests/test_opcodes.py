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

    def test_CLR(self):
        self.cpu.renderer.clear_pixels = Mock()
        self.cpu.opcode_CLR(0x00E0)
        self.cpu.renderer.clear_pixels.assert_called_once()

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
    
    def test_SE_byte(self):
        self.cpu._increment_pc = Mock(wraps=self.cpu._increment_pc)
        self.cpu.registers[0] = 0x33
        self.cpu.registers[0xB] = 0x12
        self.cpu.pc = 0
        self.cpu.opcode_SE_byte(0x3033)
        self.assertEqual(self.cpu.pc, self.cpu.PC_INCREMENT_SIZE, "CPU didn't skip next instruction with equal values")
        self.cpu.pc = 0
        self.cpu.opcode_SE_byte(0x3BAB)
        self.assertEqual(self.cpu.pc, 0, "CPU skipped next instruction with non-equal values")
        self.cpu._increment_pc.assert_called_once()
    
    def test_SNE_byte(self):
        self.cpu._increment_pc = Mock(wraps=self.cpu._increment_pc)
        self.cpu.registers[3] = 0xAB
        self.cpu.registers[4] = 0x44
        self.cpu.pc = 0
        self.cpu.opcode_SE_byte(0x4333)
        self.assertEqual(self.cpu.pc, 0, "CPU skipped next instruction with equal values")
        self.cpu.pc = 0
        self.cpu.opcode_SE_byte(0x4444)
        self.assertEqual(self.cpu.pc, self.cpu.PC_INCREMENT_SIZE, "CPU didn't skip next instruction with non-equal values")
        self.cpu._increment_pc.assert_called_once()
    
    def test_SE_reg(self):
        self.cpu._increment_pc = Mock(wraps=self.cpu._increment_pc)
        self.cpu.registers[0x9] = 0x99
        self.cpu.registers[0xE] = 0x99
        self.cpu.registers[0xF] = 0xA0
        self.cpu.pc = 0
        self.cpu.opcode_SE_reg(0x59E0)
        self.assertEqual(self.cpu.pc, self.cpu.PC_INCREMENT_SIZE, "CPU didn't skip next inscrutions with equal values")
        self.cpu.pc = 0
        self.cpu.opcode_SE_reg(0x5F90)
        self.assertEqual(self.cpu.pc, 0, "CPU skipped next instruction with non-equal values")
        self.cpu._increment_pc.assert_called_once()
    
    def test_LD_byte(self):
        self.cpu.opcode_LD_byte(0x629B)
        self.assertEqual(self.cpu.registers[2], 0x9B)
    
    def test_ADD_byte(self):
        """ Should also check that overflow happens correctly and that carry flag is not set """
        self.cpu.registers[0x7] = 0x20
        self.cpu.registers[0xA] = 0xFF
        self.cpu.opcode_ADD_byte(0x7710)
        self.assertEqual(self.cpu.registers[0x7], 0x30)
        self.assertEqual(self.cpu.registers[0xF], 0, "Carry flag should never be set")
        self.cpu.opcode_ADD_byte(0x7A02)
        self.assertEqual(self.cpu.registers[0xA], 1)
        self.assertEqual(self.cpu.registers[0xF], 0, "Carry flag should never be set")
    
    def test_LD_reg(self):
        self.cpu.registers[0x1] = 0x81
        self.cpu.registers[0xC] = 0xC0
        self.cpu.opcode_LD_reg(0x81C0)
        self.assertEqual(self.cpu.registers[1], 0xC0)
        self.assertEqual(self.cpu.registers[0xC], 0xC0, "Register 0xC should not have changed")
    
    def test_OR(self):
        self.cpu.registers[0x2] = 0b101010
        self.cpu.registers[0x4] = 0b111010
        self.cpu.opcode_OR(0x8241)
        self.assertEqual(self.cpu.registers[0x2], 0b111010)
        self.assertEqual(self.cpu.registers[0x4], 0b111010, "Register 0x4 should not have changed")
    
    def test_AND(self):
        self.cpu.registers[0x6] = 0b101010
        self.cpu.registers[0x7] = 0b111001
        self.cpu.opcode_AND(0x8672)
        self.assertEqual(self.cpu.registers[0x6], 0b101000)
        self.assertEqual(self.cpu.registers[0x7], 0b111001, "Register 0x7 should not have changed")

    def test_XOR(self):
        self.cpu.registers[0x9] = 0b10101011
        self.cpu.registers[0xB] = 0b01100101
        self.cpu.opcode_XOR(0x89B3)
        self.assertEqual(self.cpu.registers[0x9], 0b11001110)
        self.assertEqual(self.cpu.registers[0xB], 0b01100101, "Register 0xB should not have changed")
        self.cpu.opcode_XOR(0x8BB3)
        self.assertEqual(self.cpu.registers[0xB], 0)

    def test_ADD_reg(self):
        """ Also check that the carry flag is set correctly EACH TIME ADD_reg is called. """
        self.cpu.registers[0xE] = 0xE6
        self.cpu.registers[0xC] = 0x20
        self.cpu.opcode_ADD_reg(0x8EC4)
        self.assertEqual(self.cpu.registers[0xE], 6)
        self.assertEqual(self.cpu.registers[0xF], 1, "Carry flag should have been set")
        self.cpu.opcode_ADD_reg(0x8CC4)
        self.assertEqual(self.cpu.registers[0xC], 0x40)
        self.assertEqual(self.cpu.registers[0xF], 0, "Carry flag should not have been set")
    
    def test_SUB(self):
        """ Also check that the carry flag is set correctly EACH TIME SUB is called. """
        self.cpu.registers[0xD] = 0xA0
        self.cpu.registers[0x1] = 0xAA
        self.cpu.opcode_SUB(0x81D5)
        self.assertEqual(self.cpu.registers[1], 0xA)
        self.assertEqual(self.cpu.registers[0xF], 0, "Carry flag should not have been set")
        self.cpu.registers[0x1] = 0xAA
        self.cpu.opcode_SUB(0x8D15)
        self.assertEqual(self.cpu.registers[0xD], 0xFF - (0xA-1))
        self.assertEqual(self.cpu.registers[0xF], 1, "Carry flag should have been set")
        self.cpu.opcode_SUB(0x8DD5)
        self.assertEqual(self.cpu.registers[0xD], 0)
        self.assertEqual(self.cpu.registers[0xF], 0, "Carry flag should not have been set")
    
    def test_SHR(self):
        self.cpu.registers[0xA] = 0b110101
        self.cpu.registers[0x2] = 0x22
        self.cpu.opcode_SHR(0x8A26)
        self.assertEqual(self.cpu.registers[0xA], 0b11010)
        self.assertEqual(self.cpu.registers[0xF], 1)
        self.assertEqual(self.cpu.registers[0x2], 0x22, "Register Y should not be touched in this operation")
        self.cpu.opcode_SHR(0x8A26)
        self.assertEqual(self.cpu.registers[0xA], 0b1101)
        self.assertEqual(self.cpu.registers[0xF], 0)


if __name__ == '__main__':
    unittest.main()
