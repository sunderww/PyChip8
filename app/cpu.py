import logging
import random
from typing import Optional
from app.constants import DEFAULT_SPRITES, MEMORY_PROGRAM_START, MEMORY_SIZE, REGISTER_COUNT, SPRITE_BYTE_SIZE, STACK_SIZE
from app.engine.vector2 import Vector2
from app.renderer import Renderer
from app.keyboard import Keyboard
from app.speaker import Speaker

class CPUError(RuntimeError):
    pass

class StackOverflowError(CPUError):
    pass

class StackUnderflowError(CPUError):
    pass


class CPU:
    def __init__(self, cycles_per_frame: int, renderer: Renderer, keyboard: Keyboard, speaker: Speaker) -> None:
        self.renderer = renderer
        self.keyboard = keyboard
        self.speaker = speaker
        self.cycles_per_frame = cycles_per_frame

        self.memory: bytearray = bytearray(MEMORY_SIZE)
        self.registers = [0] * REGISTER_COUNT
        self.i = 0 # Special I register
        self.delay_timer = 0
        self.sound_timer = 0
        self.pc = MEMORY_PROGRAM_START # Program counter
        self.sp = 0 # Stack pointer
        self.stack = [0] * STACK_SIZE

        # Special case for OpCode 0xFx0A which requires waiting for input
        self.wait_for_key_reg: Optional[int] = None

        self._load_default_sprites()
    
    def _load_default_sprites(self) -> bytearray:
        for i, byte in enumerate(DEFAULT_SPRITES):
            self.memory[i] = byte

    def load_rom(self, rom_path: str) -> None:
        random.seed()
        with open(rom_path, 'rb') as f:
            for i, byte in enumerate(f.read()):
                self.memory[MEMORY_PROGRAM_START + i] = byte
        logging.info("CPU base memory after loading rom %s :" % rom_path)
        logging.info(self.memory)

    def update(self) -> None:
        # Special case for OpCode 0xFx0A which requires waiting for input
        if self.wait_for_key_reg is not None:
            if len(self.keyboard.pressed_keys) > 0:
                self.registers[self.wait_for_key_reg] = self.keyboard.pressed_keys[0]
                self.wait_for_key_reg = None
            else:
                return
        
        self.update_timers()
        self.handle_sound()
            
        for _ in range(self.cycles_per_frame):
            self.execute_cycle()
    
    def update_timers(self) -> None:
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
    
    def handle_sound(self) -> None:
        if self.sound_timer > 0:
            self.speaker.play()
        else:
            self.speaker.stop()
        
    def execute_cycle(self) -> None:
        opcode = int.from_bytes(self.memory[self.pc:self.pc+2], 'big', signed=False)
        self.pc += 2
        self.execute_opcode(opcode)

    def execute_opcode(self, opcode: int) -> None:
        lookup_table = {
            0x0: self.handle_clear_or_return_op,
            0x1: self.opcode_JMP,
            0x2: self.opcode_CALL,
            0x3: self.opcode_SE_byte,
            0x4: self.opcode_SNE_byte,
            0x5: self.opcode_SE_reg,
            0x6: self.opcode_LD_byte,
            0x7: self.opcode_ADD_byte,
            0x8: self.handle_math_op,
            0x9: self.opcode_SNE_reg,
            0xA: self.opcode_LDI,
            0xB: self.opcode_JMP_v0,
            0xC: self.opcode_RND,
            0xD: self.opcode_DRW,
            0xE: self.handle_key_op,
            0xF: self.handle_misc_op,
        }

        lookup_byte = (opcode & 0xF000) >> 12
        lookup_table[lookup_byte](opcode)
        
    
    def handle_clear_or_return_op(self, opcode: int) -> None:
        subop = opcode & 0xFF
        if subop == 0xE0:
            self.opcode_CLR(opcode)
        elif subop == 0xEE:
            self.opcode_RET(opcode)
        else:
            self.nop(opcode)

    def handle_math_op(self, opcode: int) -> None:
        lookup_table = {
            0x0: self.opcode_LD_reg,
            0x1: self.opcode_OR,
            0x2: self.opcode_AND,
            0x3: self.opcode_XOR,
            0x4: self.opcode_ADD_reg,
            0x5: self.opcode_SUB,
            0x6: self.opcode_SHR,
            0x7: self.opcode_SUBN,
            0xE: self.opcode_SHL,
        }

        lookup_byte = opcode & 0xF
        if lookup_byte in lookup_table.keys():
            lookup_table[lookup_byte](opcode)
        else:
            self.nop(opcode)

    def handle_key_op(self, opcode: int) -> None:
        subop = opcode & 0xFF
        if subop == 0x9E:
            self.opcode_SKP(opcode)
        elif subop == 0xA1:
            self.opcode_SKNP(opcode)
        else:
            self.nop(opcode)

    def handle_misc_op(self, opcode: int) -> None:
        lookup_table = {
            0x07: self.opcode_LD_dt_in_reg,
            0x0A: self.opcode_LD_key,
            0x15: self.opcode_LD_reg_in_dt,
            0x18: self.opcode_LD_reg_in_st,
            0x1E: self.opcode_ADD_i,
            0x29: self.opcode_LD_i_char_sprite,
            0x33: self.opcode_LD_bcd,
            0x55: self.opcode_LD_reg_to_mem,
            0x65: self.opcode_LD_mem_to_reg,
        }

        lookup_bytes = opcode & 0xFF
        if lookup_bytes in lookup_table.keys():
            lookup_table[lookup_bytes](opcode)
        else:
            self.nop(opcode)
            logging.warning("Ignoring unknown opcode %x" % opcode)
    

    @classmethod
    def get_all_opcodes(cls) -> list:
        return [f for f in dir(cls) if f.startswith('opcode_')]

    ###########################
    # Opcodes implementations #
    ###########################
    
    def nop(self, opcode: int) -> None:
        """ For debug purposes """
        if opcode != 0:
            logging.debug("Ignoring unknown opcode %x" % opcode)

    def opcode_CLR(self, _: int) -> None:
        """ 
            OpCode 00E0
            Clears the screen. 
        """
        self.renderer.clear_pixels()

    def opcode_RET(self, opcode: int) -> None:
        """ 
            OpCode 00EE
            Returns from a subroutine. 
        """
        if self.sp == 0:
            raise StackUnderflowError()
        
        self.sp -= 1
        address = self.stack[self.sp]
        self.stack[self.sp] = 0
        self.pc = address

    def opcode_JMP(self, opcode: int) -> None:
        """ 
            OpCode 1NNN
            Jump to location nnn. 
        """
        address = opcode & 0xFFF
        self.pc = address

    def opcode_CALL(self, opcode: int) -> None:
        """" 
            OpCode 2NNN
            Calls subroutine at NNN. 
        """
        if self.sp >= STACK_SIZE:
            raise StackOverflowError()

        address = (opcode & 0xFFF)
        self.stack[self.sp] = self.pc
        self.sp += 1
        self.pc = address

    def opcode_SE_byte(self, opcode: int) -> None:
        """ 
            OpCode 3XNN
            Skips the next instruction if VX equals NN. (Usually the next instruction is a jump to skip a code block)
        """
        reg = (opcode & 0xF00) >> 8
        byte = (opcode & 0xFF)
        if self.registers[reg] == byte:
            self.pc += 2

    def opcode_SNE_byte(self, opcode: int) -> None:
        """ 
            OpCode 4XNN
            Skips the next instruction if VX does not equal NN. (Usually the next instruction is a jump to skip a code block)
        """
        reg = (opcode & 0xF00) >> 8
        byte = (opcode & 0xFF)
        if self.registers[reg] != byte:
            self.pc += 2

    def opcode_SE_reg(self, opcode: int) -> None:
        """ 
            OpCode 5XY0
            Skips the next instruction if VX equals VY. (Usually the next instruction is a jump to skip a code block)
        """
        regx = (opcode & 0xF00) >> 8
        regy = (opcode & 0xF0) >> 4
        if self.registers[regx] == self.registers[regy]:
            self.pc += 2

    def opcode_LD_byte(self, opcode: int) -> None:
        """ 
            OpCode 6XNN
            Sets VX to NN. 
        """
        reg = (opcode & 0xF00) >> 8
        byte = (opcode & 0xFF)
        self.registers[reg] = byte

    def opcode_ADD_byte(self, opcode: int) -> None:
        """ 
            OpCode 7XNN
            Adds NN to VX. (Carry flag is not changed)
        """
        reg = (opcode & 0xF00) >> 8
        byte = (opcode & 0xFF)
        # Simulate overflow
        self.registers[reg] = (self.registers[reg] + byte) & 0xFF

    def opcode_LD_reg(self, opcode: int) -> None:
        """ 
            OpCode 8XY0
            Sets VX to the value of VY. 
        """
        regx = (opcode & 0xF00) >> 8
        regy = (opcode & 0xF0) >> 4
        self.registers[regx] = self.registers[regy]
    
    def opcode_OR(self, opcode: int) -> None:
        """ 
            OpCode 8XY1
            Sets VX to VX or VY. (Bitwise OR operation); 
        """
        regx = (opcode & 0xF00) >> 8
        regy = (opcode & 0xF0) >> 4
        self.registers[regx] |= self.registers[regy]
    
    def opcode_AND(self, opcode: int) -> None:
        """ 
            OpCode 8XY2
            Sets VX to VX and VY. (Bitwise AND operation); 
        """
        regx = (opcode & 0xF00) >> 8
        regy = (opcode & 0xF0) >> 4
        self.registers[regx] &= self.registers[regy]
    
    def opcode_XOR(self, opcode: int) -> None:
        """ 
            OpCode 8XY3
            Sets VX to VX xor VY.
        """
        regx = (opcode & 0xF00) >> 8
        regy = (opcode & 0xF0) >> 4
        self.registers[regx] ^= self.registers[regy]
    
    def opcode_ADD_reg(self, opcode: int) -> None:
        """ 
            OpCode 8XY4
            Adds VY to VX. VF is set to 1 when there's a carry, and to 0 when there is not. 
        """
        regx = (opcode & 0xF00) >> 8
        regy = (opcode & 0xF0) >> 4
        result_overflow = self.registers[regx] + self.registers[regy]
        result = result_overflow & 0xFF
        
        self.registers[0xF] = 1 if result != result_overflow else 0
        self.registers[regx] = result
    
    def opcode_SUB(self, opcode: int) -> None:
        """ 
            OpCode 8XY5
            VY is subtracted from VX. VF is set to 0 when there's a borrow, and 1 when there is not. 
        """
        regx = (opcode & 0xF00) >> 8
        regy = (opcode & 0xF0) >> 4

        self.registers[0xF] = self.registers[regx] > self.registers[regy]
        self.registers[regx] = (self.registers[regx] - self.registers[regy]) & 0xFF
    
    def opcode_SHR(self, opcode: int) -> None:
        """ 
            OpCode 8XY6
            Stores the least significant bit of VX in VF and then shifts VX to the right by 1.
            The VY register is not used
        """
        regx = (opcode & 0xF00) >> 8
        self.registers[0xF] = self.registers[regx] & 1
        self.registers[regx] >>= 1
    
    def opcode_SUBN(self, opcode: int) -> None:
        """ 
            OpCode 8XY7
            Sets VX to VY minus VX. VF is set to 0 when there's a borrow, and 1 when there is not. 
        """
        regx = (opcode & 0xF00) >> 8
        regy = (opcode & 0xF0) >> 4

        self.registers[0xF] = self.registers[regy] > self.registers[regx]
        self.registers[regx] = (self.registers[regy] - self.registers[regx]) & 0xFF
    
    def opcode_SHL(self, opcode: int) -> None:
        """ 
            OpCode 8XYE
            Stores the most significant bit of VX in VF and then shifts VX to the left by 1.
            The VY register is not used
        """
        regx = (opcode & 0xF00) >> 8
        self.registers[0xF] = self.registers[regx] & 0x80
        self.registers[regx] <<= 1


    def opcode_SNE_reg(self, opcode: int) -> None:
        """ 
            OpCode 9XY0
            Skips the next instruction if VX does not equal VY. (Usually the next instruction is a jump to skip a code block); 
        """
        regx = (opcode & 0xF00) >> 8
        regy = (opcode & 0xF0) >> 4
        if self.registers[regx] != self.registers[regy]:
            self.pc += 2

    def opcode_LDI(self, opcode: int) -> None:
        """ 
            OpCode ANNN
            Sets I to the address NNN. 
        """
        self.i = opcode & 0xFFF

    def opcode_JMP_v0(self, opcode: int) -> None:
        """ 
            OpCode BNNN
            Jumps to the address NNN plus V0. 
        """
        address = opcode & 0xFFF
        # Simulate overflow
        address = (address + self.registers[0]) & 0xFF
        self.pc = address

    def opcode_RND(self, opcode: int) -> None:
        """ 
            OpCode CXNN
            Sets VX to the result of a bitwise and operation on a random number (Typically: 0 to 255) and NN.
        """
        reg = (opcode & 0xF00) >> 8
        byte = (opcode & 0xFF)
        number = random.randint(0, 0xFF)
        self.registers[reg] = byte & number

    def opcode_DRW(self, opcode: int) -> None:
        """
            OpCode DXYN
            Draws a sprite at coordinate (VX, VY) that has a width of 8 pixels and a height of N pixels. 
            Each row of 8 pixels is read as bit-coded starting from memory location I; 
            I value does not change after the execution of this instruction. 
            As described above, VF is set to 1 if any screen pixels are flipped from set to unset when the sprite is drawn, 
            and to 0 if that does not happen
        """
        regx = (opcode & 0xF00) >> 8
        regy = (opcode & 0xF0) >> 4
        x = self.registers[regx]
        y = self.registers[regy]
        n = (opcode & 0xF)
        logging.info("Draw sprite (located at 0x%04x) at pos %d/%d" % (self.i, x, y))
        for i in range(0, n):
            row = self.memory[self.i + i]
            for j in range(1, 9):
                if (row >> (j-1)) & 0x1:
                    self.renderer.toggle_pixel(Vector2(x+8-j, y+i))
        self.renderer.render()

    def opcode_SKP(self, opcode: int) -> None:
        """ 
            OpCode EX9E
            Skips the next instruction if the key stored in VX is pressed. 
        """
        reg = (opcode & 0xF00) >> 8
        if self.keyboard.is_key_pressed(self.registers[reg]):
            self.pc += 2
    
    def opcode_SKNP(self, opcode: int) -> None:
        """ 
            OpCode EXA1 
            Skips the next instruction if the key stored in VX is not pressed.
        """
        reg = (opcode & 0xF00) >> 8
        if not self.keyboard.is_key_pressed(self.registers[reg]):
            self.pc += 2

    def opcode_LD_dt_in_reg(self, opcode: int) -> None:
        """ 
            OpCode FX07
            Sets VX to the value of the delay timer. 
        """
        reg = (opcode & 0xF00) >> 8
        self.registers[reg] = self.delay_timer
    
    def opcode_LD_key(self, opcode: int) -> None:
        """ 
            OpCode FX0A
            A key press is awaited, and then stored in VX. 
            (Blocking Operation. All instruction halted until next key event); 
        """
        self.wait_for_key_reg = (opcode & 0xF00) >> 8
    
    def opcode_LD_reg_in_dt(self, opcode: int) -> None:
        """ 
            OpCode FX15
            Sets the delay timer to VX. 
        """
        reg = (opcode & 0xF00) >> 8
        self.delay_timer = self.registers[reg]
    
    def opcode_LD_reg_in_st(self, opcode: int) -> None:
        """ 
            OpCode FX18
            Sets the sound timer to VX. 
        """
        reg = (opcode & 0xF00) >> 8
        self.sound_timer = self.registers[reg]

    def opcode_ADD_i(self, opcode: int) -> None:
        """ 
            OpCode FX1E
            Adds VX to I. VF is not affected
        """
        reg = (opcode & 0xF00) >> 8
        self.i += self.registers[reg]

    def opcode_LD_i_char_sprite(self, opcode: int) -> None:
        """ 
            OpCode FX29
            Sets I to the location of the sprite for the character in VX. 
            Characters 0-F (in hexadecimal) are represented by a 4x5 font. 
        """
        reg = (opcode & 0xF00) >> 8
        self.i = self.registers[reg] * SPRITE_BYTE_SIZE

    def opcode_LD_bcd(self, opcode: int) -> None:
        """ 
            OpCode FX33
            Stores the binary-coded decimal representation of VX, 
            with the most significant of three digits at the address in I, 
            the middle digit at I plus 1, and the least significant digit at I plus 2.

            (In other words, take the decimal representation of VX, 
            place the hundreds digit in memory at location in I, 
            the tens digit at location I+1, and the ones digit at location I+2.); 
        """
        reg = (opcode & 0xF00) >> 8
        value = self.registers[reg]
        self.memory[self.i] = int(value / 100) % 10
        self.memory[self.i+1] = int(value / 10) % 10
        self.memory[self.i+2] = value % 10

    def opcode_LD_reg_to_mem(self, opcode: int) -> None:
        """ 
            OpCode FX55
            Stores from V0 to VX (including VX) in memory, starting at address I. 
            The offset from I is increased by 1 for each value written, but I itself is left unmodified.
        """
        reg = (opcode & 0xF00) >> 8
        logging.debug("opcode_LD_reg_to_mem not implemented")

    def opcode_LD_mem_to_reg(self, opcode: int) -> None:
        """ 
            OpCode FX65
            Fills from V0 to VX (including VX) with values from memory, starting at address I. 
            The offset from I is increased by 1 for each value written, but I itself is left unmodified
        """
        reg = (opcode & 0xF00) >> 8
        logging.debug("opcode_LD_mem_to_reg not implemented")
