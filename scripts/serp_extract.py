#!/usr/bin/env python3
"""Mede as páginas do top 3 de uma palavra-chave a partir do HTML real (Metodologia Carratu).

Uso:
  python3 serp_extract.py URL1 URL2 URL3 --keyword "kw" --out post_data/top3.json
  python3 serp_extract.py post_data/serp/1.html 2.html 3.html --urls URL1,URL2,URL3 --keyword "kw" --out ...

Saídas: 0 ok · 3 rede bloqueada para todas as URLs (colete pelo navegador e passe os arquivos HTML).
Requer beautifulsoup4.
Copyright (c) 2026 Ubirajara Carratu, Carratu Digital. PolyForm Noncommercial 1.0.0.
"""
import argparse
import json
import re
import statistics
import sys
import unicodedata
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Instale: pip install beautifulsoup4 --break-system-packages")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
STOP = set("a o as os um uma de da do das dos em na no nas nos por para com e ou que se ao como mais seu sua the of to and for in".split())
NUM_RE = re.compile(r"(R\$\s?\d[\d.,]*|\d[\d.,]*\s?(%|mil\b|milh|bilh|x\b|vezes|dias|horas|meses|anos)|\b(19|20)\d{2}\b)", re.I)


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def cw(s):
    return [w for w in norm(s).split() if w not in STOP and len(w) > 2]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode(r.headers.get_content_charset() or "utf-8", "replace")


def main_node(soup):
    for sel in ("article", "main", "[role=main]", ".entry-content", ".post-content", "#content"):
        n = soup.select_one(sel)
        if n and len(n.get_text(" ", strip=True).split()) > 200:
            return n
    return soup.body or soup


def schema_types(soup):
    types = []
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "")
        except Exception:
            continue
        stack = [data]
        while stack:
            x = stack.pop()
            if isinstance(x, list):
                stack.extend(x)
            elif isinstance(x, dict):
                t = x.get("@type")
                if t:
                    types.extend(t if isinstance(t, list) else [t])
                stack.extend(v for v in x.values() if isinstance(v, (dict, list)))
    return sorted(set(map(str, types)))


def analyze(html, url, kw):
    soup = BeautifulSoup(html, "html.parser")
    meta = lambda **k: (soup.find("meta", attrs=k) or {}).get("content")
    title = soup.title.get_text(strip=True) if soup.title else ""
    desc = meta(name="description")
    time_tag = soup.find("time")
    pub = meta(property="article:published_time") or (time_tag.get("datetime") if time_tag else None)
    mod = meta(property="article:modified_time")
    author = meta(name="author")
    stypes = schema_types(soup)
    node = main_node(soup)
    for t in node.find_all(["script", "style", "nav", "header", "footer", "aside", "form", "noscript"]):
        t.decompose()
    text = node.get_text(" ", strip=True)
    words = text.split()
    h1 = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
    heads = [{"level": int(h.name[1]), "text": h.get_text(" ", strip=True)} for h in node.find_all(["h2", "h3"])]
    paras = [p.get_text(" ", strip=True) for p in node.find_all("p") if len(p.get_text(strip=True).split()) >= 8]
    first = " ".join(paras[:2])
    # palavras até a primeira frase que contém a keyword ou uma definição
    answer_at = None
    acc = 0
    kwc = cw(kw)
    for sent in re.split(r"(?<=[.!?])\s+", " ".join(paras)):
        n = norm(sent)
        if (kwc and all(w in n for w in kwc)) or re.search(r"\b(e|sao) (um|uma|o|a)\b|consiste em|significa", n):
            answer_at = acc
            break
        acc += len(sent.split())
    links = [a.get("href", "") for a in node.find_all("a", href=True)]
    host = urlparse(url).netloc.lower()
    ext = sorted({urlparse(l).netloc.lower() for l in links if urlparse(l).netloc and urlparse(l).netloc.lower() != host})
    qheads = [h["text"] for h in heads if h["text"].strip().endswith("?")]
    faq = bool(re.search(r"perguntas frequentes|\bfaq\b|d[uú]vidas frequentes", text[-6000:], re.I)) or "FAQPage" in stypes
    return {
        "url": url, "title": title, "title_len": len(title), "meta_description": desc,
        "h1": h1, "word_count": len(words), "headings": heads,
        "h2_count": sum(1 for h in heads if h["level"] == 2),
        "question_headings": qheads,
        "first_paragraph": first[:600], "answer_at_word": answer_at,
        "numbers": len(NUM_RE.findall(text)), "external_domains": ext,
        "tables": len(node.find_all("table")), "lists": len(node.find_all(["ul", "ol"])),
        "images": len(node.find_all("img")), "faq_detected": faq,
        "date_published": pub, "date_modified": mod, "author": author, "schema_types": stypes,
        "keyword_in_title": bool(kwc and all(w in norm(title) for w in kwc)),
    }


def group_h2(pages, kw=""):
    """Agrupa H2 parecidos entre páginas (sobreposição de palavras ≥ 50%, ignorando as da palavra-chave)."""
    kws = set(cw(kw))
    items = []
    for i, p in enumerate(pages):
        for h in p["headings"]:
            if h["level"] == 2:
                full = set(cw(h["text"]))
                items.append((i, h["text"], (full - kws) or full))
    groups = []
    for i, t, s in items:
        if not s:
            continue
        for g in groups:
            inter = len(s & g["words"]) / max(1, min(len(s), len(g["words"])))
            if inter >= 0.5:
                g["pages"].add(i)
                g["examples"].append(t)
                break
        else:
            groups.append({"words": set(s), "pages": {i}, "examples": [t]})
    common = [{"topic": g["examples"][0], "pages": sorted(p + 1 for p in g["pages"]), "examples": g["examples"][:3]}
              for g in groups if len(g["pages"]) >= 2]
    unique = [{"topic": g["examples"][0], "page": next(iter(g["pages"])) + 1} for g in groups if len(g["pages"]) == 1]
    return common, unique


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="*", help="URLs ou arquivos .html")
    ap.add_argument("--urls", help="URLs originais dos arquivos HTML, separadas por vírgula, na mesma ordem")
    ap.add_argument("--keyword", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--from-json", help="JSON devolvido por browser_collect.js ({pages:[{url,html}]})")
    a = ap.parse_args()
    urls = a.urls.split(",") if a.urls else []
    pages, errors = [], []
    if a.from_json:
        for item in json.loads(Path(a.from_json).read_text(encoding="utf-8")).get("pages", []):
            if item.get("html"):
                try:
                    pages.append(analyze(item["html"], item["url"], a.keyword))
                except Exception as e:
                    errors.append({"input": item["url"], "error": str(e)[:200]})
            else:
                errors.append({"input": item.get("url"), "error": item.get("error", "sem html")})
    for idx, inp in enumerate(a.inputs):
        try:
            if inp.startswith("http"):
                html, url = fetch(inp), inp
            else:
                html = Path(inp).read_text(encoding="utf-8", errors="replace")
                url = urls[idx] if idx < len(urls) else inp
            pages.append(analyze(html, url, a.keyword))
        except Exception as e:
            errors.append({"input": inp, "error": str(e)[:200]})
    if not pages:
        print(json.dumps({"errors": errors}, ensure_ascii=False, indent=2))
        print("Nenhuma página coletada: rede bloqueada? Colete pelo navegador e passe os arquivos HTML.", file=sys.stderr)
        return 3
    wc = [p["word_count"] for p in pages]
    common, unique = group_h2(pages, a.keyword)
    agg = {
        "pages": len(pages), "median_words": int(statistics.median(wc)), "min_words": min(wc), "max_words": max(wc),
        "median_h2": int(statistics.median(p["h2_count"] for p in pages)),
        "with_faq": sum(p["faq_detected"] for p in pages), "with_tables": sum(1 for p in pages if p["tables"]),
        "median_numbers": int(statistics.median(p["numbers"] for p in pages)),
        "answer_at_word": [p["answer_at_word"] for p in pages],
        "common_h2_topics": common, "unique_h2_topics": unique,
        "all_question_headings": sorted({q for p in pages for q in p["question_headings"]}),
    }
    out = {"keyword": a.keyword, "aggregate": agg, "pages": pages, "errors": errors}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(pages)} páginas medidas · mediana {agg['median_words']} palavras · {agg['median_h2']} H2 · "
          f"{len(common)} temas comuns · {len(unique)} temas exclusivos · FAQ em {agg['with_faq']}")
    for p in pages:
        print(f"  - {p['url']}: {p['word_count']} palavras, {p['h2_count']} H2, {p['numbers']} números, "
              f"resposta na palavra {p['answer_at_word']}, data {p['date_modified'] or p['date_published']}")
    if errors:
        print(f"  Falhas: {[e['input'] for e in errors]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
