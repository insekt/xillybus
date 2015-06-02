import mmap

MMAP_SIZE = 0x1000

class Xillybus():

    def __init__(self, dev=''):
        fdev = open(dev, 'r+b')
        self.xmap = mmap.mmap(
            fdev.fileno(), MMAP_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, 0)

    def write_bit(self, ptr, bit, value):
        self.xmap.seek(ptr)
        byte = self.xmap.read_byte()
        if value == 0:
            byte &= ~(1 << bit)
        elif value == 1:
            byte |= 1 << bit
        self.xmap.seek(ptr)
        self.xmap.write_byte(byte)

    def read_bit(self, ptr, bit):
        self.xmap.seek(ptr)
        return self.xmap.read_byte() >> bit & 0x01

    def write_bin(self, ptr, offset, value):
        self.xmap.seek(ptr)
        byte = self.xmap.read_byte()
        for i, digit in enumerate(value[::-1]): # For each bit in value
            if digit == '0':
                byte &= ~(1 << (offset + i))
            elif digit == '1':
                byte |= 1 << (offset + i)
        self.xmap.seek(ptr)
        self.xmap.write_byte(byte)

    def read_bin(self, ptr, offset, length):
        self.xmap.seek(ptr)
        return self.xmap.read_byte() >> offset & (0xFF >> (8 - length))

    def write_byte(self, ptr, value):
        self.xmap.seek(ptr)
        self.xmap.write_byte(value)

    def read_byte(self, ptr):
        self.xmap.seek(ptr)
        return self.xmap.read_byte()

    def write_int16(self, ptr, value):
        self.xmap.seek(ptr)
        self.xmap.write_byte(value & 0xFF)
        self.xmap.write_byte(value >> 8 & 0xFF)

    def read_int16(self, ptr):
        self.xmap.seek(ptr)
        value = self.xmap.read_byte()
        value += self.xmap.read_byte() << 8
        return value

    def write_int32(self, ptr, value):
        self.xmap.seek(ptr)
        self.xmap.write_byte(value & 0xFF)
        self.xmap.write_byte(value >> 8 & 0xFF)
        self.xmap.write_byte(value >> 16 & 0xFF)
        self.xmap.write_byte(value >> 24 & 0xFF)

    def read_int32(self, ptr):
        self.xmap.seek(ptr)
        value = self.xmap.read_byte()
        value += self.xmap.read_byte() << 8
        value += self.xmap.read_byte() << 16
        value += self.xmap.read_byte() << 24
        return value
   
    def write_str(self, ptr, value):
        self.xmap.seek(ptr)
        self.xmap.write_byte(value & 0xFF)
        for i in range(1, round(len('{0:x}'.format(value)) / 2 + 0.5)):
            self.xmap.write_byte(value >> (i * 8) & 0xFF)

    def read_str(self, ptr, length):
        self.xmap.seek(ptr)
        value = self.xmap.read_byte()
        for i in range(1, length):
            value += self.xmap.read_byte() << (i * 8)
        return value
