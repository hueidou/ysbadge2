#pragma once
// LZ77 压缩：与 epd_send.py 的 compress() 位级兼容（窗口 1024B、偏移 10bit、长度 Golomb m=3）。
// 设备侧解压器只认这个格式，任何改动都要用 _verify 的 host 测试对 Python decompress() 做往返验证。
#include <stdint.h>

// 取第 pos 个原始字节（0 <= pos < total）。实现可利用缓存，但必须支持向前 1024 字节内的随时访问。
typedef uint8_t (*lz77_src_fn)(uint32_t pos, void *ctx);

struct Lz77Result {
  uint32_t bits;    // 压缩后比特数，写进 PIC_INFO
  int32_t  bytes;   // 实际写入 out 的字节数
  bool     overflow;// 输出缓冲不够 / 超出设备上限
};

// out 需先清零（本函数只置 1 位，不清 0）。
Lz77Result lz77_compress(uint32_t total, lz77_src_fn src, void *ctx,
                         uint8_t *out, uint32_t out_cap);
