#!/usr/bin/env python3
"""Fecha o ciclo: registra o que foi publicado e o que aconteceu depois (30 e 90 dias).

Uso:
  python3 track.py add post_data/checks.json --url https://blog.site.com.br/slug/ --date 2026-11-03 --log tracking/<blog>.csv
      Grava a linha do post (keyword, notas do lint, cauda/intenção se houver pauta.json) com as colunas de
      acompanhamento vazias.
  python3 track.py due tracking/<blog>.csv [--today AAAA-MM-DD]
      Lista os posts que completaram 30 ou 90 dias e ainda não têm medição.
  python3 track.py report tracking/<blog>.csv
      Resume: posição média por intenção/cauda, % com citação em IA, correlação simples entre nota do lint e
      resultado (serve para recalibrar a rubrica).
Colunas de medição (preencha com Search Console, Semrush ou painel de prompts):
  pos_30, impr_30, clicks_30, aio_30, ai_cited_30, pos_90, impr_90, clicks_90, aio_90, ai_cited_90, notes
Copyright (c) 2026 Ubirajara Carratu, Carratu Digital. PolyForm Noncommercial 1.0.0.
"""
import argparse
import csv
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

COLS = ["url", "slug", "keyword", "tail", "intent", "persona", "published", "score_seo", "score_geo", "score_aeo",
        "score_overall", "words", "pos_30", "impr_30", "clicks_30", "aio_30", "ai_cited_30",
        "pos_90", "impr_90", "clicks_90", "aio_90", "ai_cited_90", "notes"]


def read(path):
    p = Path(path)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLS})


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["add", "due", "report"])
    ap.add_argument("path")
    ap.add_argument("--url", default="")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--log")
    ap.add_argument("--pauta", help="pauta.json para puxar cauda/intenção/persona")
    ap.add_argument("--today", default=dt.date.today().isoformat())
    a = ap.parse_args()

    if a.cmd == "add":
        if not a.log:
            sys.exit("--log é obrigatório em add")
        ck = json.loads(Path(a.path).read_text(encoding="utf-8"))
        sc = ck.get("scores", {})
        row = {"url": a.url, "slug": a.url.rstrip("/").split("/")[-1] if a.url else Path(ck.get("post", "")).stem,
               "keyword": ck.get("keyword", ""), "published": a.date,
               "score_seo": (sc.get("seo") or {}).get("score"), "score_geo": (sc.get("geo") or {}).get("score"),
               "score_aeo": (sc.get("aeo") or {}).get("score"), "score_overall": ck.get("overall"),
               "words": ck.get("stats", {}).get("words")}
        if a.pauta and Path(a.pauta).exists():
            for r in json.loads(Path(a.pauta).read_text(encoding="utf-8")).get("rows", []):
                if r.get("keyword", "").lower() == row["keyword"].lower():
                    row.update(tail=r.get("tail", ""), intent=r.get("intent", ""), persona=r.get("persona", ""))
        rows = [r for r in read(a.log) if r.get("url") != row["url"] or not row["url"]]
        rows.append(row)
        write(a.log, rows)
        print(f"Registrado: {row['slug']} ({row['keyword']}) em {a.log}. Medições em {a.date} +30 e +90 dias.")
        return 0

    rows = read(a.path)
    today = dt.date.fromisoformat(a.today)
    if a.cmd == "due":
        due = []
        for r in rows:
            try:
                pub = dt.date.fromisoformat(r["published"])
            except Exception:
                continue
            age = (today - pub).days
            if age >= 30 and not r.get("pos_30") and not r.get("impr_30"):
                due.append((r, 30, age))
            if age >= 90 and not r.get("pos_90") and not r.get("impr_90"):
                due.append((r, 90, age))
        if not due:
            print("Nada a medir hoje.")
        for r, m, age in due:
            print(f"  medir +{m}: {r['url'] or r['slug']}  ({r['keyword']}, {age} dias)")
        print("\nFontes: Search Console (posição, impressões, cliques, filtro de IA se houver), Semrush (posição, SERP "
              "feature AI Overview), painel de prompts (ai_cited = marca citada em 3+ rodadas).")
        return 0

    # report
    def avg(key, filt=lambda r: True):
        vals = [num(r.get(key)) for r in rows if filt(r)]
        vals = [v for v in vals if v is not None]
        return (round(statistics.mean(vals), 1), len(vals)) if vals else (None, 0)

    print(f"{len(rows)} posts registrados")
    for m in (30, 90):
        p, n = avg(f"pos_{m}")
        cited = [r for r in rows if r.get(f"ai_cited_{m}") not in ("", None)]
        c = sum(1 for r in cited if str(r[f"ai_cited_{m}"]).lower() in ("1", "true", "sim", "yes"))
        print(f"  +{m} dias: posição média {p} (n={n}) · citados em IA {c}/{len(cited)}")
    for dim in ("intent", "tail"):
        groups = sorted({r.get(dim, "") for r in rows if r.get(dim)})
        for g in groups:
            p30, n = avg("pos_30", lambda r: r.get(dim) == g)
            p90, _ = avg("pos_90", lambda r: r.get(dim) == g)
            print(f"  {dim}={g}: pos30 {p30} · pos90 {p90} (n={n})")
    pairs = [(num(r.get("score_overall")), num(r.get("pos_90") or r.get("pos_30"))) for r in rows]
    pairs = [(s, p) for s, p in pairs if s is not None and p is not None]
    if len(pairs) >= 5:
        xs, ys = zip(*pairs)
        mx, my = statistics.mean(xs), statistics.mean(ys)
        cov = sum((x - mx) * (y - my) for x, y in pairs)
        den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
        r = cov / den if den else 0
        print(f"  Correlação nota do lint x posição: {r:.2f} (negativa = nota maior, posição melhor; n={len(pairs)})")
        if abs(r) < 0.2:
            print("  A nota não está prevendo resultado: revise pesos em rubric.json com os posts que performaram.")
    else:
        print("  Correlação nota x posição: precisa de 5+ posts medidos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
