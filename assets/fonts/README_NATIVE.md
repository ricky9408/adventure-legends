# Native Japanese typography

Japanese prose, menus, names and controls use **PixelMplus12 Regular at exactly
12 pixels**, with no scaling or smoothing. The font is an outline conversion of
the M+ 12px bitmap design. Compile-time monochrome rasterization creates the
ordinary UiRun pixel spans; the cartridge contains no TTF decoder or font cache.

Official source: https://github.com/itouhiro/PixelMplus

- Author credit: **itouhiro / M+ FONTS PROJECT**.
- `pixelmplus/PixelMplus12-Regular.ttf` is the unmodified author file; SHA-256
  `02f19467ea7cc235cc06c570b7f6c3b0a12a6f682bc8d74c43f2d323d97bcd12`.
- `pixelmplus/LICENSE_E` is the exact official license; SHA-256
  `907e9f5ac24cba6ce2523cd2a66d6ba143e082c685344dfa8d30ef12f67410a0`.

The measured shop effect summaries exceed their single-row width at12px (up to
295px). Those summaries and the constrained gear units footer use **k8x12**, the
author's native8×12 bitmap. Its glyphs are not squeezed from a12px-wide font.

Official source: https://littlelimit.net/k8x12.htm

- Author credit: **Num Kadoma**.
- `k8x12/k8x12.bdf` is the exact author BDF, SHA-256
  `97361b327b410c2cd6e8fe87ed3873387229e76af13829931d6987f267585277`.
- Downloaded official `k8x12_bdf_2021-05-05.zip`, SHA-256
  `305ab94915ec3c8e1ada08f493ee5bfdd21e2710a97d7c4d4272444d8e18ff40`.
- Original `readme.txt`, `k8x12.txt` and the author license page are preserved.
  License source: https://littlelimit.net/font.htm#license

Small10px-high ASCII footers retain the original unscaled GBJ-Slim bitmap and
DejaVu8 lowercase glyphs. Their author credits and license notices remain.
Original GBJ atlas APIs and Noto notices are also retained for historical
source-atlas validation; the main Japanese rendering path no longer uses the
dense10px Noto Bold fallback.

The shared compiler checks cmap coverage, source ink bounds and target height
before cropping. Every text family round-trips both halfword alignments exactly.
Keep those checks, native-size views, actual panel bounds and frame-budget
verification when adding copy or changing layout. Neither font is installed on
the user's computer.
