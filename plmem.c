#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <string.h>

#define DEV_FILENAME "/dev/uio0"
#define MMAP_SIZE 0x1000
#define STRING_BLOCK_SIZE 0x7  // 7 bytes

static int parse_value(const char *val) {
  char *endptr;
  int result = (int)strtol(val, &endptr, 0);
  if (endptr[0] != '\0') return -1;
  return result;
}

// bit format
static int read_bit(const void *addr, int bit) {
  unsigned int val = ((const unsigned int*)addr)[0];
  printf("%d\n", (val >> bit) & 1);
  return 0;
}

static int write_bit(void *addr, int bit, int val) {
  if (val) {
    // set bit
    ((unsigned int*)addr)[0] |= 1 << bit;
  } else {
    // unset bit
    ((unsigned int*)addr)[0] &= ~(1 << bit);
  }
  return 0;
}

// byte format
static int read_byte(const void *addr) {
  printf("0x%02x\n", ((const unsigned char*)addr)[0]);
  return 0;
}

static int write_byte(void *addr, int val) {
  *((unsigned char*)addr) = (unsigned char)val;
  return 0;
}

// int16 format
static int read_int16(const void *addr) {
  printf("0x%08x\n", ((const uint16_t*)addr)[0]);
  return 0;
}

static int write_int16(void *addr, int val) {
  *((uint16_t*)addr) = (uint16_t)val;
  return 0;
}

// int32 format
static int read_int32(const void *addr) {
  printf("0x%08x\n", ((const unsigned int*)addr)[0]);
  return 0;
}

static int write_int32(void *addr, int val) {
  *((unsigned int*)addr) = (unsigned int)val;
  return 0;
}

// string format
static int read_string(const void *addr, int length) {
  int i;
  const unsigned char *addr2 = (const unsigned char *)addr;
  char *buf = (char *)malloc(2*length + 1);
  buf[length] = '\0';
  for (i = 0; i < length; ++i) {
    sprintf(buf + 2*i, "%02x", addr2[i]);
  }
  printf("%s\n", buf);
  free(buf);
  return 0;
}

static int write_string(void *addr, const char* str) {
  int i, val, result, ret;
  unsigned char *buf;
  int buf_size;
  int length = strlen(str);
  if (!length) return 0;  // success
  if (length % 2) {
    printf("Invalid string\n");
    return -1;
  }
  if ((str[0] == '0') && (str[1] == 'x')) {
    // skip 0x
    str += 2;
    length -= 2;
  }
  buf_size = length/2;
  buf = (unsigned char*)malloc(buf_size);
  result = 0;
  for (i = 0; i < length; i += 2) {
    ret = sscanf(str + i, "%2x", &val);
    if (ret == 0) {
      printf("Invalid string value at index %d: %2s\n", i, str + i);
      result = -1;
      break;
    }
    buf[i/2] = val;
  }
  if (!result) { // copy on success
#ifdef STRING_BLOCKS
    // copy string by blocks
    unsigned char *addr_ptr = (unsigned char*)addr;
    unsigned char *buf_ptr = (unsigned char*)buf;
    while (buf_size > 0) {
      memcpy(addr_ptr,
             buf_ptr,
             buf_size > STRING_BLOCK_SIZE ? STRING_BLOCK_SIZE : buf_size);
      addr_ptr += STRING_BLOCK_SIZE;
      buf_ptr += STRING_BLOCK_SIZE;
      buf_size -= STRING_BLOCK_SIZE;
    }
#else
    memcpy(addr, buf, buf_size);
#endif  // STRING_BLOCKS
  }
  free((void *)buf);
  return result;
}

// binary format
static int read_binary(const void *addr, int offset, int length) {
  const int block_size = sizeof(unsigned char) * 8;  // 8-bit blocks
  int i, idx, bit;
  unsigned char val;
  char *buf = (char *)malloc(length + 1);
  buf[length] = '\0';
  int block_offset = length%block_size;
  for (i = 0; i < length; ++i) {
    idx = (offset + i) / block_size;
    if (block_offset == 0) block_offset = block_size;
      bit = block_offset + offset - (i + 1 - idx * block_size);
    val = ((const unsigned char*)addr)[idx];
    buf[i] = ((val >> bit) & 1) ? '1' : '0';
  }
  printf("%s\n", buf);
  free((void *)buf);
  return 0;
}

static int write_binary(void *addr, int offset, const char* str) {
  const int block_size = sizeof(unsigned char) * 8;  // 8-bit blocks
  int i, idx, bit;
  int length = strlen(str);
  if (!length) return 0;  // success
  // check bit string
  for (i = 0; i < length; ++i) {
    if ((str[i] != '0') && (str[i] != '1')) return -1;
  }
  for (i = 0; i < length; ++i) {
    idx = (offset + i) / block_size;
    int block_offset = length%block_size;
    if (block_offset == 0) block_offset = block_size;
      bit = block_offset + offset - (i + 1 - idx * block_size);
    if (str[i] != '0') {
      // set bit
      ((unsigned char*)addr)[idx] |= 1 << bit;
    } else {
      // unset bit
      ((unsigned char*)addr)[idx] &= ~(1 << bit);
    }
  }
  return 0;
}

static void usage(const char *progname) {
  printf("Usage:\n"
         "  plmem get address { bit num | byte | int16 | int32 | string length | binary offset length }\n"
         "  plmem set address { bit num | byte | int16 | int32 | string | binary offset } value\n"
         "\n"
         "Version 0.6 21.12.2014\n");
}

int main (int argc, char* argv[]) {
  int fd;
  void *map_addr;
  volatile unsigned char *mapped;
  void *target_addr;
  int val;
  int result;

  if (argc < 4) {
    printf("Too few arguments\n");
    usage(argv[0]);
    return 1;
  }

  enum {CMD_GET, CMD_SET} cmd;

  val = 0;
  if (!strcmp(argv[1], "get")) {
    cmd = CMD_GET;
  } else if (!strcmp(argv[1], "set")) {
    cmd = CMD_SET;
    if (argc < 5) {
      printf("Missing value for set command\n");
      usage(argv[0]);
      return 1;
    }
    val = parse_value(argv[4]);
  } else {
    printf("Invalid command: %s\n", argv[1]);
    usage(argv[0]);
    return 1;
  }

  int offset = parse_value(argv[2]);
  if (offset < 0) {
    printf("Invalid address: %s\n", argv[2]);
    return 2;
  }

  fd = open(DEV_FILENAME, O_RDWR);
  if (fd < 0) {
    perror("Failed to open devfile");
    return 1;
  }

  map_addr = mmap(NULL, MMAP_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
  if (map_addr == MAP_FAILED) {
    perror("Failed to mmap");
    close(fd);
    return 1;
  }

  mapped = map_addr;
  target_addr = (void *)(mapped + offset);

  result = -1;
  if (!strcmp(argv[3], "bit")) {
    int bit_num = (argc > 4) ? parse_value(argv[4]) : 0;
    if ((bit_num >= 0) && (bit_num < 32)) {
      if (cmd == CMD_GET) {
        result = read_bit(target_addr, bit_num);
      } else {  // CMD_SET
        val = (argc > 5) ? parse_value(argv[5]) : 0;
        if ((val == 0) || (val == 1)) {
          result = write_bit(target_addr, bit_num, val);
        } else {
          printf("Invalid bit value\n");
        }
      }
    } else if (bit_num < 0) {
      printf("Invalid bit number: %s\n", argv[4]);
    } else {
      printf("Bit number %d not in range [0; 31]\n", bit_num);
    }
  } else if (!strcmp(argv[3], "byte")) {
    if (cmd == CMD_GET) {
      result = read_byte(target_addr);
    } else {  // CMD_SET
      result = write_byte(target_addr, val);
    }
  } else if (!strcmp(argv[3], "int16")) {
    if (cmd == CMD_GET) {
      result = read_int16(target_addr);
    } else {  // CMD_SET
      result = write_int16(target_addr, val);
    }
  } else if (!strcmp(argv[3], "int32")) {
    if (cmd == CMD_GET) {
      result = read_int32(target_addr);
    } else {  // CMD_SET
      result = write_int32(target_addr, val);
    }
  } else if (!strcmp(argv[3], "string")) {
    if (cmd == CMD_GET) {
      int length = (argc > 4) ? parse_value(argv[4]) : 0;
      if (length > 0) {
        result = read_string(target_addr, length);
      } else {
        printf("Wrong string length value\n");
      }
    } else {  // CMD_SET
      result = write_string(target_addr, argv[4]);
    }
  } else if (!strcmp(argv[3], "binary")) {
    int bit_offset = (argc > 4) ? parse_value(argv[4]) : 0;
    if (cmd == CMD_GET) {
      int length = (argc > 5) ? parse_value(argv[5]) : 0;
      if (length > 0) {
        result = read_binary(target_addr, bit_offset, length);
      } else {
        printf("Wrong binary length value\n");
      }
    } else {  // CMD_SET
      if (argc > 5) {
        result = write_binary(target_addr, bit_offset, argv[5]);
      } else {
        printf("Missing binary value\n");
      }
    }
  }

  munmap(map_addr, MMAP_SIZE);
  close(fd);
  return result;
}
