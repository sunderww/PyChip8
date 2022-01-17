#! python3

import sys

from app.emulator import Emulator

def run_emulation(path: str, cpu_cycles_per_frame: int) -> None:
    emulator: Emulator = Emulator(cpu_cycles_per_frame)
    try:
        emulator.run_rom(path)
    except OSError:
        print("Can't open file %s" % path, file=sys.stderr)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_emulation(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 10)
    else:
        print("Usage: %s <rom_path> [cpu_cycles_per_frame]" % sys.argv[0])

