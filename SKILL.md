---
name: carratu-blogpost-seo-geo-aeo
description: Pauta editorial e blogposts otimizados para SEO, GEO e AEO (Google, AI Overviews, ChatGPT, Perplexity, Gemini, Claude) com a Metodologia Carratu, por Ubirajara Carratu. Use quando pedirem para criar pauta ou calendário editorial de blog, escolher palavras-chave por intenção, escrever/redigir/produzir um artigo ou post de blog, atualizar (refresh) um post existente, conteúdo pilar, post otimizado para SEO ou para aparecer em IA, para qualquer blog ou cliente. Analisa o top 3, faz fact-check, revisão independente, entrega post com nota 0-100 e arquivos de publicação. Também em inglês (editorial calendar, SEO blog post, AI search optimized article, content refresh).
---

# Pauta e Blogpost SEO · GEO · AEO (Metodologia Carratu)

Autor: Ubirajara Carratu · Carratu Digital. Versão 1.1.0 (out/2026). Licença: PolyForm Noncommercial 1.0.0
(uso comercial exige licença; ver `NOTICE.md`). Irmã da skill de auditoria `carratu-seo-geo-aeo`: a auditoria
mede o que existe, esta planeja e escreve já passando nos mesmos critérios.

Você vai trabalhar como redator sênior que também é analista de growth: o post precisa ganhar a busca, ser
citado por motores de IA e gerar negócio para o ICP do blog. Nada de texto comoditizado que repete o top 10,
nada de número sem fonte, e quem escreve não dá a própria nota.

**Antes de tudo:** `SKILL_DIR` é a pasta deste arquivo. Trabalhe numa pasta gravável com `post_data/`,
`outputs/` e `tracking/`. Rode Python com `python3` (instale `beautifulsoup4` se faltar, com
`--break-system-packages`; `openpyxl` é opcional, para a pauta em .xlsx).

Referências (leia quando a etapa pedir, não tudo de uma vez):
- `references/evidence-2026.md`: o que a pesquisa mostra e os mitos (cópia da skill de auditoria; ver nota no fim)
- `references/pauta.md`: modo pauta (cauda, intenção, H1, H2, persona, prioridade)
- `references/serp-analysis.md`: pesquisa da palavra-chave e análise do top 3
- `references/writing-rules.md`: regras de escrita, uma por check
- `references/brief-template.md`: o brief que liga pesquisa e texto
- `references/fact-check.md`: verificação afirmação a afirmação
- `references/editor-review.md`: revisão independente por subagente
- `references/rubric.json`: checks, pesos e níveis de evidência
- `profiles/`: perfis de blog/cliente com voz, ICP, personas, CTA e regras (`_template.json` para criar)

Esta skill **não publica**. Ela entrega os arquivos que a publicação consome (WordPress, HubSpot, pipeline do
blog). Scripts em `scripts/`: `pauta_build.py`, `sitemap_links.py`, `serp_extract.py` (+ `browser_collect.js`),
`html_to_md.py`, `claims.py`, `lint_post.py`, `md_to_wp.py`, `track.py`.

---

## Três modos

| Modo | Quando | Entrada | Saída |
|---|---|---|---|
| **Pauta** | "monte a pauta", "calendário editorial", "quais palavras-chave", "30 posts para o trimestre" | perfil + universo de palavras-chave + ritmo | `pauta-<blog>-<periodo>.md/.csv/.xlsx` |
| **Post novo** | "escreva o post sobre…", uma linha da pauta | perfil + palavra-chave (+ linha da pauta) | `outputs/<slug>.md` + arquivos de publicação + checks |
| **Refresh** | "atualize este post", URL existente, ou `sitemap_links.py` apontou canibalização | URL do post | mesmo que post novo, preservando URL, links e o que já ranqueia |

Se o pedido não disser o modo, deduza: URL de post = refresh; tema sem palavra-chave fechada e mais de 3 posts =
pauta; o resto = post novo.

## Etapa 0: Briefing (uma rodada de perguntas, no máximo)

Descubra em silêncio o que existe na sessão: conector Semrush, busca na web, navegador (Claude in Chrome ou
integrado), conector do blog (WordPress, HubSpot), Search Console, ferramenta de agentes. Depois, numa única
rodada (ferramenta de múltipla escolha se houver), pulando o que o usuário já disse ou o que a linha da pauta já
traz:

1. **Blog / cliente:** qual perfil usar (liste os de `profiles/`) ou "novo".
2. **Modo e escopo:** pauta (período, quantos posts, mix por intenção), post novo (palavra-chave ou tema) ou
   refresh (URL).
3. **Fontes de dados:** só as disponíveis. "Semrush (qual o teto de unidades?)", "Search Console", "Busca na
   web", "Sitemap/posts do blog", "Material do cliente (cases, números, falas)". Nenhuma é obrigatória.
4. **Entrega:** Markdown + arquivos de publicação (padrão), documento para revisão do cliente, ou os dois.

Sem resposta: perfil mais provável, modo deduzido, fontes sem custo, entrega padrão. Diga o que assumiu.

## Etapa 1: Perfil do blog

Leia `profiles/<blog>.json`: marca, domínios internos, ICP, oferta, **personas**, voz, regras de estilo
(`proibir_travessao`, termos proibidos, mínimo de links internos), autor e credenciais, CTA, concorrentes,
exigências de publicação. Se não existir: leia home, Sobre e 3 posts, monte pelo `_template.json`, mostre em 5
linhas, salve (na pasta de trabalho se `SKILL_DIR` for só leitura). Campos "a confirmar": pergunte no briefing
e atualize. Nunca invente credenciais, números ou clientes do autor.

---

## Modo pauta

Siga `references/pauta.md`. Resumo:

1. **Universo de palavras-chave** → `post_data/keywords.csv` (`keyword,volume,kd,intent,source,cluster,aio`).
   Com Semrush (base `br`, teto do briefing): relacionadas, perguntas, lacunas frente aos concorrentes. Sem:
   Search Console (consultas com impressão em posição 11 a 30), busca na web (autocomplete, PAA, relacionadas),
   perguntas de vendas e suporte, fan-out por tema.
2. **O que já existe:** `python3 SKILL_DIR/scripts/sitemap_links.py --sitemap URL --keywords post_data/keywords.csv --out post_data/internal.json`
   → palavras já cobertas viram refresh; risco de canibalização entra na coluna `cannibal_risk`.
3. **Classificar:** `python3 SKILL_DIR/scripts/pauta_build.py post_data/keywords.csv --profile SKILL_DIR/profiles/<blog>.json --out post_data/pauta.json`
   (cauda short/medium/long, intenção informacional/navegacional/comercial/transacional, prioridade, cluster).
4. **Preencher cada linha escolhida** em `pauta.json`: `persona` (id do perfil), `h1` (40 a 70 caracteres,
   palavra-chave no primeiro terço, promessa concreta), `seo_title` (50 a 60), `h2[]` (5 a 8 subtópicos, com um
   de ganho de informação e "Perguntas frequentes"), `secondary_keywords[{keyword, intent}]`, `format`. Para
   `short` e `medium`, olhe a SERP antes de fechar intenção e formato.
5. **Validar e gerar:** `python3 SKILL_DIR/scripts/pauta_build.py post_data/pauta.json --profile ... --validate --out-dir outputs --start AAAA-MM-DD --every N --period AAAA-MM`
   Corrija o que o script apontar (tamanhos, palavra-chave no H1, H2 genéricos, persona inexistente,
   duplicidade) e regenere.
6. **Entregar** os arquivos e um resumo: linhas por intenção, cauda, persona e cluster; as 3 de maior prioridade e
   o porquê; o que virou refresh. Cada linha aprovada é o briefing pronto do modo post novo.

---

## Modo post novo (e refresh)

### Etapa 2: Pesquisa da palavra-chave
`references/serp-analysis.md`, parte 1 → `post_data/keyword.json` (intenção, secundárias, perguntas, fan-out,
AI Overview). Se veio da pauta, só confirme. **Intenção manda no formato.**

### Etapa 3: Top 3
`references/serp-analysis.md`, parte 2. Coleta pelo HTML real:
- Direto: `python3 SKILL_DIR/scripts/serp_extract.py URL1 URL2 URL3 --keyword "kw" --out post_data/top3.json`
  (saída 3 = rede bloqueada).
- Navegador: abra cada URL numa aba, rode `scripts/browser_collect.js` (`mode: "current"`) com a ferramenta de
  JavaScript, salve o JSON em `post_data/serp/N.json` e rode `serp_extract.py --from-json post_data/serp/N.json`
  (um por URL, ou junte os `pages` num JSON só).
- Sem nada: leitura de página web só para estrutura; marque no brief que a medição é aproximada.
Depois leia os textos e preencha a matriz de lacunas (obrigatório, diferencial, **ganho de informação**,
correções) e o que o AI Overview cita.

### Etapa 4: Posts existentes e material próprio
- `python3 SKILL_DIR/scripts/sitemap_links.py --sitemap URL --keyword "kw" --secondary "a,b" --out post_data/internal.json`
  → risco de canibalização (se houver, **pare e pergunte**: refresh ou outro ângulo) e candidatos a link interno
  com âncora. Sem sitemap acessível: conector do blog ou `--urls` com lista salva.
- Material do cliente: cases, números, metodologia, falas. Se não houver, proponha no brief 1 ou 2 perguntas ao
  cliente e siga.
- Fontes externas: 5 a 10 dados com fonte primária e data, preferindo os últimos 24 meses.

### Etapa 4R (só refresh)
`python3 SKILL_DIR/scripts/html_to_md.py URL --out post_data/current.md --blog <id>` → preencha `keyword` e
`secondary_keywords` no frontmatter e rode o lint nele (Etapa 7) para ter a linha de base. Regras do refresh:
manter URL, slug e os H2 que trazem tráfego (Search Console, se houver); atualizar dados e datas; adicionar o que
o top 3 cobre e o post não; cortar o que ficou velho; `updated` com a data de hoje e um parágrafo que diga o que
mudou se o tema for sensível a tempo. Entregue também um diff resumido (o que entrou, saiu, mudou).

### Etapa 5: Brief
`references/brief-template.md` → `post_data/brief.md`. Mostre resumo de 6 a 10 linhas; espere o ok se o usuário
estiver presente.

### Etapa 6: Texto
`references/writing-rules.md` → `outputs/<slug>.md` com frontmatter:

```yaml
---
title: "H1 do post"
seo_title: "Title de 50 a 60 caracteres"
meta_description: "140 a 160 caracteres com benefício e convite"
slug: "slug-curto-sem-stopwords"
keyword: "palavra-chave principal"
secondary_keywords: ["...", "..."]
author: "Nome (cargo)"
author_url: "https://site/autor/"
date: "AAAA-MM-DD"
updated: "AAAA-MM-DD"
excerpt: "1 a 2 frases"
blog: "id-do-perfil"
lang: "pt-BR"
persona: "id-da-persona"
image_alt: "alt da imagem de destaque com a palavra-chave"
---
```

Corpo: um `# H1`, bloco-resposta de 40 a 60 palavras, H2 autocontidos, listas e tabelas quando ajudam, `##
Perguntas frequentes` com `### pergunta` e resposta curta, conclusão com o CTA do perfil, `## Fontes`. Posts
longos: seção por seção a partir do brief.

### Etapa 7: Checagem em três camadas

**7a. Lint automático**
```bash
python3 SKILL_DIR/scripts/lint_post.py outputs/<slug>.md --profile SKILL_DIR/profiles/<blog>.json --top3 post_data/top3.json --out post_data/checks.json
```
Corrija tudo que estiver `fail` ou crítico em `warn` **no texto**, nunca na nota.

**7b. Fact-check** (`references/fact-check.md`)
```bash
python3 SKILL_DIR/scripts/claims.py extract outputs/<slug>.md --out post_data/claims.json
```
Abra cada fonte, preencha `status` e `quote`. Afirmação sem fonte primária sai do texto.
`python3 SKILL_DIR/scripts/claims.py status post_data/claims.json` tem que sair 0.

**7c. Revisão independente** (`references/editor-review.md`): dispare um subagente com o post, o brief, o perfil
e o `top3.json`, sem o histórico. Salve em `post_data/review.json`, aplique o `top_fix`, trate objeções e riscos.
Se a sessão não tiver agentes, revise após pausa e diga na entrega que não foi independente.

**7d. Nota final**
```bash
python3 SKILL_DIR/scripts/lint_post.py outputs/<slug>.md --profile ... --top3 ... --claims post_data/claims.json --review post_data/review.json --out post_data/checks.json
```
Meta: índice ≥ 80, confiança ≥ 90% e nenhum crítico fora de `pass`. Se mudou o texto depois do fact-check,
rode `claims.py extract` de novo.

### Etapa 8: Arquivos de publicação
```bash
python3 SKILL_DIR/scripts/md_to_wp.py outputs/<slug>.md --out-dir outputs --site https://blog.site.com.br [--logo URL]
```
Gera `<slug>.html` (blocos do WordPress), `<slug>.plain.html` (HubSpot e outros), `<slug>.jsonld` (Article +
BreadcrumbList) e `<slug>.wp.json` (payload com meta do Yoast). Quem publica é a pipeline ou o conector do blog.

### Etapa 9: Entrega e acompanhamento
Entregue o `.md`, os arquivos de publicação e, se pedido, o documento de revisão. No chat:

```
**[Título]** · [n] palavras · "[kw]" ([cauda], [intenção]) · persona [id]

| SEO | GEO | AEO | Geral | Confiança |
|---|---|---|---|---|
| XX | XX | XX | XX | XX% |

**Ganho de informação frente ao top 3:** (uma frase)
**Fact-check:** N afirmações verificadas, M dados do cliente, K removidas
**Revisor:** top fix aplicado: (uma frase)
**Pendente do cliente:** (se houver)
```

Depois de publicado: `python3 SKILL_DIR/scripts/track.py add post_data/checks.json --url URL --date AAAA-MM-DD --log tracking/<blog>.csv --pauta post_data/pauta.json`.
Ofereça uma tarefa agendada mensal que rode `track.py due` e preencha as medições (Search Console, Semrush,
painel de prompts da skill de auditoria). `track.py report` mostra se a nota do lint está prevendo resultado;
quando não estiver, é a rubrica que muda, com os posts que performaram como evidência.

---

## Princípios inegociáveis

- **Evidência acima de moda.** Sem llms.txt, FAQ schema como promessa de rich result (encerrado em mai/2026),
  palavra-chave repetida, "headings em pergunta" como fórmula. Ver `evidence-2026.md`.
- **Resposta primeiro.** A pergunta principal respondida nas primeiras 40 a 60 palavras após o H1.
- **Ganho de informação ou não publica.** Pelo menos um elemento que o top 3 não tem.
- **Nenhum número sem fonte verificada.** `claims.json` com `unverified` bloqueia a entrega. Dado do cliente é
  marcado como tal.
- **Quem escreve não dá a nota.** Revisão por agente que não viu o processo; nota ruim muda o texto, não a nota.
- **Seções autocontidas** com entidades nomeadas. Referência de 120 a 180 palavras por subtema.
- **Voz do perfil** acima do gosto do redator. Nos perfis Carratu, travessão (—) é proibido.
- **Visão de negócio.** Persona e etapa de funil definidas antes de escrever; CTA coerente com o funil.
- **Honestidade sobre limites.** Sem Semrush, volume e KD são "não medidos". Sem top 3 real, diga.
- **Campo que muda rápido.** `evidence-2026.md` é cópia da skill de auditoria (revisão out/2026). Quando atualizar
  uma, copie para a outra. Se a data atual passar de 6 meses da revisão, confirme por busca os itens com ⚠.
