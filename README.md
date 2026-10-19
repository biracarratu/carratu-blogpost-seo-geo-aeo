# Blogpost SEO · GEO · AEO (Metodologia Carratu)

Skill para o Claude que escreve posts de blog prontos para ranquear no Google e ser citados por motores de IA
(ChatGPT, AI Overviews/AI Mode, Perplexity, Gemini, Claude), com base nas mesmas evidências de 2026 da skill de
auditoria `carratu-seo-geo-aeo`.

**Autor:** Ubirajara Carratu · [Carratu Digital](https://carratu.com.br) · Versão 1.1.0 (outubro de 2026)

## Três modos

- **Pauta:** do universo de palavras-chave ao calendário editorial, com cauda (short, medium, long), intenção
  (informacional, navegacional, comercial, transacional), H1 e title dentro das regras, 5 a 8 subtópicos H2,
  persona, cluster, prioridade e risco de canibalização. Sai em .md, .csv e .xlsx.
- **Post novo:** pesquisa, análise do top 3, brief, texto, checagem em três camadas, arquivos de publicação.
- **Refresh:** importa o post publicado, mede a linha de base e atualiza preservando URL e o que já ranqueia.

## Como funciona o post

1. **Briefing curto:** blog/cliente, pauta, palavra-chave, fontes de dados e formato de entrega.
2. **Perfil do blog:** voz, ICP, CTA e regras de estilo de cada blog ou cliente (`profiles/`).
3. **Pesquisa da palavra-chave:** intenção, secundárias, perguntas reais e fan-out (Semrush opcional).
4. **Análise das 3 primeiras posições** pelo HTML real: tamanho, estrutura, respostas, dados, FAQ, datas, e uma
   matriz de lacunas (o que todos cobrem, o que ninguém cobre e o ICP pergunta).
5. **Posts existentes e material próprio:** links internos, canibalização, cases e dados do cliente.
6. **Brief** com ângulo, estrutura, evidências e metadados.
7. **Texto** em Markdown com frontmatter (title, meta, slug, keyword, autor, datas, alt).
8. **Checagem em três camadas:** lint com 36 checks ponderados por evidência (notas 0-100 de SEO, GEO e AEO, confiança,
   portões de estilo); **fact-check** afirmação a afirmação contra a fonte primária (`claims.json`, qualquer dado não
   verificado bloqueia); **revisão independente** por um agente que não viu o processo. Só entrega com índice ≥ 80 e
   críticos em pass.
9. **Arquivos de publicação:** HTML de blocos do WordPress, HTML limpo, JSON-LD Article e payload com meta do Yoast.
10. **Acompanhamento:** registro do post e medições em 30 e 90 dias (Search Console, Semrush, painel de prompts) para
    recalibrar a rubrica com resultado real.

Não publica: entrega o post para a etapa de publicação (WordPress, HubSpot ou a pipeline de cada blog).

## Instalação

1. Envie o ZIP em **Configurações → Capacidades → Skills** no app do Claude.
2. Ative a execução de código. Com rede liberada, o top 3 é coletado direto; sem ela, pelo navegador (Claude in
   Chrome) ou em modo aproximado.
3. Opcional: conecte o Semrush e o conector do seu blog.
4. Crie o perfil do seu blog copiando `profiles/_template.json` (ou deixe a skill montar no primeiro uso).

## Scripts

- `pauta_build.py`: classifica palavras-chave (cauda, intenção, prioridade, cluster), valida H1/title/H2/persona e gera a pauta.
- `sitemap_links.py`: canibalização e candidatos a link interno a partir do sitemap.
- `serp_extract.py` + `browser_collect.js`: medem o top 3 pelo HTML real (direto ou pelo navegador).
- `html_to_md.py`: importa um post publicado para o modo refresh.
- `claims.py`: extrai afirmações com dados e controla a verificação.
- `lint_post.py`: 36 checks, notas e confiança; lê `claims.json` e `review.json`. Só biblioteca padrão.
- `md_to_wp.py`: HTML de blocos, JSON-LD e payload do WordPress/Yoast.
- `track.py`: registro de publicação, medições pendentes e relatório nota x resultado.

Licença: PolyForm Noncommercial 1.0.0 (ver `NOTICE.md`). Uso comercial exige licença.
