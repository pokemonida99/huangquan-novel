# 黃泉燒肉店｜小說文庫

IG 短劇《黃泉燒肉店》（[@baoandrain0428](https://www.instagram.com/baoandrain0428/)）的粉絲改寫小說，涵蓋原作第 1–104 話。七卷、二十三章，約十萬字，附 71 張插畫。

線上閱讀：https://pokemonida99.github.io/huangquan-novel/

## 網站功能

- 每章一頁，插圖轉成 WebP（全站圖片約 6.6MB，原本單檔閱讀版 199MB）
- 目錄抽屜、上一章／下一章
- 字級調整，紙頁／米黃／夜讀三種背景
- 自動記住讀到哪裡，首頁有「繼續閱讀」，讀完的章節會標「已讀」（只存在讀者自己的瀏覽器）
- 手機優先

## 檔案

| 檔案 | 用途 |
|---|---|
| `src/novel.md` | 小說合訂稿（唯一來源） |
| `src/appendix.md` | 原篇對照表 |
| `tools/build.py` | 產生所有頁面與 `img/` 插圖 |
| `assets/` | 樣式、閱讀功能腳本 |
| `index.html`、`ch01–23.html`、`characters.html`、`appendix.html` | 產生出來的頁面，不要手改 |

## 更新

1. 改 `src/novel.md`
2. `python3 tools/build.py`（需要 Pillow；插圖原檔在 `../1005/小說文庫/插圖/`）
3. commit 並 push，GitHub Pages 會自動更新

## 版權

原作影片、劇情與角色屬於《棲渺拾光》。本站為粉絲改寫的非官方作品，不做商業用途。
