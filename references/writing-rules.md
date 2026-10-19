# Regras de escrita SEO · GEO · AEO

Cada regra tem o id do check em `rubric.json`. **(auto)** = o `lint_post.py` mede; **(claims)** = sai do fact-check
(`claims.json`); **(manual)** = o revisor independente avalia (`review.json`), ou você com `--manual` se não houver agentes. Níveis de evidência como em `evidence-2026.md`: S forte, C correlacional, A prática de mercado.
Crítico = precisa estar em `pass` para entregar.

## Esqueleto padrão

```
# H1 (promessa clara, com a palavra-chave ou variação natural)

Bloco-resposta: 40 a 60 palavras que respondem a pergunta principal. Definição ou resposta direta na 1ª frase.

[Opcional: 3 a 5 bullets "o que você vai ver" ou um dado forte com fonte]

## H2 = subpergunta 1 (o que é / por que importa)
## H2 = subpergunta 2 (como funciona / passo a passo)
## H2 = subpergunta 3 (comparação, ferramentas, custo, exemplos)
## H2 = seção de ganho de informação (dado próprio, case, framework, erro comum que ninguém conta)
## H2 = como começar / próximos passos + CTA do perfil
## Perguntas frequentes
### Pergunta real 1?
Resposta de 40 a 80 palavras.
## Fontes
- [Título da fonte, ano](URL)
```

Adapte ao formato decidido na Etapa 2: lista ("N melhores…") usa H2 por item com critério igual para todos;
comparação usa tabela no início; passo a passo usa lista numerada e um H2 por etapa.

---

## SEO

- **seo.single_h1** (auto, crítico, S): um único `# H1` no corpo.
- **seo.title_length** (auto, A): `seo_title` de 50 a 60 caracteres (45 a 65 = warn). Termina antes do corte.
- **seo.title_keyword** (auto, A): palavra-chave ou variação natural no `seo_title`, de preferência no início.
  Correspondência exata forçada não ajuda em IA (evidência M); escreva para clique.
- **seo.meta_description** (auto, A): 140 a 160 caracteres, benefício concreto e convite. O Google reescreve
  muitas vezes, mas ela vira o snippet em redes e em vários motores.
- **seo.h1_keyword** (auto, A): H1 contém a palavra-chave ou suas palavras principais.
- **seo.slug** (auto, A): até 6 palavras, minúsculas, sem acento, sem stopwords, sem ano (para durar).
- **seo.keyword_early** (auto, A): palavra-chave nas primeiras 100 palavras.
- **seo.keyword_stuffing** (auto, C): densidade da palavra-chave exata até 2,5%. Use variações e sinônimos.
- **seo.secondary_coverage** (auto, A): pelo menos 60% das secundárias aparecem de forma natural.
- **seo.heading_structure** (auto, S): 3+ H2, nenhum H3 sem H2 acima, headings descritivos (não "Introdução",
  "Conclusão" soltos).
- **seo.internal_links** (auto, S): 3+ links para o próprio blog/site com âncora descritiva (nunca "clique aqui").
- **seo.external_links** (auto, C): 2+ links para fontes externas confiáveis (primárias, não concorrentes diretos).
- **seo.image_alt** (auto, S): `image_alt` no frontmatter e alt descritivo em toda imagem do corpo.
- **seo.length_vs_top3** (auto, A): entre -20% e +30% da mediana do top 3 (só com `--top3`).
- **seo.readability** (auto, C): frases com média até 22 palavras, parágrafos até 4 frases (~90 palavras),
  25%+ das frases com palavra de transição. Voz ativa.
- **seo.search_intent** (manual, crítico, S): o formato e o ângulo atendem a intenção dominante da SERP e o ICP.
  pass: um leitor do ICP que buscou a palavra-chave resolve o que queria aqui · fail: formato errado (ex.: guia
  para consulta transacional) ou ângulo genérico.

## GEO

- **geo.answer_first** (auto, crítico, C): o primeiro parágrafo após o H1 tem 30 a 80 palavras e contém a
  palavra-chave (ou suas palavras principais) e uma resposta ou definição ("X é…", "X consiste em…",
  "Para X, faça…"). 44% das citações do ChatGPT saem do primeiro terço da página. Nada de "Neste artigo vamos…".
- **geo.passages** (auto, C): seções H2 autocontidas; 60%+ entre 100 e 350 palavras e nenhuma abaixo de 50.
  Referência ideal de passagem: 120 a 180 palavras por subtema.
- **geo.no_vague_openers** (auto, A): seções não começam com pronome sem referente ("Isso", "Ele", "Essa
  ferramenta"). Repita o nome da entidade: passagens são lidas isoladas.
- **geo.evidence_density** (auto, C): pelo menos 1 dado concreto (número, %, R$, prazo, ano) a cada 250 palavras.
- **geo.sources_section** (auto, C): seção `## Fontes` com links, ou links inline em todos os dados.
- **geo.expert_signal** (auto, C): pelo menos uma citação atribuída ("segundo [nome, cargo]", blockquote com
  autor) ou experiência em primeira pessoa do autor/cliente.
- **geo.author_eeat** (auto, S): `author` preenchido com nome e papel. A página de autor no site é com a
  publicação.
- **geo.freshness** (auto, C): `date`/`updated` preenchidos; dados citados dos últimos 24 meses quando existirem;
  ano atual mencionado quando o tema é sensível a tempo (ferramentas, preços, regras).
- **geo.information_gain** (manual, crítico, S): há algo que o top 3 não tem. pass: pelo menos um ativo
  original relevante (dado do cliente, case com número, framework próprio, teste, opinião assinada com
  argumento) · warn: originalidade só no ângulo · fail: reescreve o top 3.
- **geo.data_accuracy** (claims, crítico, S): todo número tem fonte verificável e está dito como a fonte diz
  (ano, amostra, país). Dado do cliente marcado como tal. Nenhuma estatística inventada. fail com 1 dado sem
  fonte.
- **geo.entity_specificity** (manual, C): nomes próprios claros e consistentes (marca, produto, ferramentas,
  normas, cidades, pessoas) em vez de "soluções", "plataformas", "especialistas".

## AEO

- **aeo.definition** (auto, C): existe uma frase de definição direta do tema principal ("X é um/uma…").
- **aeo.faq** (auto, A): seção de perguntas frequentes com 3 a 6 perguntas reais (PAA, Semrush, vendas) e
  respostas de 40 a 80 palavras que começam pela resposta. Sem FAQ schema como promessa de rich result
  (encerrado); FAQ serve para o leitor e para extração.
- **aeo.direct_answers** (auto, C): headings em pergunta são seguidos de um parágrafo de até 70 palavras que
  responde de cara. Use headings em pergunta quando espelham buscas reais, não como fórmula.
- **aeo.lists_tables** (auto, C): pelo menos uma lista ou tabela quando o conteúdo é sequência, critério ou
  comparação.
- **aeo.question_coverage** (manual, C): as perguntas de `keyword.json` relevantes ao ICP estão respondidas
  em seção ou FAQ. pass: 80%+ · warn: 50 a 79% · fail: menos.

## Estilo e marca (portões, não somam nota)

- **style.em_dash** (auto, crítico se o perfil proíbe): nenhum travessão (—) nem meia-risca usada como
  travessão (–). Troque por vírgula, dois-pontos, ponto ou parênteses.
- **style.forbidden_terms** (auto): nenhum termo de `estilo.termos_proibidos` do perfil (inclui clichês como
  "no cenário atual", "no mundo cada vez mais", "desvendar", "mergulhar fundo").
- **style.cta** (auto): o post tem o CTA do perfil (texto ou URL) na conclusão.
- **style.voice** (manual): soa como a persona do perfil, na pessoa e no registro definidos.

## Como registrar os manuais (sem revisor)

```json
[
  {"id": "geo.information_gain", "status": "pass", "evidence": "Seção 'O que vimos em 40 operações B2B' traz taxa de resposta do cliente (dado próprio); nenhum do top 3 tem dado de campo."},
  {"id": "geo.data_accuracy", "status": "pass", "evidence": "7 dados, todos com link para fonte primária (Gartner 2025, RD Station 2026...)."}
]
```

Status: `pass`, `warn`, `fail`, `na`, `unknown`.
