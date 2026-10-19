# Revisão independente (editor que não viu o processo)

Quem escreve não dá a própria nota. Depois do lint automático e do fact-check, dispare **um subagente** (ferramenta
de agentes da sessão, agente de uso geral) com o prompt abaixo. Ele recebe só: o post, o brief, o perfil, o
`top3.json` e este arquivo. Não recebe o histórico da conversa nem as notas do lint.

Se a sessão não tiver ferramenta de agentes, faça a revisão você mesmo **depois de uma pausa de contexto**: releia
o post do início como leitor, sem olhar o brief, e só então preencha o `review.json`. Diga na entrega que a
revisão não foi independente.

## Prompt do revisor

```
Você é editor sênior de conteúdo B2B e analista de busca. Vai revisar um post de blog que outra pessoa escreveu.
Você NÃO participou da pesquisa nem da escrita. Seja específico e duro: elogio genérico não ajuda ninguém.

Arquivos: o post (Markdown), o brief, o perfil do blog (voz, ICP, CTA, regras), top3.json (medição dos 3 primeiros
resultados para a palavra-chave) e as regras em references/writing-rules.md.

Leia o post inteiro UMA vez como o leitor do ICP descrito no perfil, sem pular. Depois responda, com evidência
(trecho citado, número de seção), a cada item:

1. seo.search_intent: se eu buscasse "[palavra-chave]" e caísse aqui, eu resolveria o que vim fazer? O formato
   (guia, lista, comparação) é o que a SERP pede? pass / warn / fail.
2. geo.information_gain: cite UMA coisa que este post tem e que, pelo top3.json e pela sua leitura, os três
   primeiros resultados não têm. Se não houver, fail. Se for só ângulo, warn.
3. geo.entity_specificity: liste 3 trechos genéricos ("soluções", "ferramentas modernas", "especialistas") que
   deveriam nomear coisas. Nenhum = pass; 1 ou 2 = warn; 3+ = fail.
4. aeo.question_coverage: das perguntas listadas no brief (seção FAQ e subperguntas), quais ficaram sem resposta
   direta no texto? Percentual coberto e status.
5. style.voice: o texto soa como a persona do perfil? Cite um trecho que acerta e um que erra. Pronome, registro,
   clichês, travessão.
6. Leitura humana: onde você parou de ler? Que parágrafo poderia sumir sem perda? Que frase um especialista do
   setor acharia errada ou rasa?
7. Risco: alguma afirmação que, publicada com o nome do cliente, poderia gerar problema (jurídico, factual,
   promessa de resultado)?

Devolva APENAS um JSON neste formato:
{
  "checks": [
    {"id": "seo.search_intent", "status": "pass|warn|fail", "evidence": "..."},
    {"id": "geo.information_gain", "status": "...", "evidence": "..."},
    {"id": "geo.entity_specificity", "status": "...", "evidence": "..."},
    {"id": "aeo.question_coverage", "status": "...", "evidence": "..."},
    {"id": "style.voice", "status": "...", "evidence": "..."}
  ],
  "cut_candidates": ["trecho ou seção que poderia sair"],
  "expert_objections": ["frase e por que um especialista discordaria"],
  "risks": ["..."],
  "top_fix": "a única mudança que mais melhoraria o post"
}
```

## Depois da revisão

1. Salve a resposta em `post_data/review.json`.
2. Aplique `top_fix` e trate `expert_objections` e `risks` (corrigir ou cortar). `cut_candidates` são sugestões:
   corte se concordar, justifique se não.
3. Rode o lint com `--review post_data/review.json` (os checks do revisor entram no lugar dos manuais).
4. Se o revisor deu `fail` em algo crítico, corrija e **rode a revisão de novo** com um agente novo. Não negocie a
   nota: mude o texto.
