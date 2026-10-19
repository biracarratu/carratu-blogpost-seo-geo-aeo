// Coletor do top 3 pelo navegador (Claude in Chrome ou navegador integrado), quando a rede do ambiente bloqueia
// a coleta direta. Uso: abra QUALQUER aba (ex.: a busca do Google da palavra-chave), execute este arquivo inteiro
// com a ferramenta de JavaScript, trocando CONFIG.urls pelas URLs do top 3. Ele faz fetch de cada URL (cross-origin
// costuma falhar: nesse caso use CONFIG.mode = "tabs", abrindo cada URL numa aba e rodando com mode "current").
// Salve a saída em post_data/serp/<n>.html (campo html de cada item) ou passe o JSON inteiro para
// serp_extract.py com --from-json.
//   CONFIG = {mode: "fetch", urls: ["https://...", "https://...", "https://..."]}
//   CONFIG = {mode: "current"}  -> devolve o HTML da aba atual (rode uma vez por URL do top 3)
(async () => {
  const CONFIG = { mode: "current", urls: [] }; // <- EDITAR
  const clean = (html) => html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, (m) => /ld\+json/i.test(m) ? m : "")
                              .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, "").slice(0, 900000);
  if (CONFIG.mode === "current") {
    return JSON.stringify({ pages: [{ url: location.href, status: 200, html: clean(document.documentElement.outerHTML) }] });
  }
  const out = [];
  for (const u of CONFIG.urls) {
    try {
      const r = await fetch(u, { redirect: "follow", credentials: "omit" });
      out.push({ url: r.url, status: r.status, html: clean(await r.text()) });
    } catch (e) {
      out.push({ url: u, status: null, html: "", error: String(e).slice(0, 200) + " (abra a URL numa aba e use mode: current)" });
    }
  }
  return JSON.stringify({ pages: out });
})();
