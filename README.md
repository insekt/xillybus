# Xillybus
Python lib to write and read date to/from FPGA registers over Xillybus Lite

Based on http://xillybus.com/xillybus-lite

Example:

```
#!/usr/bin/python3
import xillybus

bus=xillybus.Xillybus('/dev/uio0')
bus.read_byte(0x04)
print(hex(val))
```

Based on plmem utility