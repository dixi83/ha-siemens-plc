import os
import platform


def get_lib_location() -> str:
    machine = platform.machine()
    system = platform.system()
    pwd = os.path.dirname(os.path.abspath(__file__))

    if system == "Linux" and machine == "x86_64":  # 32/64 bit linux
        return f"{pwd}/lib/linux_x86_64/libsnap7.so"
    if system == "Darwin":  # Mac OS
        return f"{pwd}/lib/macosx_universal/libsnap7.dylib"
    if system == "Windows" and machine == "AMD64":  # 64 bit Windows
        return f"{pwd}/lib/win_amd64/libsnap7.dll"
    if system == "Linux" and machine == "aarch64":  # e.g. 64bit Raspberry Pi
        return f"{pwd}/lib/linux_aarch64/libsnap7.so"
    if system == "Linux" and machine == "armv7l":  # e.g. 32bit Raspberry Pi
        return f"{pwd}/lib/linux_armv7l/libsnap7.so"