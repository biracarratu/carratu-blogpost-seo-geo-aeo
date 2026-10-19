# Modo pauta: do universo de palavras-chave ao calendário editorial

Saída: `outputs/pauta-<blog>-<periodo>.md` (para ler e aprovar), `.csv` e `.xlsx` (para a operação). Cada linha
da pauta tem o que a skill de escrita precisa para começar sem perguntar nada:

| Campo | O que é | Regra |
|---|---|---|
| `keyword` | Palavra-chave principal | Uma por artigo; sem duplicar intenção com outra linha |
| `tail` | Cauda: `short`, `medium` ou `long` | Ver classificação abaixo |
| `intent` | Intenção dominante: `informacional`, `navegacional`, `comercial`, `transacional` | Decide formato e etapa do funil |
| `h1` | Título do artigo | 40 a 70 caracteres; palavra-chave (ou variação) no primeiro terço; promessa concreta; sem clickbait |
| `seo_title` | Title tag | 50 a 60 caracteres; pode ser igual ao H1 se couber |
| `h2` | 5 a 8 subtópicos | Cada um responde uma subpergunta; incluem o ganho de informação e a FAQ |
| `secondary_keywords` | Por intenção | 2 a 6 por linha, cada uma marcada com a intenção |
| `persona` | Quem lê | Nome da persona do perfil + a pergunta que ela digitaria |
| `funnel` | Etapa: topo, meio, fundo | Derivada da intenção e da persona |
| `format` | guia, lista, comparação, passo a passo, definição, opinião | Pela SERP (ver `serp-analysis.md`) |
| `volume`, `kd`, `aio` | Dados do Semrush/GSC quando houver | `null` = não medido |
| `cluster` | Tema pilar ao qual a linha pertence | Serve para links internos e para a ordem de publicação |
| `priority` | 1 a 3 | Impacto no negócio x facilidade (ver pontuação) |
| `cannibal_risk` | URL de post existente parecido, se houver | De `sitemap_links.py` |
| `publish_date` | Data sugerida | Pelo ritmo definido no briefing |

## 1. Entradas

- **Perfil do blog** (`profiles/<blog>.json`): ICP, oferta, personas (ver abaixo), concorrentes, cluster já
  trabalhado.
- **Universo de palavras-chave** em `post_data/keywords.csv` (`keyword,volume,kd,intent,source,cluster`). Com
  Semrush: relatórios de palavras relacionadas, perguntas e lacunas de palavras frente aos concorrentes
  (base `br`, teto de unidades do briefing). Sem Semrush: Search Console (consultas com impressão e posição > 10
  são ouro), busca na web (autocomplete, PAA, "buscas relacionadas"), perguntas de vendas e suporte do cliente,
  fan-out por tema.
- **Posts existentes**: `python3 SKILL_DIR/scripts/sitemap_links.py --sitemap URL --keywords post_data/keywords.csv`
  marca o que já está coberto (refresh em vez de post novo) e o risco de canibalização.
- **Ritmo**: quantos posts no período e o mix por intenção (ex.: Pontua Q4/2026: 10 por mês, 3 SEO + 7 AEO).

## 2. Personas

Cada perfil tem 2 a 4 personas em `personas[]`: `id`, `nome`, `cargo`, `contexto` (porte, setor), `dor`,
`objetivo`, `pergunta_tipica` (como ela digitaria no Google ou no ChatGPT), `objecoes`, `etapa_funil` onde ela
costuma entrar. Se o perfil não tiver personas, monte a partir do ICP, da página Sobre, de cases e de 3 posts mais
lidos, mostre ao usuário e salve no perfil. Nunca invente dado demográfico que não ajuda a escrever (idade, hobby);
foque em cargo, dor, pergunta e critério de decisão.

Cada linha da pauta tem UMA persona principal. Se a palavra-chave serve a duas, escolha a de maior valor para
o negócio e anote a segunda em `notes`.

## 3. Classificação de cauda

Pelo número de palavras de conteúdo e pelo volume (quando houver):

| Cauda | Palavras | Volume (BR, referência) | Papel na pauta |
|---|---|---|---|
| `short` | 1 a 2 | alto (> 1.000/mês) | Pilar do cluster; difícil; 1 ou 2 por trimestre |
| `medium` | 2 a 3 | médio (100 a 1.000) | Espinha dorsal; maioria dos posts SEO |
| `long` | 4+ ou pergunta completa | baixo (< 100) ou não medido | Posts AEO/GEO; respondem perguntas; ganham citação em IA |

Sem volume, decida pelas palavras e pelo formato (pergunta completa = `long`). O script `pauta_build.py` aplica
essa regra e você ajusta quando conhecer o mercado.

## 4. Intenção

Classifique pela SERP real quando possível (o que o Google mostra: artigos = informacional; páginas de produto e
anúncios = transacional; comparativos e listas "melhores" = comercial; marca ou login = navegacional). Sem SERP, o
script usa modificadores:

- **Informacional:** o que é, como, por que, guia, exemplos, significado, diferença, passo a passo, dicas.
- **Navegacional:** nome de marca, produto, "login", "site", "app". Entra na pauta só se for a própria marca
  (página institucional, não post) ou "alternativas a [concorrente]" (que é comercial).
- **Comercial:** melhor, melhores, vs, versus, comparativo, alternativas, review, avaliação, vale a pena, top.
- **Transacional:** preço, quanto custa, comprar, contratar, assinar, plano, teste grátis, orçamento, demo.

Posts cobrem informacional e comercial; transacional costuma ser página de produto ou preço, e a pauta sinaliza
isso (`format: pagina` e nota) em vez de forçar um artigo. As `secondary_keywords` de uma linha podem misturar
intenções: um guia informacional com uma secundária comercial no fim ("como escolher") faz o funil andar.

## 5. Título (H1) e title tag

- H1 de 40 a 70 caracteres (o lint aceita até 70; acima disso corta em cards e em respostas de IA). Palavra-chave
  ou variação natural no primeiro terço.
- Uma promessa concreta e verificável: número, resultado, público ou prazo ("em 4 etapas", "para PMEs",
  "o que muda em 2026"). Sem "definitivo", "completo", "tudo sobre".
- `seo_title` de 50 a 60 caracteres. Se o H1 couber, repita; senão, encurte preservando a palavra-chave.
- Para `long` em forma de pergunta, o H1 pode ser a pergunta exata, se for como a persona fala.
- Nunca dois H1 na pauta com a mesma promessa para palavras-chave vizinhas: fundir numa linha só.

## 6. Subtópicos (H2)

5 a 8 por linha, derivados de: perguntas do PAA/Semrush, fan-out da palavra-chave, lacunas do top 3 (quando a
pauta for feita com análise de SERP) e objeções da persona. Regras: cada H2 responde uma subpergunta, nomeia a
entidade (não "Benefícios" solto: "Benefícios do controle de ponto digital para o RH"), e a lista inclui
obrigatoriamente um H2 de ganho de informação (dado próprio, case, framework) e "Perguntas frequentes". A ordem é
a do raciocínio da persona: o que é → como funciona → como escolher/fazer → erros → próximos passos.

## 7. Prioridade

`priority` 1 (primeiro) a 3, por pontuação simples que o script calcula e você ajusta:
- Valor de negócio: intenção comercial ou persona de fundo de funil (+2); informacional ligada à oferta (+1).
- Alcance: volume medido acima da mediana do universo (+1) ou AI Overview presente (+1, é oportunidade de citação).
- Facilidade: KD abaixo de 30 ou `long` (+1); post existente para refresh (+1).
- Penalidade: canibalização com post forte (-2); transacional que deveria ser página (-2).

## 8. Montar e validar

1. Preencha `post_data/keywords.csv`. Rode
   `python3 SKILL_DIR/scripts/pauta_build.py post_data/keywords.csv --profile SKILL_DIR/profiles/<blog>.json --out post_data/pauta.json`
   para classificar cauda, intenção, prioridade e cluster inicial.
2. Para cada linha escolhida, escreva `h1`, `seo_title`, `h2[]`, `persona`, `format`, `secondary_keywords[]`
   (com intenção) em `post_data/pauta.json`. Se o ritmo for baixo (até 12 posts), faça uma leitura rápida da SERP
   de cada palavra-chave para confirmar intenção e formato; se for alto, confirme só as `short` e `medium`.
3. Valide e gere os arquivos:
   `python3 SKILL_DIR/scripts/pauta_build.py post_data/pauta.json --profile ... --validate --out-dir outputs --start 2026-11-03 --every 3`
   O script checa tamanhos de H1 e title, palavra-chave no H1, número de H2, persona existente no perfil,
   duplicidade de intenção, e distribui as datas. Gera `.md`, `.csv` e `.xlsx` (se `openpyxl` existir).
4. Mostre ao usuário o resumo: linhas por intenção, por cauda, por persona, por cluster; e as 3 linhas de maior
   prioridade com o porquê. Ajuste e regenere.

Cada linha aprovada vira a resposta do briefing do modo "post novo" (ou "refresh", se `cannibal_risk` indicar um
post existente).
