#!/usr/bin/env python3
"""Fact-check operacional: extrai as afirmações com dados de um post e monta a tabela de verificação.

Uso:
  python3 claims.py extract outputs/post.md --out post_data/claims.json
      Lista cada frase com número, %, R$, ano, "segundo X" etc., o link mais próximo e o status "pending".
  python3 claims.py status post_data/claims.json
      Resume: verificadas, pendentes, sem fonte. Saída 0 se tudo verificado, 1 se não.

Fluxo: Claude abre cada fonte, confirma o trecho e preenche "status" (verified | unverified | client_data |
removed) e "quote" (trecho da fonte que confirma). O lint_post.py lê este arquivo para o check geo.data_accuracy.
Copyright (c) 2026 Ubirajara Carratu, Carratu Digital. PolyForm Noncommercial 1.0.0.
"""
import argparse
import json
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
CLAIM_RE = re.compile(
    r"(\d[\d.,]*\s?(%|por cento|mil\b|milh|bilh|x\b|vezes|dias|horas|minutos|semanas|meses|anos|pontos|p\.p\.)"
    r"|R\$\s?\d|US\$\s?\d|\b(19|20)\d{2}\b|\b(segundo (a|o|os|as|um|uma)\b|de acordo com|conforme (a|o)\b|aponta|revela|"
    r"(estudo|pesquisa|relat[óo]rio|levantamento|dados) (d[aoe]|do|da|publicad|realizad|recente)|according to|a study|report by|survey)\b)",
    re.IGNORECASE)
SKIP_SECTIONS = ("fontes", "referencias", "referências", "sources")


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ú0-9\"“(])", text) if s.strip()]


def extract(md: str):
    body = md
    if md.startswith("---"):
        end = md.find("\n---", 3)
        body = md[end + 4:] if end != -1 else md
    claims, section, last_link, idx = [], "", None, 0
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("```"):
            continue
        h = re.match(r"^(#{1,6})\s+(.*)", line)
        if h:
            section = h.group(2)
            continue
        if section.lower().strip() in SKIP_SECTIONS or any(section.lower().startswith(s) for s in SKIP_SECTIONS):
            continue
        plain_line = re.sub(r"^([-*+]|\d+[.)]|>|\|)\s*", "", line)
        for sent in sentences(plain_line) if not line.startswith("|") else [plain_line]:
            links = LINK_RE.findall(sent)
            if links:
                last_link = links[-1][1]
            if not CLAIM_RE.search(LINK_RE.sub(r"\1", sent)):
                continue
            # frases só com o ano da data ou sem dado real são ruído; mantenha, o revisor marca "removed"/"na"
            idx += 1
            claims.append({
                "id": f"c{idx}", "section": section,
                "text": LINK_RE.sub(r"\1", sent)[:400],
                "source_url": links[-1][1] if links else (last_link if last_link and ("segundo" in sent.lower() or "estudo" in sent.lower()) else None),
                "source_inline": bool(links),
                "status": "pending", "quote": "", "note": "",
            })
    return claims


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["extract", "status"])
    ap.add_argument("path")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.cmd == "extract":
        claims = extract(Path(a.path).read_text(encoding="utf-8"))
        out = {"post": a.path, "claims": claims}
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{len(claims)} afirmações para verificar ({sum(1 for c in claims if not c['source_url'])} sem link próximo).")
        for c in claims:
            print(f"  {c['id']} [{c['section'][:30]}] {c['text'][:110]}  ← {c['source_url'] or 'SEM FONTE'}")
        return 0
    data = json.loads(Path(a.path).read_text(encoding="utf-8"))
    cl = data.get("claims", [])
    by = {}
    for c in cl:
        by.setdefault(c["status"], []).append(c)
    print(f"{len(cl)} afirmações: " + ", ".join(f"{k}={len(v)} " for k, v in sorted(by.items())))
    bad = by.get("pending", []) + by.get("unverified", [])
    for c in bad:
        print(f"  {c['status'].upper()} {c['id']}: {c['text'][:110]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
