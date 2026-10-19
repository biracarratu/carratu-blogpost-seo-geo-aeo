#!/usr/bin/env python3
"""Converte o post .md (com frontmatter) nos arquivos que a publicação consome.

Uso:
  python3 md_to_wp.py outputs/<slug>.md --out-dir outputs [--site https://blog.site.com.br] [--logo URL]
Gera:
  <slug>.html        HTML de blocos do WordPress (com comentários <!-- wp:... -->), pronto para `content`
  <slug>.jsonld      JSON-LD Article + BreadcrumbList (autor, datas, imagem)
  <slug>.wp.json     payload para POST wp/v2/posts (title, slug, excerpt, content, meta do Yoast, status draft)
  <slug>.plain.html  HTML limpo sem comentários de bloco (HubSpot, outros CMS)
Só biblioteca padrão. Copyright (c) 2026 Ubirajara Carratu, Carratu Digital. PolyForm Noncommercial 1.0.0.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_post import parse_body, parse_frontmatter  # noqa: E402


def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1"/>', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+&quot;[^&]*&quot;)?\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", s)
    s = re.sub(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def wp(block_name, inner, attrs=None):
    a = (" " + json.dumps(attrs, ensure_ascii=False)) if attrs else ""
    return f"<!-- wp:{block_name}{a} -->\n{inner}\n<!-- /wp:{block_name} -->"


def render(blocks, drop_h1=True):
    out = []
    for b in blocks:
        t = b["type"]
        if t == "heading":
            if b["level"] == 1 and drop_h1:
                continue
            lvl = b["level"]
            out.append(wp("heading", f"<h{lvl} class=\"wp-block-heading\">{inline(b['text'])}</h{lvl}>",
                          {"level": lvl} if lvl != 2 else None))
        elif t == "para":
            text = " ".join(l.strip() for l in b["lines"])
            m = re.fullmatch(r"!\[([^\]]*)\]\(([^)\s]+)\)", text.strip())
            if m:
                out.append(wp("image", f'<figure class="wp-block-image size-large"><img src="{m.group(2)}" alt="{html.escape(m.group(1))}"/></figure>',
                              {"sizeSlug": "large"}))
            else:
                out.append(wp("paragraph", f"<p>{inline(text)}</p>"))
        elif t == "list":
            ordered = bool(re.match(r"^\s*\d+[.)]", b["lines"][0]))
            items = []
            for l in b["lines"]:
                m = re.match(r"^\s*([-*+]|\d+[.)])\s+(.*)", l)
                if m:
                    items.append(f"<li>{inline(m.group(2))}</li>")
                elif items:
                    items[-1] = items[-1][:-5] + " " + inline(l.strip()) + "</li>"
            tag = "ol" if ordered else "ul"
            out.append(wp("list", f"<{tag} class=\"wp-block-list\">" + "".join(items) + f"</{tag}>",
                          {"ordered": True} if ordered else None))
        elif t == "table":
            rows = [l.strip().strip("|").split("|") for l in b["lines"] if l.strip() and not re.match(r"^\|?\s*:?-{3,}", l.strip())]
            if not rows:
                continue
            head = "<thead><tr>" + "".join(f"<th>{inline(c.strip())}</th>" for c in rows[0]) + "</tr></thead>"
            body = "<tbody>" + "".join("<tr>" + "".join(f"<td>{inline(c.strip())}</td>" for c in r) + "</tr>" for r in rows[1:]) + "</tbody>"
            out.append(wp("table", f'<figure class="wp-block-table"><table>{head}{body}</table></figure>'))
        elif t == "quote":
            text = " ".join(re.sub(r"^>\s?", "", l.strip()) for l in b["lines"])
            out.append(wp("quote", f'<blockquote class="wp-block-quote"><p>{inline(text)}</p></blockquote>'))
        elif t == "code":
            code = "\n".join(b["lines"][1:-1])
            out.append(wp("code", f"<pre class=\"wp-block-code\"><code>{html.escape(code)}</code></pre>"))
        elif t == "html":
            out.append(wp("html", "\n".join(b["lines"])))
    return "\n\n".join(out)


def jsonld(meta, site, logo, url):
    org = meta.get("publisher") or meta.get("blog") or ""
    author = meta.get("author", "")
    name = re.split(r"\s*[(,–-]\s*", author)[0] if author else ""
    role = author[len(name):].strip(" (),–-") if author else ""
    art = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": meta.get("title", "")[:110], "description": meta.get("meta_description", ""),
        "inLanguage": meta.get("lang", "pt-BR"),
        "datePublished": meta.get("date"), "dateModified": meta.get("updated") or meta.get("date"),
        "author": {"@type": "Person", "name": name, **({"jobTitle": role} if role else {}),
                   **({"url": meta["author_url"]} if meta.get("author_url") else {})},
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "keywords": ", ".join([meta.get("keyword", "")] + list(meta.get("secondary_keywords") or [])),
    }
    if meta.get("image"):
        art["image"] = [meta["image"]]
    if org:
        art["publisher"] = {"@type": "Organization", "name": org, **({"logo": {"@type": "ImageObject", "url": logo}} if logo else {})}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Blog", "item": site or ""},
        {"@type": "ListItem", "position": 2, "name": meta.get("title", ""), "item": url}]}
    return [art, crumbs]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("post")
    ap.add_argument("--out-dir", default="outputs")
    ap.add_argument("--site", default="")
    ap.add_argument("--logo", default="")
    ap.add_argument("--status", default="draft")
    a = ap.parse_args()
    raw = Path(a.post).read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    blocks = parse_body(body)
    slug = meta.get("slug") or Path(a.post).stem
    url = f"{a.site.rstrip('/')}/{slug}/" if a.site else f"/{slug}/"
    content = render(blocks)
    plain = re.sub(r"<!--\s*/?wp:[^>]*-->\n?", "", content)
    ld = jsonld(meta, a.site, a.logo, url)
    payload = {
        "title": meta.get("title", ""), "slug": slug, "status": a.status,
        "excerpt": meta.get("excerpt", "") or meta.get("meta_description", ""),
        "content": content,
        "meta": {"_yoast_wpseo_focuskw": meta.get("keyword", ""), "_yoast_wpseo_title": meta.get("seo_title", ""),
                 "_yoast_wpseo_metadesc": meta.get("meta_description", "")},
        "_carratu": {"image_alt": meta.get("image_alt", ""), "secondary_keywords": meta.get("secondary_keywords") or [],
                     "jsonld": ld, "date": meta.get("date")},
    }
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{slug}.html").write_text(content, encoding="utf-8")
    (out / f"{slug}.plain.html").write_text(plain, encoding="utf-8")
    (out / f"{slug}.jsonld").write_text('<script type="application/ld+json">\n' + json.dumps(ld, ensure_ascii=False, indent=2) + "\n</script>\n", encoding="utf-8")
    (out / f"{slug}.wp.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    nb = content.count("<!-- wp:")
    print(f"{slug}: {nb} blocos · title {len(meta.get('seo_title', ''))} chars · meta {len(meta.get('meta_description', ''))} chars → {out}/{slug}.html, .plain.html, .jsonld, .wp.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
