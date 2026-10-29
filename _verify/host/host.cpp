// 本机（PC）验证程序：不需要 ESP32 就能出图 / 跑压缩，方便反复调版式。
// 编译见 _verify/host/build.sh；用法：
//   host.exe preview  out.ppm [code] [temp]
//   host.exe compress in.bin out.lz      -> stdout 打印比特数
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include "ui.h"
#include "canvas.h"
#include "lz77.h"
#include "wmo.h"

static const uint8_t PAL[7][3] = {
    {0, 0, 0}, {255, 255, 255}, {0, 255, 0}, {0, 0, 255},
    {255, 0, 0}, {255, 255, 0}, {255, 128, 0}};

static void sample(int code, int temp) {
  Weather w;
  memset(&w, 0, sizeof w);
  w.valid = true;
  w.y = 2026; w.mo = 10; w.d = 29; w.dow = 4; w.hh = 6; w.mi = 0;
  strcpy(w.city, "上海");
  w.temp = temp; w.feels = temp - 1; w.code = code;
  w.hum = 68; w.wind = 12; w.pop = 30;
  w.tmax = temp + 3; w.tmin = temp - 6;
  w.code2 = 61; w.tmax2 = 15; w.tmin2 = 8;
  ui_begin(w);
}

int main(int argc, char **argv) {
  if (argc < 3) { fprintf(stderr, "usage: host preview out.ppm [code] [temp] | compress in out\n"); return 1; }
  if (!strcmp(argv[1], "preview")) {
    int code = argc > 3 ? atoi(argv[3]) : 0;
    int temp = argc > 4 ? atoi(argv[4]) : 21;
    sample(code, temp);
    FILE *f = fopen(argv[2], "wb");
    if (!f) { perror("open"); return 1; }
    fprintf(f, "P6\n%d %d\n255\n", UI_W, UI_H);
    std::vector<uint8_t> row(UI_W);
    for (int y = 0; y < UI_H; y++) {
      ui_row(y, row.data());
      for (int x = 0; x < UI_W; x++) fwrite(PAL[row[x] & 7], 1, 3, f);
    }
    fclose(f);
    printf("ok %s\n", argv[2]);
    return 0;
  }
  if (!strcmp(argv[1], "compress")) {
    FILE *f = fopen(argv[2], "rb");
    if (!f) { perror("open"); return 1; }
    std::vector<uint8_t> in;
    int ch;
    while ((ch = fgetc(f)) != EOF) in.push_back((uint8_t)ch);
    fclose(f);
    std::vector<uint8_t> out(in.size() * 2 + 64, 0);
    auto src = [](uint32_t p, void *ctx) -> uint8_t { return ((std::vector<uint8_t> *)ctx)->at(p); };
    Lz77Result r = lz77_compress((uint32_t)in.size(), src, &in, out.data(), (uint32_t)out.size());
    FILE *g = fopen(argv[3], "wb");
    fwrite(out.data(), 1, r.bytes, g);
    fclose(g);
    printf("%u\n", r.bits);
    return 0;
  }
  if (!strcmp(argv[1], "frame")) {
    sample(0, 21);
    ui_reset_cache();
    std::vector<uint8_t> out(48 * 1024, 0);
    Lz77Result r = lz77_compress(800u * 480u / 2u, ui_byte, nullptr, out.data(), (uint32_t)out.size());
    FILE *g = fopen(argv[2], "wb");
    fwrite(out.data(), 1, r.bytes, g);
    fclose(g);
    FILE *h = fopen(argv[3], "wb");
    std::vector<uint8_t> row(UI_W);
    for (int y = 0; y < UI_H; y++) {
      ui_row(y, row.data());
      for (int x = 0; x < UI_W; x += 2)
        fputc((row[x] << 4) | (row[x + 1] & 0x0F), h);
    }
    fclose(h);
    printf("%u %d %d\n", r.bits, r.bytes, (int)r.overflow);
    return 0;
  }

  fprintf(stderr, "unknown cmd\n");
  return 1;
}

