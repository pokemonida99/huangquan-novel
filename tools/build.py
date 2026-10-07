"""把小說合訂稿（src/novel.md）拆成靜態網站：首頁、人物介紹、每章一頁、附錄。
插圖從 ../1005/小說文庫/ 讀原檔，轉成 WebP 放到 img/。

用法（在專案根目錄）：python3 tools/build.py
需要 Pillow（有 WebP 支援）。
"""
import hashlib, html, json, os, re, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_IMG = os.path.join(os.path.dirname(ROOT), "1005", "小說文庫")   # 插圖原檔所在
os.chdir(ROOT)

SITE = "黃泉燒肉店｜小說文庫"
CREDIT = ('原作：IG 短劇《黃泉燒肉店》© 棲渺拾光 '
          '<a href="https://www.instagram.com/baoandrain0428/" rel="noopener">@baoandrain0428</a>。'
          '本站為粉絲改寫的小說，非官方作品，不做商業用途。')
INTRO = ("這間店，讓來到黃泉的人坐下來，吃一頓自己喜歡的飯。有人想見最後一面，有人想說一句真心話；"
         "店裡的人，也各自帶著還沒走完的故事。")
ABOUT = ("依 IG 短劇《黃泉燒肉店》的劇情與台詞改寫成小說，涵蓋原作第 1 至 104 話。"
         "正文依故事轉折分為七卷、二十三章，補上日常與內心描寫；第六季仍在連載，正文停在第 104 話，尚未揭曉的結果不另作補完。")

# ------------------------------------------------------------------ 圖片
IMG_CACHE = {}


def image(src):
    """原檔相對路徑 → 網站用的 WebP 路徑（同一張圖只轉一次，原檔沒變就不重轉）"""
    if src in IMG_CACHE:
        return IMG_CACHE[src]
    path = os.path.join(SRC_IMG, src)
    if not os.path.exists(path):
        sys.exit("找不到插圖：" + path)
    name = os.path.splitext(os.path.basename(src))[0]
    sub = "c" if "人物插畫" in src else "s"
    out = "img/%s/%s.webp" % (sub, re.sub(r"[^\w一-鿿-]", "_", name))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if not os.path.exists(out) or os.path.getmtime(path) > os.path.getmtime(out):
        im = Image.open(path).convert("RGB")
        lim = 640 if sub == "c" else 1200
        if max(im.size) > lim:
            r = lim / max(im.size)
            im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
        im.save(out, "WEBP", quality=80, method=6)
    w, h = Image.open(out).size
    IMG_CACHE[src] = (out, w, h)
    return IMG_CACHE[src]


THUMBS = set()


def thumb(src):
    """圖庫用的小縮圖（寬 480）"""
    big = image(src)[0]
    out = big.replace("img/", "img/t/", 1)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if not os.path.exists(out) or os.path.getmtime(big) > os.path.getmtime(out):
        im = Image.open(big)
        im.thumbnail((480, 720), Image.LANCZOS)
        im.save(out, "WEBP", quality=72, method=6)
    THUMBS.add(out)
    w, h = Image.open(out).size
    return out, w, h


# ------------------------------------------------------------------ 解析
IMG_RE = re.compile(r"^!\[(.*?)\]\((.*?)\)\s*$")


def blocks(lines):
    """Markdown 行 → [('p', 文字) | ('img', alt, src) | ('h3', 文字)]"""
    out, para = [], []

    def flush():
        if para:
            out.append(("p", "".join(para)))
            para.clear()
    for ln in lines:
        s = ln.strip()
        if not s or s == "---":
            flush(); continue
        m = IMG_RE.match(s)
        if m:
            flush(); out.append(("img", m.group(1), m.group(2))); continue
        if s.replace("　", "").replace(" ", "") == "＊＊＊":   # 換場分隔
            flush(); out.append(("sep",)); continue
        if s.startswith("### "):
            flush(); out.append(("h3", s[4:])); continue
        para.append(s)
    flush()
    return out


def render(bs, prefix=""):
    h = []
    for b in bs:
        if b[0] == "p":
            h.append("<p>%s</p>" % html.escape(b[1]))
        elif b[0] == "sep":
            h.append('<p class="sep" aria-hidden="true">＊　＊　＊</p>')
        elif b[0] == "h3":
            h.append("<h3>%s</h3>" % html.escape(b[1]))
        else:
            alt = b[1]
            src, w, hh = image(b[2])
            cap = alt.split("・")[-1] if "・" in alt else alt.split("｜")[0]   # 「章名｜文庫插畫・原作片名」只留原作片名
            h.append('<figure><img src="%s%s" width="%d" height="%d" alt="%s" loading="lazy" decoding="async">'
                     '<figcaption>%s</figcaption></figure>' % (prefix, src, w, hh, html.escape(alt), html.escape(cap)))
    return "\n".join(h)


text = open("src/novel.md", encoding="utf-8").read().split("\n")
# 依一級標題切段：書名、人物介紹、各卷
parts, cur = [], None
for ln in text:
    if ln.startswith("# "):
        cur = {"title": ln[2:].strip(), "lines": []}
        parts.append(cur)
    elif cur:
        cur["lines"].append(ln)

front, people, vols = parts[0], parts[1], parts[2:]
_v = re.search(r"版本：\s*(v[\d.]+)\s*[·‧]\s*([\d-]+)", "\n".join(front["lines"]))
VERSION = "%s（%s）" % _v.groups() if _v else ""
cover = next(b for b in blocks(front["lines"]) if b[0] == "img")

# 人物介紹：每個 ## 一位
chars = []
for ln in people["lines"]:
    if ln.startswith("## "):
        chars.append({"name": ln[3:].strip(), "lines": []})
    elif chars:
        chars[-1]["lines"].append(ln)
    else:
        people.setdefault("lead", []).append(ln)

# 各卷各章
chapters = []
volumes = []
for v in vols:
    vol = {"title": v["title"], "chapters": []}
    volumes.append(vol)
    for ln in v["lines"]:
        if ln.startswith("## "):
            m = re.match(r"第(\d+)章\s*(.*)", ln[3:].strip())
            ch = {"no": int(m.group(1)), "title": m.group(2), "vol": v["title"], "lines": []}
            chapters.append(ch); vol["chapters"].append(ch)
        elif vol["chapters"]:
            vol["chapters"][-1]["lines"].append(ln)
for ch in chapters:
    ch["blocks"] = blocks(ch["lines"])
    ch["chars"] = sum(len(b[1]) for b in ch["blocks"] if b[0] == "p")
    ch["file"] = "ch%02d.html" % ch["no"]
    ch["thumb"] = next((b for b in ch["blocks"] if b[0] == "img"), None)

# ------------------------------------------------------------------ 版型
VER = hashlib.md5(open("assets/style.css", "rb").read() + open("assets/reader.js", "rb").read()).hexdigest()[:8]


def page(title, body, prefix="", kind="", desc=""):
    return f"""<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc or INTRO)}">
<meta name="theme-color" content="#f6efe3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#121014" media="(prefers-color-scheme: dark)">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc or INTRO)}">
<meta property="og:image" content="{prefix}{image(cover[2])[0]}">
<link rel="icon" href="{prefix}assets/icon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefix}assets/style.css?v={VER}">
<script>try{{var t=localStorage.getItem('hq.theme');if(t)document.documentElement.dataset.theme=t;var f=localStorage.getItem('hq.fs');if(f)document.documentElement.style.setProperty('--fs',f+'px')}}catch(e){{}}</script>
</head>
<body class="{kind}">
<div class="progress" id="progress"></div>
<header class="bar">
  <a class="brand" href="{prefix}index.html">黃泉燒肉店<span>小說文庫</span></a>
  <div class="tools">
    <a class="tool" href="{prefix}gallery.html">圖庫</a>
    <button id="btnToc" aria-label="目錄">目錄</button>
    <button id="btnSet" aria-label="閱讀設定">Aa</button>
  </div>
</header>
<div class="panel" id="setPanel" hidden>
  <div class="row"><span>字級</span><button data-fs="-1" aria-label="縮小字級">A−</button><b id="fsNow"></b><button data-fs="1" aria-label="放大字級">A＋</button></div>
  <div class="row"><span>背景</span><button data-theme="light">紙頁</button><button data-theme="sepia">米黃</button><button data-theme="dark">夜讀</button><button data-theme="">跟隨系統</button></div>
</div>
<nav class="drawer" id="toc" hidden aria-label="目錄">{toc_html(prefix)}</nav>
{body}
<footer class="foot"><p>{CREDIT}</p></footer>
<script src="{prefix}assets/reader.js?v={VER}"></script>
</body>
</html>
"""


def toc_html(prefix=""):
    h = ['<a class="toc-top" href="%sindex.html">封面與目錄</a>' % prefix,
         '<a class="toc-top" href="%scharacters.html">人物介紹</a>' % prefix]
    for v in volumes:
        h.append('<div class="toc-vol">%s</div>' % html.escape(v["title"]))
        for c in v["chapters"]:
            h.append('<a href="%s%s" data-ch="%d"><i>%02d</i>%s</a>' % (prefix, c["file"], c["no"], c["no"], html.escape(c["title"])))
    h.append('<a class="toc-top" href="%sappendix.html">附錄：原篇對照</a>' % prefix)
    h.append('<a class="toc-top" href="%sgallery.html">插畫圖庫</a>' % prefix)
    return "\n".join(h)


N_ILLUS = len({m for m in re.findall(r"\]\((插圖[^)]*)\)", "\n".join(text)) if "封面" not in m})


def build_index():
    src, w, h = image(cover[2])
    total = sum(c["chars"] for c in chapters)
    vols = []
    for v in volumes:
        items = []
        for c in v["chapters"]:
            th = image(c["thumb"][2])[0] if c["thumb"] else ""
            items.append(f'<a class="chap" href="{c["file"]}" data-ch="{c["no"]}">'
                         f'<img src="{th}" alt="" loading="lazy" decoding="async">'
                         f'<span class="n">第{c["no"]:02d}章</span><span class="t">{html.escape(c["title"])}</span>'
                         f'<span class="m">約 {round(c["chars"] / 1000, 1)} 千字</span></a>')
        vt = v["title"].split("　")
        vols.append(f'<section class="vol"><h2><small>{html.escape(vt[0])}</small>{html.escape(vt[-1])}</h2>'
                    f'<div class="chaps">{"".join(items)}</div></section>')
    body = f"""<main class="home">
<section class="hero">
  <img class="cover" src="{src}" width="{w}" height="{h}" alt="封面">
  <div class="hero-tx">
    <p class="kicker">粉絲改寫小說 ‧ 第 1–104 話</p>
    <h1>黃泉燒肉店</h1>
    <p class="intro">{html.escape(INTRO)}</p>
    <p class="meta">{('版本 ' + VERSION + ' ‧ ') if VERSION else ''}七卷 ‧ 二十三章 ‧ 約 {round(total / 10000, 1)} 萬字 ‧ {N_ILLUS} 張插畫</p>
    <div class="cta"><a class="btn" href="{chapters[0]['file']}">從第一章開始</a><a class="btn ghost" id="resume" hidden href="#">繼續閱讀</a></div>
  </div>
</section>
<p class="about">{html.escape(ABOUT)}</p>
<section class="vol"><h2><small>開卷之前</small>人物介紹</h2>
  <a class="peoplelink" href="characters.html">{''.join(f'<img src="{image(b[2])[0]}" alt="" loading="lazy">' for c in chars[:8] for b in blocks(c["lines"]) if b[0] == "img")}<span>認識店裡的人 →</span></a>
</section>
{''.join(vols)}
<section class="vol"><h2><small>欣賞插畫</small>圖庫</h2><a class="gal-teaser" href="gallery.html">{''.join('<img src="%s" alt="" loading="lazy">' % thumb(c["thumb"][2])[0] for c in chapters[::4] if c["thumb"])}<span>看全部 {N_ILLUS} 張 →</span></a></section>
<section class="vol"><h2><small>附錄</small>原篇對照</h2><p class="about"><a href="appendix.html">小說第 1–104 話與原作集數的對照表 →</a></p></section>
</main>"""
    open("index.html", "w").write(page(SITE, body, kind="is-home"))


def build_characters():
    cards = []
    for c in chars:
        bs = blocks(c["lines"])
        ims = [b for b in bs if b[0] == "img"]       # 合寫的人物卡會有好幾張插畫
        text = render([b for b in bs if b[0] != "img"])
        pics = "".join('<img src="%s" width="%d" height="%d" alt="%s" loading="lazy" decoding="async">'
                       % (*image(b[2]), html.escape(b[1].split("｜")[0])) for b in ims)
        cls = "pics multi" if len(ims) > 1 else "pics"
        cards.append(f'<article class="person"><div class="{cls}">{pics}</div><div><h2>{html.escape(c["name"])}</h2>{text}</div></article>')
    lead = render(blocks(people.get("lead", [])))
    body = f'<main class="read"><header class="ch-head"><p class="kicker">開卷之前</p><h1>人物介紹</h1></header>{lead}<div class="people">{"".join(cards)}</div>' \
           f'<nav class="pager"><span></span><a href="{chapters[0]["file"]}">第01章　{html.escape(chapters[0]["title"])} →</a></nav></main>'
    open("characters.html", "w").write(page("人物介紹｜" + SITE, body, kind="is-read"))


def build_chapters():
    for i, c in enumerate(chapters):
        prev = chapters[i - 1] if i else None
        nxt = chapters[i + 1] if i + 1 < len(chapters) else None
        pv = f'<a href="{prev["file"]}">← 第{prev["no"]:02d}章　{html.escape(prev["title"])}</a>' if prev else '<a href="characters.html">← 人物介紹</a>'
        nx = f'<a href="{nxt["file"]}">第{nxt["no"]:02d}章　{html.escape(nxt["title"])} →</a>' if nxt else '<a href="appendix.html">附錄：原篇對照 →</a>'
        end = '<p class="tbc">（第六季連載中，故事未完待續）</p>' if not nxt else ""
        vt = c["vol"].replace("　", " ‧ ")
        body = f"""<main class="read" data-ch="{c['no']}">
<header class="ch-head"><p class="kicker">{html.escape(vt)}</p><h1><small>第{c['no']:02d}章</small>{html.escape(c['title'])}</h1>
<p class="meta">約 {round(c['chars'] / 1000, 1)} 千字 ‧ 閱讀約 {max(1, round(c['chars'] / 500))} 分鐘</p></header>
<article class="text">{render(c['blocks'])}</article>{end}
<nav class="pager">{pv}{nx}</nav>
</main>"""
        open(c["file"], "w").write(page(f"第{c['no']:02d}章 {c['title']}｜{SITE}", body, kind="is-read",
                                        desc=next((b[1] for b in c["blocks"] if b[0] == "p"), "")[:80]))


def build_appendix():
    rows = []
    for ln in open("src/appendix.md", encoding="utf-8"):
        m = re.match(r"\|\s*(\d{3})\s*\|\s*(\S+)\s*\|\s*(.+?)\s*\|", ln)
        if m:
            rows.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % tuple(html.escape(x) for x in m.groups()))
    body = f"""<main class="read"><header class="ch-head"><p class="kicker">附錄</p><h1>原篇對照</h1></header>
<p>小說依事件轉折分章，不按影片一集一章切開。下表列出小說涵蓋的原作 104 話，以及對應的原作集數（EP 季-集）與片名，方便對照影片。</p>
<div class="tablewrap"><table><thead><tr><th>話數</th><th>原作集數</th><th>原作片名</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<nav class="pager"><a href="{chapters[-1]['file']}">← 第{chapters[-1]['no']:02d}章　{html.escape(chapters[-1]['title'])}</a><a href="index.html">回到目錄 →</a></nav></main>"""
    open("appendix.html", "w").write(page("原篇對照｜" + SITE, body, kind="is-read"))
    return len(rows)


def build_gallery():
    """圖庫：封面、人物插畫、各章插畫，點開看大圖並可連回章節"""
    items, secs = [], []

    def card(src, cap, sub, link):
        i = len(items)
        big, bw, bh = image(src)
        t, tw, th = thumb(src)
        items.append({"src": big, "cap": cap, "sub": sub, "link": link})
        return (f'<button class="g-item" data-i="{i}"><img src="{t}" width="{tw}" height="{th}" alt="{html.escape(cap)}" loading="lazy" decoding="async">'
                f'<span>{html.escape(cap)}</span></button>')

    secs.append('<section class="g-sec"><h2>封面</h2><div class="g-grid">' + card(cover[2], "封面", "黃泉燒肉店｜小說文庫", "index.html") + '</div></section>')
    people_cards = []
    for c in chars:
        for b in blocks(c["lines"]):
            if b[0] == "img":
                people_cards.append(card(b[2], b[1].split("｜")[0], "人物介紹", "characters.html"))
    secs.append('<section class="g-sec"><h2>人物</h2><div class="g-grid">' + "".join(people_cards) + '</div></section>')
    for v in volumes:
        vt = v["title"].replace("　", " ‧ ")
        cs = []
        for ch in v["chapters"]:
            for b in ch["blocks"]:
                if b[0] == "img":
                    alt = b[1]
                    cap = alt.split("・")[-1] if "・" in alt else alt.split("｜")[0]
                    cs.append(card(b[2], cap, f"第{ch['no']:02d}章　{ch['title']}", ch["file"]))
        secs.append(f'<section class="g-sec"><h2>{html.escape(vt)}</h2><div class="g-grid">' + "".join(cs) + '</div></section>')
    body = f"""<main class="gallery">
<header class="ch-head"><p class="kicker">欣賞插畫</p><h1>圖庫</h1><p class="meta">{len(items)} 張插畫 ‧ 點圖片看大圖，可以左右切換</p></header>
{''.join(secs)}
</main>
<div class="lb" id="lb" hidden role="dialog" aria-modal="true" aria-label="插畫">
  <button class="lb-x" data-lb="close" aria-label="關閉">✕</button>
  <button class="lb-nav prev" data-lb="prev" aria-label="上一張">‹</button>
  <figure><img id="lbImg" alt=""><figcaption><b id="lbCap"></b><span id="lbSub"></span><a id="lbLink" href="#">到這一章閱讀 →</a></figcaption></figure>
  <button class="lb-nav next" data-lb="next" aria-label="下一張">›</button>
</div>
<script>window.GALLERY={json.dumps(items, ensure_ascii=False)};</script>"""
    open("gallery.html", "w").write(page("插畫圖庫｜" + SITE, body, kind="is-gallery"))
    return len(items)


build_index(); build_characters(); build_chapters(); n = build_appendix(); ng = build_gallery()
json.dump([{"no": c["no"], "title": c["title"], "file": c["file"]} for c in chapters],
          open("assets/chapters.json", "w"), ensure_ascii=False)
used = {v[0] for v in IMG_CACHE.values()} | THUMBS
for d, _, fs in os.walk("img"):                 # 清掉這次沒用到的舊圖
    for f in fs:
        if os.path.join(d, f) not in used:
            os.remove(os.path.join(d, f))
size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk("img") for f in fs)
print(f"{len(chapters)} 章、{len(chars)} 位人物、附錄 {n} 列、圖庫 {ng} 張、插圖 {len(IMG_CACHE)} 張（{size / 1e6:.1f} MB）")
