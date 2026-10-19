#!/usr/bin/env python3
"""Canibalização e links internos a partir do sitemap (ou de uma lista de URLs/títulos) do blog.

Uso:
  python3 sitemap_links.py --sitemap https://blog.site.com.br/sitemap.xml --keyword "controle de ponto" [--secondary "a,b"] --out post_data/internal.json
  python3 sitemap_links.py --urls post_data/urls.csv --keyword "..." --out ...        # csv: url[,title]
  python3 sitemap_links.py --sitemap ... --keywords post_data/keywords.csv --out ...  # modo pauta: um resultado por linha
Para cada palavra-chave: posts com alta sobreposição (risco de canibalização → refresh em vez de post novo) e
candidatos a link interno (sobreposição parcial), com âncora sugerida. Sem rede: passe o sitemap salvo em arquivo.
Copyright (c) 2026 Ubirajara Carratu, Carratu Digital. PolyForm Noncommercial 1.0.0.
"""
import argparse
import csv
import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

UA = "Mozilla/5.0 (compatible; CarratuSkill/1.0)"
STOP = set("a o as os um uma uns umas de da do das dos em na no nas nos por para pra com sem e ou que se ao aos à às "
           "como melhor melhores guia dicas tipos quais qual quando onde porque por que o que the of to and for in how what is".split())
SKIP = re.compile(r"/(tag|categoria|category|author|autor|page|pagina|wp-content|feed|privacidade|politica|contato|sobre|login)(/|$)|\.(jpg|png|pdf|xml)$", re.I)


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def stem(w):
    w = re.sub(r"(coes|cao|oes|ao|mente|ais|eis|ns|s|a|o|e)$", "", w) if len(w) > 5 else re.sub(r"s$", "", w)
    return w[:7]


def cw(s):
    return {stem(w) for w in norm(s).split() if w not in STOP and len(w) > 2}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")


def load_sitemap(src, seen=None, depth=0):
    seen = seen if seen is not None else set()
    xml = fetch(src) if src.startswith("http") else Path(src).read_text(encoding="utf-8", errors="replace")
    locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)
    urls = []
    if "<sitemapindex" in xml and depth < 2:
        for child in locs:
            if child not in seen:
                seen.add(child)
                try:
                    urls += load_sitemap(child, seen, depth + 1)
                except Exception as e:
                    print(f"  (sitemap filho falhou: {child}: {e})", file=sys.stderr)
    else:
        urls = locs
    return [u for u in urls if not SKIP.search(urlparse(u).path)]


def title_from_url(u):
    return urlparse(u).path.strip("/").split("/")[-1].replace("-", " ")


def analyze(keyword, secondary, pages, min_link=0.25, min_cannibal=0.75):
    kw = cw(keyword)
    all_kw = kw | set().union(*(cw(s) for s in secondary)) if secondary else kw
    cannibal, links = [], []
    for p in pages:
        pw = cw(p["title"]) | cw(title_from_url(p["url"]))
        if not pw or not kw:
            continue
        overlap_kw = len(kw & pw) / len(kw)
        overlap_any = len(all_kw & pw) / max(1, len(pw))
        if overlap_kw >= min_cannibal:
            cannibal.append({"url": p["url"], "title": p["title"], "overlap": round(overlap_kw, 2)})
        elif overlap_kw >= min_link or overlap_any >= 0.4:
            links.append({"url": p["url"], "title": p["title"], "anchor": p["title"] or title_from_url(p["url"]),
                          "score": round(max(overlap_kw, overlap_any), 2)})
    links.sort(key=lambda x: -x["score"])
    return {"keyword": keyword, "cannibal_risk": cannibal, "internal_link_candidates": links[:8],
            "recommendation": "refresh do post existente ou ângulo diferente" if cannibal else "post novo"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sitemap")
    ap.add_argument("--urls", help="CSV com url[,title]")
    ap.add_argument("--keyword")
    ap.add_argument("--secondary", default="")
    ap.add_argument("--keywords", help="CSV da pauta (coluna keyword) para analisar várias")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    pages = []
    if a.sitemap:
        try:
            pages = [{"url": u, "title": ""} for u in load_sitemap(a.sitemap)]
        except Exception as e:
            print(f"Sitemap inacessível: {e}. Salve o XML e passe o arquivo, ou use --urls.", file=sys.stderr)
            return 3
    if a.urls:
        with open(a.urls, encoding="utf-8") as f:
            for row in csv.reader(f):
                if row and row[0].startswith("http"):
                    pages.append({"url": row[0], "title": row[1] if len(row) > 1 else ""})
    if not pages:
        sys.exit("Nenhuma URL. Passe --sitemap ou --urls.")
    kws = [a.keyword] if a.keyword else []
    if a.keywords:
        with open(a.keywords, encoding="utf-8") as f:
            kws += [r["keyword"] for r in csv.DictReader(f) if r.get("keyword")]
    sec = [s.strip() for s in a.secondary.split(",") if s.strip()]
    results = [analyze(k, sec if k == a.keyword else [], pages) for k in kws]
    out = {"pages_indexed": len(pages), "results": results}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(pages)} URLs no blog")
    for r in results:
        print(f"  \"{r['keyword']}\": {len(r['cannibal_risk'])} risco(s) de canibalização, {len(r['internal_link_candidates'])} links internos → {r['recommendation']}")
        for c in r["cannibal_risk"][:3]:
            print(f"      ! {c['url']} ({c['overlap']:.0%})")
        for l in r["internal_link_candidates"][:4]:
            print(f"      → {l['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
