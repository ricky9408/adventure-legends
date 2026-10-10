# GBJ / GBJ-Slim by GeeBee

Official source and author credit: https://geebeegb.itch.io/gbj

Downloaded 2026-10-07 from the page's official `GBJ Font.zip` download
(upload ID 12902905). Original archive: 71,970 bytes, SHA-256
`65931fea0dcd8ddad1099e1aa23890ec4536d07e5e1ea672887cf64d236ec56b`.
The four PNG/JSON files here are unmodified original archive entries.

## Published usage permission

The author did not include a separate license file in this archive. The official
page's 使用範囲 (usage scope), checked at download time, states:

- Commercial use is permitted.
- Free redistribution is permitted; use the official download where possible.
- Modification is permitted, including combining/replacing glyphs with kanji.
- Credit is optional, but appreciated by the author.

These are a plain-language summary of the author's page, not an invented SPDX
license. Adventure Legends explicitly credits GeeBee in the source and game.

## Integration

`assets/gbj_font.py` reads 8x8 cells at byte offset 32 using the supplied mapping.
Right-side magenta columns encode proportional width and are removed; original
left spacing and every ink pixel remain. GBJ is used normally; GBJ-Slim is used
for small footer text. Each is rasterized directly into GBA UiRun pixel spans.
The atlas is not stretched, antialiased or converted into a substitute font.

The pack has kana, Latin capitals, digits and symbols, not kanji or lowercase.
Noto Sans CJK Bold at 10px provides missing Japanese glyphs and DejaVu Sans at
8px provides unsupported ASCII/lowercase. Their original licenses are retained
one directory up. Existing purpose-built runtime stat digits remain unchanged
because their 4px cells are narrower than GBJ's unmodified numeral ink.

## Original file SHA-256

- GBJ.json: `5ecb03715593756be3c3135bbf4ec18bbde2d57ca3fe65b3011eef7b88ef661c`
- GBJ.png: `39acffbbb65988a079f9375be66a0446d1db537ac70adb2ae8ef48663ee720fd`
- GBJ-Slim.json: `38abc3619047c14169a369ec30a842ee7122642adaaae84cb6488ca07ab78063`
- GBJ-Slim.png: `96fe782302852d7cba95c1fa1e218bdb7155620549d59345a71ccc8eb6e6f379`
