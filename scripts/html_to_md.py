#!/usr/bin/env python3
"""Modo refresh: transforma um post publicado (HTML) no .md com frontmatter que o lint e o redator usam.

Uso:
  python3 html_to_md.py https://blog.site.com.br/post/ --out post_data/current.md
  python3 html_to_md.py post_data/current.html --url https://blog.site.com.br/post/ --out post_data/current.md
  (para WordPress via REST/conector: salve o `content.rendered` num .html e passe --title/--meta pelo JSON)
Extrai title, meta description, canonical, datas, autor, H1, corpo em Markdown (headings, parágrafos, listas,
tabelas, links, imagens com alt, blockquotes) e os JSON-LD encontrados. Requer beautifulsoup4.
Saídas: 0 ok · 3 rede bloqueada. Copyright (c) 2026 Ubirajara Carratu, Carratu Digital. PolyForm Noncommercial 1.0.0.
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup, NavigableString
except ImportError:
    sys.exit("Instale: pip install beautifulsoup4 --break-system-packages")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode(r.headers.get_content_charset() or "utf-8", "replace")


def inline(node):
    parts = []
    for c in node.children if hasattr(node, "children") else []:
        if isinstance(c, NavigableString):
            parts.append(re.sub(r"\s+", " ", str(c)))
        elif c.name in ("strong", "b"):
            parts.append(f"**{inline(c).strip()}**")
        elif c.name in ("em", "i"):
            parts.append(f"*{inline(c).strip()}*")
        elif c.name == "a":
            parts.append(f"[{inline(c).strip()}]({c.get('href', '')})")
        elif c.name == "img":
            parts.append(f"![{c.get('alt', '')}]({c.get('src', '')})")
        elif c.name == "br":
            parts.append(" ")
        elif c.name == "code":
            parts.append(f"`{c.get_text()}`")
        else:
            parts.append(inline(c))
    return "".join(parts)


def block_md(node, out, depth=0):
    for c in node.children:
        if isinstance(c, NavigableString):
            t = str(c).strip()
            if t:
                out.append(t)
            continue
        n = c.name
        if n in ("script", "style", "nav", "aside", "form", "noscript", "footer", "header"):
            continue
        if re.fullmatch(r"h[1-6]", n or ""):
            out.append(f"\n{'#' * int(n[1])} {inline(c).strip()}\n")
        elif n == "p":
            t = inline(c).strip()
            if t:
                out.append(t + "\n")
        elif n in ("ul", "ol"):
            for i, li in enumerate(c.find_all("li", recursive=False), 1):
                mark = f"{i}." if n == "ol" else "-"
                out.append(f"{'  ' * depth}{mark} {inline(li).strip()}")
            out.append("")
        elif n == "table":
            rows = [[inline(td).strip() for td in tr.find_all(["th", "td"])] for tr in c.find_all("tr")]
            rows = [r for r in rows if r]
            if rows:
                out.append("| " + " | ".join(rows[0]) + " |")
                out.append("|" + "---|" * len(rows[0]))
                for r in rows[1:]:
                    out.append("| " + " | ".join(r) + " |")
                out.append("")
        elif n == "blockquote":
            out.append("> " + inline(c).strip() + "\n")
        elif n == "pre":
            out.append("```\n" + c.get_text() + "\n```\n")
        elif n in ("figure", "picture"):
            if c.find("table") or c.find("blockquote") or c.find(["ul", "ol"]):
                block_md(c, out, depth)
            else:
                img = c.find("img")
                if img:
                    out.append(f"![{img.get('alt', '')}]({img.get('src', '')})\n")
        elif n == "img":
            out.append(f"![{c.get('alt', '')}]({c.get('src', '')})\n")
        elif n == "details":
            s = c.find("summary")
            out.append(f"### {inline(s).strip() if s else 'Pergunta'}")
            body = [x for x in c.children if getattr(x, 'name', None) != 'summary']
            tmp = []
            for x in body:
                if isinstance(x, NavigableString):
                    if str(x).strip():
                        tmp.append(str(x).strip())
                else:
                    block_md(x.parent if False else BeautifulSoup(str(x), "html.parser"), tmp, depth)
            out.extend(tmp)
        else:
            block_md(c, out, depth)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="URL ou arquivo .html")
    ap.add_argument("--url", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--blog", default="")
    a = ap.parse_args()
    try:
        html = fetch(a.source) if a.source.startswith("http") else Path(a.source).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Falha ao obter o HTML: {e}", file=sys.stderr)
        return 3
    url = a.url or (a.source if a.source.startswith("http") else "")
    soup = BeautifulSoup(html, "html.parser")
    meta = lambda **k: (soup.find("meta", attrs=k) or {}).get("content", "")
    title_tag = soup.title.get_text(strip=True) if soup.title else ""
    h1 = soup.find("h1")
    canonical = (soup.find("link", rel="canonical") or {}).get("href", "")
    lds = []
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            lds.append(json.loads(s.string or ""))
        except Exception:
            pass
    node = None
    for sel in ("article .entry-content", ".entry-content", "article", "main", "[role=main]", ".post-content", "#content"):
        node = soup.select_one(sel)
        if node and len(node.get_text(" ", strip=True).split()) > 150:
            break
    node = node or soup.body or soup
    body = []
    block_md(node, body)
    md_body = re.sub(r"\n{3,}", "\n\n", "\n".join(body)).strip()
    if h1 and not md_body.startswith("# "):
        md_body = f"# {h1.get_text(' ', strip=True)}\n\n" + re.sub(r"^# .*\n+", "", md_body, count=1)
    slug = urlparse(canonical or url).path.strip("/").split("/")[-1] if (canonical or url) else Path(a.source).stem
    fm = {
        "title": h1.get_text(" ", strip=True) if h1 else title_tag,
        "seo_title": title_tag, "meta_description": meta(name="description"),
        "slug": slug, "keyword": "", "secondary_keywords": [],
        "author": meta(name="author") or "", "date": (meta(property="article:published_time") or "")[:10],
        "updated": (meta(property="article:modified_time") or "")[:10],
        "excerpt": meta(property="og:description") or "", "blog": a.blog,
        "image": meta(property="og:image") or "", "image_alt": "", "canonical": canonical or url,
        "schema_found": sorted({str(x.get("@type")) for x in lds if isinstance(x, dict)}),
        "mode": "refresh",
    }
    lines = ["---"] + [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in fm.items()] + ["---", "", md_body, ""]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(lines), encoding="utf-8")
    words = len(md_body.split())
    print(f"{slug}: {words} palavras, title {len(title_tag)} chars, meta {len(fm['meta_description'])} chars, "
          f"schema {fm['schema_found'] or 'nenhum'}, atualizado {fm['updated'] or '?'} → {a.out}")
    print("Preencha keyword e secondary_keywords no frontmatter antes do lint.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
