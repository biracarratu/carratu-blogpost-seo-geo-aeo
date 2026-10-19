#!/usr/bin/env python3
"""Checagem SEO/GEO/AEO de um blogpost em Markdown (Metodologia Carratu).

Uso:
  python3 lint_post.py post.md [--profile perfil.json] [--top3 top3.json]
                       [--manual manual.json] [--out checks.json] [--today AAAA-MM-DD]

Saída: JSON com cada check (status, evidência), notas 0-100 por pilar, confiança,
índice geral, críticos em falha e lista pending_for_claude. Só biblioteca padrão.
Copyright (c) 2026 Ubirajara Carratu, Carratu Digital. PolyForm Noncommercial 1.0.0.
"""
import argparse
import datetime as dt
import json
import re
import statistics
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

SKILL_DIR = Path(__file__).resolve().parent.parent
RUBRIC = SKILL_DIR / "references" / "rubric.json"

STOP = set("""a o as os um uma uns umas de da do das dos em na no nas nos por para pra com sem sob sobre
e ou que se ao aos à às é ser como mais menos seu sua seus suas the of to and for in on with""".split())

TRANSITIONS = [
    "além disso", "ainda assim", "por isso", "portanto", "porém", "contudo", "no entanto", "entretanto",
    "assim", "dessa forma", "desse modo", "por exemplo", "ou seja", "isto é", "em resumo", "em suma",
    "por fim", "primeiro", "segundo", "terceiro", "depois", "em seguida", "antes de", "enquanto",
    "também", "logo", "então", "afinal", "mas", "porque", "pois", "já que", "visto que", "embora",
    "apesar de", "mesmo assim", "da mesma forma", "do mesmo modo", "em contrapartida", "por outro lado",
    "sobretudo", "principalmente", "inclusive", "ou melhor", "em outras palavras", "na prática",
    "como resultado", "consequentemente", "finalmente", "a seguir", "nesse sentido", "nesse caso",
    "acima de tudo", "em primeiro lugar", "em segundo lugar", "por último", "em conclusão", "ainda",
    "however", "therefore", "for example", "also", "because", "first", "finally", "in addition",
]
TRANSITIONS_EN = [
    "however", "therefore", "for example", "for instance", "also", "because", "first", "second", "finally",
    "in addition", "moreover", "as a result", "in other words", "on the other hand", "meanwhile", "then",
    "so", "but", "although", "even though", "in short", "in summary", "next", "after that", "instead",
    "that said", "in practice", "specifically", "ultimately", "consequently", "similarly", "likewise",
]
VAGUE_OPENERS = {"isso", "isto", "ele", "ela", "eles", "elas", "esse", "essa", "este", "esta", "aquilo",
                 "esses", "essas", "estes", "estas", "it", "this", "they"}
GENERIC_HEADINGS = {"introducao", "conclusao", "consideracoes finais", "resumo", "introduction", "conclusion"}
NUM_RE = re.compile(
    r"(R\$\s?\d[\d.,]*|US\$\s?\d[\d.,]*|\d[\d.,]*\s?(%|por cento|mil\b|milh|bilh|x\b|vezes|dias|horas|"
    r"minutos|semanas|meses|anos|pontos|leads|empresas|usu[aá]rios|clientes)|\b(19|20)\d{2}\b)",
    re.IGNORECASE)
LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)")
HTML_IMG_RE = re.compile(r"<img[^>]*>", re.IGNORECASE)


def nohost(h: str) -> str:
    h = (h or "").lower().split(":")[0]
    return h[4:] if h.startswith("www.") else h


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9%$ ]", " ", s)).strip()


def words(s: str) -> list:
    return re.findall(r"[0-9A-Za-zÀ-ÿ%$]+(?:[-'][0-9A-Za-zÀ-ÿ]+)*", s or "")


def content_words(s: str) -> list:
    return [w for w in norm(s).split() if w not in STOP and len(w) > 1]


def strip_md(s: str) -> str:
    s = IMG_RE.sub("", s)
    s = LINK_RE.sub(r"\1", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"[*_`>#|]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def kw_match(text: str, kw: str) -> str:
    """'exact' se a palavra-chave aparece igual; 'words' se todas as palavras de conteúdo aparecem;
    'partial' se metade ou mais; '' se não."""
    if not kw:
        return ""
    t, k = norm(text), norm(kw)
    if k and re.search(r"\b" + re.escape(k) + r"\b", t):
        return "exact"
    cw = content_words(kw)
    if not cw:
        return ""
    tset = set(t.split())
    hit = sum(1 for w in cw if w in tset or any(x.startswith(w[:max(4, len(w) - 2)]) for x in tset))
    if hit == len(cw):
        return "words"
    if hit / len(cw) >= 0.5:
        return "partial"
    return ""


# ---------------------------------------------------------------- parsing

def parse_frontmatter(raw: str):
    meta = {}
    if not raw.startswith("---"):
        return meta, raw
    end = raw.find("\n---", 3)
    if end == -1:
        return meta, raw
    block, body = raw[3:end], raw[end + 4:]
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line.strip())
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if v.startswith("["):
            try:
                v = json.loads(v)
            except Exception:
                v = [x.strip().strip("\"'") for x in v.strip("[]").split(",") if x.strip()]
        else:
            v = v.strip("\"'")
        meta[k] = v
    return meta, body.lstrip("\n")


def parse_body(body: str):
    """Devolve lista de blocos: {type: heading|para|list|table|quote|code|html, level, text, lines}."""
    blocks, buf, btype = [], [], None
    in_code = False

    def flush():
        nonlocal buf, btype
        if buf:
            blocks.append({"type": btype, "text": "\n".join(buf), "lines": list(buf)})
        buf, btype = [], None

    for line in body.splitlines():
        if line.strip().startswith("```"):
            if in_code:
                buf.append(line)
                flush()
                in_code = False
            else:
                flush()
                in_code, btype, buf = True, "code", [line]
            continue
        if in_code:
            buf.append(line)
            continue
        s = line.strip()
        if not s:
            flush()
            continue
        h = re.match(r"^(#{1,6})\s+(.*?)\s*#*$", s)
        if h:
            flush()
            blocks.append({"type": "heading", "level": len(h.group(1)), "text": h.group(2).strip(), "lines": [s]})
            continue
        if re.match(r"^([-*+]|\d+[.)])\s+", s):
            t = "list"
        elif s.startswith("|"):
            t = "table"
        elif s.startswith(">"):
            t = "quote"
        elif re.match(r"^<(details|summary|figure|div|table|ul|ol|p|img|section)", s, re.I):
            t = "html"
        else:
            t = "para"
        if btype and btype != t and not (btype == "list" and t == "para" and line.startswith("  ")):
            flush()
        btype = btype or t
        buf.append(line)
    flush()
    return blocks


def sections(blocks):
    """Agrupa blocos por H2. Cada seção: {title, blocks}."""
    secs, cur = [], None
    for b in blocks:
        if b["type"] == "heading" and b["level"] <= 2:
            if b["level"] == 2:
                cur = {"title": b["text"], "blocks": []}
                secs.append(cur)
            continue
        if cur is not None:
            cur["blocks"].append(b)
    return secs


def sentences(text: str) -> list:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ú0-9\"“(])", text)
    return [p for p in parts if len(words(p)) >= 3]


# ---------------------------------------------------------------- checks

def st(status, evidence, **extra):
    d = {"status": status, "evidence": evidence}
    d.update(extra)
    return d


def run_checks(meta, body, profile, top3, today):
    R = {}
    blocks = parse_body(body)
    kw = meta.get("keyword", "") or ""
    secondary = meta.get("secondary_keywords") or []
    if isinstance(secondary, str):
        secondary = [x.strip() for x in secondary.split(",") if x.strip()]
    estilo = profile.get("estilo", {}) if profile else {}
    lang = (meta.get("lang") or (profile or {}).get("idioma") or "pt-BR").lower()
    transitions = TRANSITIONS_EN if lang.startswith("en") else TRANSITIONS
    internal_domains = [nohost(d) for d in (profile or {}).get("dominios_internos", [])]

    headings = [b for b in blocks if b["type"] == "heading"]
    h1s = [b for b in headings if b["level"] == 1]
    text_blocks = [b for b in blocks if b["type"] in ("para", "list", "table", "quote", "html")]
    full_text = strip_md("\n".join(b["text"] for b in text_blocks))
    all_words = words(full_text)
    n_words = len(all_words)
    secs = sections(blocks)

    def is_meta_sec(title):
        t = norm(title)
        return any(x in t for x in ("perguntas frequentes", "faq", "fontes", "referencias", "sources"))

    # ---- SEO
    R["seo.single_h1"] = st("pass" if len(h1s) == 1 else "fail", f"{len(h1s)} H1 no corpo.")

    t = meta.get("seo_title", "")
    L = len(t)
    R["seo.title_length"] = st("fail" if not t else "pass" if 50 <= L <= 60 else "warn" if 45 <= L <= 65 else "fail",
                               f"seo_title com {L} caracteres: \"{t}\"" if t else "seo_title ausente no frontmatter.")
    m = kw_match(t, kw)
    R["seo.title_keyword"] = st("unknown" if not kw else "pass" if m in ("exact", "words") else "warn" if m == "partial" else "fail",
                                f"Correspondência no title: {m or 'nenhuma'}." if kw else "Sem keyword no frontmatter.")
    d = meta.get("meta_description", "")
    L = len(d)
    R["seo.meta_description"] = st("fail" if not d else "pass" if 140 <= L <= 160 else "warn" if 120 <= L <= 170 else "fail",
                                   f"Meta description com {L} caracteres." if d else "meta_description ausente.")
    h1 = h1s[0]["text"] if h1s else meta.get("title", "")
    m = kw_match(h1, kw)
    R["seo.h1_keyword"] = st("unknown" if not kw else "pass" if m in ("exact", "words") else "warn" if m == "partial" else "fail",
                             f"H1 \"{h1}\": correspondência {m or 'nenhuma'}.")

    slug = meta.get("slug", "")
    issues = []
    if not slug:
        issues.append("ausente")
    else:
        parts = slug.split("-")
        if not re.fullmatch(r"[a-z0-9-]+", slug):
            issues.append("caracteres fora de a-z0-9-")
        if len(parts) > 6:
            issues.append(f"{len(parts)} palavras")
        sw = [p for p in parts if p in STOP]
        if sw:
            issues.append("stopwords: " + ",".join(sw))
        if re.search(r"\b(19|20)\d{2}\b", slug.replace("-", " ")):
            issues.append("contém ano")
    R["seo.slug"] = st("pass" if not issues else "warn" if len(issues) == 1 and slug else "fail",
                       f"Slug \"{slug}\"" + (": " + "; ".join(issues) if issues else " ok."))

    # primeiro texto após H1
    after_h1 = []
    seen_h1 = False
    for b in blocks:
        if b["type"] == "heading" and b["level"] == 1:
            seen_h1 = True
            continue
        if seen_h1 or not h1s:
            if b["type"] in ("para", "list", "quote", "html", "table"):
                after_h1.append(strip_md(b["text"]))
    first100 = " ".join(" ".join(after_h1).split()[:100])
    m = kw_match(first100, kw)
    R["seo.keyword_early"] = st("unknown" if not kw else "pass" if m in ("exact", "words") else "warn" if m == "partial" else "fail",
                                f"Primeiras 100 palavras: correspondência {m or 'nenhuma'}.")

    if kw and n_words:
        occ = len(re.findall(r"\b" + re.escape(norm(kw)) + r"\b", norm(full_text)))
        dens = occ * len(norm(kw).split()) / n_words * 100
        R["seo.keyword_stuffing"] = st("pass" if dens <= 2.5 else "warn" if dens <= 3.5 else "fail",
                                       f"Palavra-chave exata {occ}x, densidade {dens:.1f}%.")
    else:
        R["seo.keyword_stuffing"] = st("unknown", "Sem keyword ou texto.")

    if secondary:
        hits = [s for s in secondary if kw_match(full_text, s) in ("exact", "words")]
        r = len(hits) / len(secondary)
        R["seo.secondary_coverage"] = st("pass" if r >= 0.6 else "warn" if r >= 0.3 else "fail",
                                         f"{len(hits)} de {len(secondary)} secundárias presentes."
                                         + (" Faltam: " + ", ".join(s for s in secondary if s not in hits)[:300]
                                            if len(hits) < len(secondary) else ""))
    else:
        R["seo.secondary_coverage"] = st("na", "Sem secondary_keywords no frontmatter.")

    h2s = [b for b in headings if b["level"] == 2]
    orphan_h3 = False
    seen_h2 = False
    for b in headings:
        if b["level"] == 2:
            seen_h2 = True
        if b["level"] >= 3 and not seen_h2:
            orphan_h3 = True
    generic = [b["text"] for b in h2s if norm(b["text"]) in GENERIC_HEADINGS]
    probs = []
    if len(h2s) < 3:
        probs.append(f"só {len(h2s)} H2")
    if orphan_h3:
        probs.append("H3 antes de qualquer H2")
    if generic:
        probs.append("H2 genérico: " + ", ".join(generic))
    R["seo.heading_structure"] = st("pass" if not probs else "warn" if len(probs) == 1 else "fail",
                                    f"{len(h2s)} H2, {len([b for b in headings if b['level'] == 3])} H3"
                                    + ("; " + "; ".join(probs) if probs else "."))

    links = LINK_RE.findall(body)
    links += [(t2, u) for u, t2 in re.findall(r"<a\s[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", body, re.I)]
    internal, external, bad_anchor = [], [], []
    for anchor, url in links:
        host = nohost(urlparse(url).netloc)
        is_int = (not host and not url.startswith("#") and not url.startswith("mailto")) or \
            any(host == d or host.endswith("." + d) for d in internal_domains)
        (internal if is_int else external).append((anchor, url))
        if norm(anchor) in ("clique aqui", "aqui", "saiba mais", "leia mais", "link", "veja"):
            bad_anchor.append(anchor)
    min_int = int(estilo.get("links_internos_min", 3) or 3)
    ni = len(internal)
    if not internal_domains:
        R["seo.internal_links"] = st("unknown", f"{ni} links relativos; sem dominios_internos no perfil para classificar absolutos.")
    else:
        R["seo.internal_links"] = st("pass" if ni >= min_int and not bad_anchor else "warn" if ni >= max(1, min_int // 2) else "fail",
                                     f"{ni} links internos (mínimo do perfil: {min_int})"
                                     + (f"; âncoras fracas: {bad_anchor}" if bad_anchor else "."))
    ext_domains = sorted({nohost(urlparse(u).netloc) for _, u in external if urlparse(u).netloc})
    R["seo.external_links"] = st("pass" if len(ext_domains) >= 2 else "warn" if len(ext_domains) == 1 else "fail",
                                 f"{len(ext_domains)} domínios externos: {', '.join(ext_domains[:8])}")

    imgs = IMG_RE.findall(body)
    html_imgs = HTML_IMG_RE.findall(body)
    no_alt = [u for a, u in imgs if not a.strip()] + [i for i in html_imgs if not re.search(r'alt="[^"]+"', i)]
    fm_alt = bool(meta.get("image_alt"))
    if fm_alt and not no_alt:
        R["seo.image_alt"] = st("pass", "image_alt no frontmatter" + (f"; {len(imgs) + len(html_imgs)} imagens no corpo, todas com alt." if imgs or html_imgs else "; sem imagens no corpo."))
    elif fm_alt or (imgs or html_imgs):
        R["seo.image_alt"] = st("warn", f"image_alt no frontmatter: {'sim' if fm_alt else 'não'}; imagens sem alt: {len(no_alt)}.")
    else:
        R["seo.image_alt"] = st("fail", "Sem image_alt no frontmatter e sem imagens no corpo.")

    med = (top3 or {}).get("aggregate", {}).get("median_words")
    if med:
        r = n_words / med
        R["seo.length_vs_top3"] = st("pass" if 0.8 <= r <= 1.3 else "warn" if 0.6 <= r <= 1.6 else "fail",
                                     f"{n_words} palavras vs mediana do top 3 {med} ({r:.0%}).")
    else:
        R["seo.length_vs_top3"] = st("na", f"{n_words} palavras; sem top3.json para comparar.")

    paras = [strip_md(b["text"]) for b in blocks if b["type"] == "para"]
    sents = [s for p in paras for s in sentences(p)]
    if sents:
        avg = statistics.mean(len(words(s)) for s in sents)
        long_p = [p for p in paras if len(words(p)) > 90 or len(sentences(p)) > 4]
        ok_p = 1 - len(long_p) / max(1, len(paras))
        trans = sum(1 for s in sents if any(re.search(r"\b" + re.escape(norm(tw)) + r"\b", norm(s)) for tw in transitions))
        tr = trans / len(sents)
        score = sum([avg <= 22, ok_p >= 0.8, tr >= 0.25])
        R["seo.readability"] = st("pass" if score == 3 else "warn" if score == 2 else "fail",
                                  f"Frase média {avg:.1f} palavras; {ok_p:.0%} dos parágrafos curtos; "
                                  f"{tr:.0%} das frases com transição.",
                                  metrics={"avg_sentence_words": round(avg, 1), "short_paragraph_ratio": round(ok_p, 2),
                                           "transition_ratio": round(tr, 2)})
    else:
        R["seo.readability"] = st("unknown", "Sem parágrafos para medir.")

    # ---- GEO
    first_para = after_h1[0] if after_h1 else ""
    fw = len(words(first_para))
    m = kw_match(first_para, kw)
    has_answer = bool(re.search(r"\b(é|são|consiste|significa|funciona|serve|permite|ajuda|depende|custa|"
                                r"deve|precisa|basta|faça|use|comece|is|are|means)\b", first_para, re.I))
    filler = bool(re.search(r"\b(neste (artigo|post|texto|conteúdo)|nesse (artigo|post)|vamos (falar|explicar|ver|mostrar)|"
                            r"você vai (aprender|descobrir|ver)|in this (article|post))\b", first_para, re.I))
    pts = sum([30 <= fw <= 80, m in ("exact", "words") or not kw, has_answer]) - (1 if filler else 0)
    R["geo.answer_first"] = st("pass" if pts == 3 else "warn" if pts == 2 else "fail",
                               f"1º parágrafo com {fw} palavras; keyword: {m or 'nenhuma'}; resposta/definição: "
                               f"{'sim' if has_answer else 'não'}" + ("; abre com anúncio do artigo" if filler else "")
                               + f". Trecho: \"{first_para[:160]}\"")

    body_secs = [s for s in secs if not is_meta_sec(s["title"])]
    sizes = [len(words(strip_md("\n".join(b["text"] for b in s["blocks"])))) for s in body_secs]
    if sizes:
        good = sum(1 for x in sizes if 100 <= x <= 350) / len(sizes)
        tiny = [s["title"] for s, x in zip(body_secs, sizes) if x < 50]
        R["geo.passages"] = st("pass" if good >= 0.6 and not tiny else "warn" if good >= 0.4 else "fail",
                               f"{len(sizes)} seções H2; {good:.0%} entre 100 e 350 palavras; tamanhos {sizes}"
                               + (f"; curtas demais: {tiny}" if tiny else "."))
    else:
        R["geo.passages"] = st("fail", "Nenhuma seção H2 de conteúdo.")

    vague = []
    for s in body_secs:
        fp = next((strip_md(b["text"]) for b in s["blocks"] if b["type"] == "para"), "")
        w0 = norm(fp).split()[:1]
        if w0 and w0[0] in VAGUE_OPENERS:
            vague.append(s["title"])
    R["geo.no_vague_openers"] = st("pass" if not vague else "warn" if len(vague) == 1 else "fail",
                                   "Nenhuma seção abre com pronome solto." if not vague else f"Abrem com pronome: {vague}")

    nums = NUM_RE.findall(full_text)
    need = max(1.0, n_words / 250)
    r = len(nums) / need
    R["geo.evidence_density"] = st("pass" if r >= 1 else "warn" if r >= 0.5 else "fail",
                                   f"{len(nums)} dados numéricos em {n_words} palavras (alvo ≥ {need:.0f}).")

    src_sec = next((s for s in secs if re.search(r"fontes|refer[eê]ncias|sources", norm(s["title"]))), None)
    src_links = len(LINK_RE.findall("\n".join(b["text"] for b in src_sec["blocks"]))) if src_sec else 0
    if src_sec and src_links:
        R["geo.sources_section"] = st("pass", f"Seção \"{src_sec['title']}\" com {src_links} links.")
    elif len(ext_domains) >= 2:
        R["geo.sources_section"] = st("warn", "Sem seção de fontes, mas há links externos inline.")
    else:
        R["geo.sources_section"] = st("fail", "Sem seção de fontes e quase sem links externos.")

    quote_blocks = [b for b in blocks if b["type"] == "quote"]
    attrib = re.findall(r"\b(?i:segundo|de acordo com|conforme|afirma|explica|diz|according to)\s+[A-ZÀ-Ú][\wÀ-ÿ]+",
                        strip_md(body))
    first_person = re.findall(r"\b(na nossa experi[eê]ncia|em nossos projetos|nos nossos clientes|atendemos|"
                              r"acompanhamos|testamos|medimos|vimos em|na minha experi[eê]ncia|eu vi|aprendi)\b",
                              full_text, re.I)
    sig = len(quote_blocks) + len(attrib) + len(first_person)
    R["geo.expert_signal"] = st("pass" if sig >= 1 else "fail",
                                f"{len(quote_blocks)} citações em bloco, {len(attrib)} atribuições, "
                                f"{len(first_person)} marcas de experiência própria.")

    author = meta.get("author", "")
    R["geo.author_eeat"] = st("pass" if author and re.search(r"[(,–-]", author) else "warn" if author else "fail",
                              f"Autor: \"{author}\"" if author else "author ausente.")

    date_s = meta.get("updated") or meta.get("date") or ""
    yr = today.year
    years_in = set(int(y) for y in re.findall(r"\b(20\d{2})\b", full_text))
    try:
        dval = dt.date.fromisoformat(str(date_s)[:10])
        age = (today - dval).days
        ok_date = age <= 120
    except Exception:
        dval, ok_date = None, False
    recent_mention = bool(years_in & {yr, yr - 1})
    R["geo.freshness"] = st("pass" if ok_date and recent_mention else "warn" if dval else "fail",
                            f"Data: {date_s or 'ausente'}; anos citados no texto: {sorted(years_in) or 'nenhum'}.")

    # ---- AEO
    kwc = content_words(kw)
    defn = None
    for s in sentences(full_text):
        if re.search(r"\b(é|são)\s+(um|uma|o|a|os|as)\b|\bconsiste em\b|\bsignifica\b|\bis an?\b", s, re.I):
            if not kwc or any(w in norm(s) for w in kwc):
                defn = s
                break
    generic_def = re.search(r"\b(é|são)\s+(um|uma)\b", full_text, re.I)
    R["aeo.definition"] = st("pass" if defn else "warn" if generic_def else "fail",
                             f"Definição: \"{defn[:160]}\"" if defn else "Sem frase de definição do tema principal.")

    faq_sec = next((s for s in secs if re.search(r"perguntas frequentes|\bfaq\b|duvidas frequentes", norm(s["title"]))), None)
    details_q = re.findall(r"<summary>(.*?)</summary>", body, re.I | re.S)
    if faq_sec or details_q:
        qs, answers = [], []
        if faq_sec:
            cur = None
            for b in faq_sec["blocks"]:
                if b["type"] == "heading" and b["level"] >= 3:
                    cur = {"q": b["text"], "a": ""}
                    qs.append(cur)
                elif cur is not None and b["type"] in ("para", "list"):
                    cur["a"] += " " + strip_md(b["text"])
            answers = [len(words(q["a"])) for q in qs]
        nq = len(qs) or len(details_q)
        avg_a = statistics.mean(answers) if answers else None
        ok = 3 <= nq <= 8 and (avg_a is None or 30 <= avg_a <= 90)
        R["aeo.faq"] = st("pass" if ok else "warn",
                          f"{nq} perguntas" + (f", resposta média {avg_a:.0f} palavras." if avg_a else "."))
    else:
        R["aeo.faq"] = st("fail", "Sem seção de perguntas frequentes.")

    qh = 0
    ok_q = 0
    for i, b in enumerate(blocks):
        if b["type"] == "heading" and b["level"] >= 2 and b["text"].strip().endswith("?"):
            qh += 1
            nxt = next((x for x in blocks[i + 1:] if x["type"] != "heading" or x["level"] <= b["level"]), None)
            if nxt and nxt["type"] == "para" and 12 <= len(words(strip_md(nxt["text"]))) <= 70:
                ok_q += 1
    if qh:
        r = ok_q / qh
        R["aeo.direct_answers"] = st("pass" if r >= 0.8 else "warn" if r >= 0.5 else "fail",
                                     f"{ok_q} de {qh} headings em pergunta seguidos de resposta de 12 a 70 palavras.")
    else:
        R["aeo.direct_answers"] = st("na", "Nenhum heading em pergunta.")

    lists = [b for b in blocks if b["type"] == "list"]
    tables = [b for b in blocks if b["type"] == "table" and re.search(r"\|\s*:?-{3,}", b["text"])]
    R["aeo.lists_tables"] = st("pass" if lists or tables else "fail", f"{len(lists)} listas, {len(tables)} tabelas.")

    # ---- Estilo
    em = body.count("—") + len(re.findall(r"\s–\s", body)) + sum(str(v).count("—") for v in meta.values())
    if estilo.get("proibir_travessao", True):
        R["style.em_dash"] = st("pass" if em == 0 else "fail", f"{em} travessões encontrados.")
    else:
        R["style.em_dash"] = st("na", f"Perfil permite travessão ({em} no texto).")
    forb = [t2 for t2 in estilo.get("termos_proibidos", []) if norm(t2) and norm(t2) in norm(full_text)]
    R["style.forbidden_terms"] = st("pass" if not forb else "warn" if len(forb) == 1 else "fail",
                                    "Nenhum termo proibido." if not forb else f"Termos proibidos: {forb}")
    cta = (profile or {}).get("cta", {})
    keys = [k for k in (cta.get("palavras_chave") or []) if k] + ([cta["url"]] if cta.get("url") else [])
    if not keys:
        R["style.cta"] = st("unknown", "Perfil sem CTA definido (url ou palavras_chave).")
    else:
        tail = body[int(len(body) * 0.7):]
        if any(norm(k) in norm(tail) or k in tail for k in keys):
            R["style.cta"] = st("pass", "CTA do perfil no trecho final.")
        elif any(norm(k) in norm(body) or k in body for k in keys):
            R["style.cta"] = st("warn", "CTA aparece, mas não no fechamento.")
        else:
            R["style.cta"] = st("fail", f"CTA do perfil ausente (procurado: {keys}).")

    stats = {"words": n_words, "h2": len(h2s), "internal_links": ni, "external_domains": len(ext_domains),
             "numbers": len(nums), "em_dash": em}
    return R, stats


# ---------------------------------------------------------------- score

def score(results, rubric):
    lv = rubric["evidence_levels"]
    sc = rubric["scale"]
    dims = {}
    for c in rubric["checks"]:
        r = results.get(c["id"])
        if c["dim"] == "style":
            continue
        dd = dims.setdefault(c["dim"], {"got": 0.0, "eval": 0.0, "total": 0.0})
        w = lv[c["ev"]]
        status = r["status"] if r else "pending"
        if status == "na":
            continue
        dd["total"] += w
        if status in sc:
            dd["eval"] += w
            dd["got"] += w * sc[status]
    out = {}
    for d, v in dims.items():
        out[d] = {"score": round(100 * v["got"] / v["eval"]) if v["eval"] else None,
                  "confidence": round(100 * v["eval"] / v["total"]) if v["total"] else None}
    wsum = sum(rubric["dimension_weights"][d] for d in out if out[d]["score"] is not None)
    overall = round(sum(rubric["dimension_weights"][d] * out[d]["score"] for d in out if out[d]["score"] is not None) / wsum) if wsum else None
    return out, overall


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("post")
    ap.add_argument("--profile")
    ap.add_argument("--top3")
    ap.add_argument("--manual", help="JSON com lista de {id, status, evidence} dos checks manuais")
    ap.add_argument("--claims", help="claims.json preenchido (fact-check); alimenta geo.data_accuracy")
    ap.add_argument("--review", help="review.json do revisor independente; alimenta os checks manuais")
    ap.add_argument("--out")
    ap.add_argument("--today")
    a = ap.parse_args()

    raw = Path(a.post).read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    profile = json.loads(Path(a.profile).read_text(encoding="utf-8")) if a.profile else {}
    top3 = json.loads(Path(a.top3).read_text(encoding="utf-8")) if a.top3 and Path(a.top3).exists() else {}
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    rubric = json.loads(RUBRIC.read_text(encoding="utf-8"))

    results, stats = run_checks(meta, body, profile, top3, today)
    if a.claims and Path(a.claims).exists():
        cl = json.loads(Path(a.claims).read_text(encoding="utf-8")).get("claims", [])
        pend = [c for c in cl if c.get("status") in ("pending", "unverified")]
        nosrc = [c for c in cl if c.get("status") == "verified" and not c.get("source_url") and not c.get("quote")]
        if not cl:
            results["geo.data_accuracy"] = st("warn", "claims.json vazio: nenhum dado numérico detectado para verificar.", source="claims")
        elif pend:
            results["geo.data_accuracy"] = st("fail", f"{len(pend)} de {len(cl)} afirmações não verificadas: "
                                              + "; ".join(c["id"] + " " + c["text"][:60] for c in pend[:4]), source="claims")
        elif nosrc:
            results["geo.data_accuracy"] = st("warn", f"{len(nosrc)} afirmações 'verified' sem URL nem trecho da fonte.", source="claims")
        else:
            cd = sum(1 for c in cl if c.get("status") == "client_data")
            results["geo.data_accuracy"] = st("pass", f"{len(cl)} afirmações verificadas contra a fonte"
                                              + (f" ({cd} dados do cliente, marcados)." if cd else "."), source="claims")
    if a.review and Path(a.review).exists():
        rv = json.loads(Path(a.review).read_text(encoding="utf-8"))
        for item in rv.get("checks", []):
            results[item["id"]] = st(item["status"], "[revisor] " + item.get("evidence", ""), source="review")
    if a.manual:
        for item in json.loads(Path(a.manual).read_text(encoding="utf-8")):
            results[item["id"]] = st(item["status"], item.get("evidence", ""), source="manual")

    by_id = {c["id"]: c for c in rubric["checks"]}
    pending = [c["id"] for c in rubric["checks"] if c["id"] not in results]
    dims, overall = score(results, rubric)
    critical_fail = [i for i, r in results.items() if by_id.get(i, {}).get("critical") and r["status"] in ("fail", "warn")]
    critical_pending = [i for i in pending if by_id[i].get("critical")]

    report = {
        "post": a.post, "keyword": meta.get("keyword"), "stats": stats,
        "scores": dims, "overall": overall,
        "ready": not critical_fail and not critical_pending and (overall or 0) >= 80,
        "critical_fail": critical_fail, "pending_for_claude": pending,
        "checks": {i: {**results[i], "label": by_id.get(i, {}).get("label", i), "dim": by_id.get(i, {}).get("dim")}
                   for i in results},
    }
    out = json.dumps(report, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(out, encoding="utf-8")

    # resumo legível
    print(f"\n{meta.get('title', a.post)}  ({stats['words']} palavras)")
    for d in ("seo", "geo", "aeo"):
        v = dims.get(d, {})
        print(f"  {d.upper()}: {v.get('score')}  (confiança {v.get('confidence')}%)")
    print(f"  GERAL: {overall}")
    icon = {"pass": "OK ", "warn": "~  ", "fail": "X  ", "na": "-  ", "unknown": "?  "}
    for c in rubric["checks"]:
        r = results.get(c["id"])
        if r and r["status"] in ("fail", "warn"):
            crit = " [CRÍTICO]" if c.get("critical") else ""
            print(f"  {icon[r['status']]}{c['id']}{crit}: {r['evidence']}")
    if pending:
        print(f"  Pendentes (avaliar com --manual): {', '.join(pending)}")
    print(f"  Pronto para entregar: {'SIM' if report['ready'] else 'NÃO'}"
          + (f" (críticos fora de pass: {', '.join(critical_fail)})" if critical_fail else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
