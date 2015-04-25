# plmem
Utility to write and read date to/from FPGA registers over Xillybus Lite

Based on http://xillybus.com/xillybus-lite

Example:

```
#!/usr/bin/python 3
import plmem

if __name__ == '__main__':
	x=plmem.Xillybus(/dev/uio0)
	val=x.read_byte(0x04)
	print(hex(val))
```