# Pesquisa da palavra-chave e análise do top 3

Todo caminho tem versão com Semrush e sem Semrush. Nenhuma ferramenta paga é obrigatória.

## Parte 1: palavra-chave → `post_data/keyword.json`

```json
{
  "keyword": "prospecção b2b com ia",
  "market": "br", "language": "pt-BR",
  "volume": 590, "kd": 34, "intent": "informacional",
  "source": "semrush | websearch | user",
  "secondary": ["prospecção outbound com inteligência artificial", "..."],
  "questions": ["o que é prospecção com ia", "quais ferramentas usar", "..."],
  "aio_present": true,
  "format": "guia | lista | comparação | passo a passo | definição | opinião",
  "notes": "SERP mostra 2 vídeos e um PAA com 4 perguntas"
}
```

### Com Semrush (conector MCP)

Fluxo do conector: descoberta (`keyword_research`, `organic_research`) → `get_report_schema(relatório)` →
`execute_report`. Use o nome do relatório exatamente como a descoberta devolve.

- **Base:** `br` para blogs brasileiros (o padrão do conector é `us`).
- **Orçamento:** estime e respeite o teto do usuário (um post costuma caber em 300 a 1.500 unidades).
  `display_limit` de 10 a 30.
- Roteiro:
  1. Visão da palavra-chave: volume, KD, intenção, CPC e SERP features (código 52 = AI Overview).
  2. Palavras relacionadas e variações (escolha 5 a 12 secundárias com intenção compatível).
  3. Perguntas (relatório de perguntas/"questions") para a FAQ e para os H2.
  4. Resultados orgânicos da palavra (top 10 com URL e posição): fonte da lista do top 3.

### Sem Semrush

- **Search Console conectado** (blog já existente): consultas próximas que já trazem impressões.
- **Busca na web:** pesquise a palavra-chave e 2 variações; registre o top 3, se há resposta de IA no topo e as
  perguntas relacionadas que aparecem. Diga que é amostra (a busca do Claude não é o Google).
- **Navegador do usuário (Claude in Chrome), com permissão:** abrir o Google em aba nova para ver o top 3 real,
  People Also Ask e AI Overview. É o substituto mais fiel para a SERP brasileira.
- Volume e KD sem Semrush: `null` e anote "não medido".

### Fan-out (sempre)

Liste as subconsultas que um motor de IA faria para responder a palavra-chave: definição, como funciona,
benefícios e riscos, custo, passo a passo, ferramentas, comparação com alternativa, exemplos, erros comuns,
"vale a pena para [ICP]". As que forem relevantes viram H2 ou FAQ.

## Parte 2: top 3 → `post_data/top3.json` + matriz de lacunas

### Coleta (HTML real, não resumo)

Resumos de página perdem headings, tabelas e datas. Em ordem:

1. **Direto:** `python3 SKILL_DIR/scripts/serp_extract.py URL1 URL2 URL3 --keyword "kw" --out post_data/top3.json`
   (saída 3 = rede bloqueada).
2. **Navegador:** abra cada URL, rode `document.documentElement.outerHTML` com a ferramenta de JavaScript e
   salve em `post_data/serp/1.html`, `2.html`, `3.html`. Depois rode o script com os arquivos e
   `--urls URL1,URL2,URL3` para manter a referência.
3. **Sem rede e sem navegador:** use a leitura de páginas da web só para estrutura e argumento; marque no brief
   que a medição do top 3 é aproximada.

Pule do top 3: Reddit/fóruns, YouTube, marketplaces e páginas de ferramenta (anote no brief que existem, pois
indicam o formato que o Google quer). Use a próxima posição de artigo.

### O que o script mede (por URL)

`word_count`, `h1`, `headings` (H2/H3), `answer_first` (palavras até a primeira frase que contém a palavra-chave
ou uma definição), `question_headings`, `numbers` (números com contexto), `external_links` (domínios),
`tables`, `lists`, `faq_detected`, `date_published/modified`, `author`, `schema_types`, `images`.
E o agregado: tamanho mediano, H2 comuns (temas presentes em 2+ concorrentes) e H2 exclusivos.

### O que você avalia lendo

| Pergunta | Uso no brief |
|---|---|
| O que os 3 cobrem? | Obrigatório ter (sem isso o post não compete) |
| O que só 1 cobre? | Diferencial barato, cubra melhor |
| O que nenhum cobre e o ICP pergunta? | **Ganho de informação**, vira seção destaque |
| O que está velho, errado ou sem fonte? | Corrija com dado atual e fonte primária |
| Qual o ângulo de cada um? | Escolha um ângulo que eles não ocupam |
| AI Overview cita quem e responde como? | Formato do bloco-resposta e das definições |

### Tamanho

Não persiga contagem de palavras. Referência: mediana do top 3, de -20% a +30%, desde que cada seção ganhe seu
lugar. Se o top 3 é raso (menos de 800 palavras) e a intenção é simples, um post enxuto e melhor vence.
