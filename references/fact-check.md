# Fact-check operacional

Estatística inventada é o erro mais caro do conteúdo para IA: o motor cita, o cliente assina. Por isso o
check `geo.data_accuracy` não é opinião do redator: ele sai de `post_data/claims.json`.

## Passos

1. **Extrair:** `python3 SKILL_DIR/scripts/claims.py extract outputs/<slug>.md --out post_data/claims.json`
   Cada frase com número, %, R$, ano, "segundo X", "estudo", "pesquisa" vira uma linha com `status: pending`.
2. **Verificar uma a uma.** Para cada afirmação:
   - Abra a `source_url` (leitura de página web, navegador ou coleta direta). Se não houver URL, encontre a fonte
     primária por busca; se não existir fonte primária, a afirmação sai do texto.
   - Confirme que a fonte diz **aquilo**, com o mesmo número, ano, país e amostra. Arredondar é ok se o texto
     disser "cerca de"; trocar "empresas B2B dos EUA" por "empresas" não é.
   - Preencha `status`, `quote` (trecho literal da fonte, até 300 caracteres) e, se precisar, `note`.
3. **Status possíveis:**
   - `verified`: fonte primária confirma; `quote` preenchido e `source_url` apontando para ela.
   - `client_data`: número fornecido pelo cliente (case, resultado interno). O texto precisa dizer que é dado
     do cliente ("em nossos clientes", "na operação da [Marca]"). `note` com quem forneceu e quando.
   - `removed`: a afirmação foi retirada do texto porque não achou fonte ou a fonte dizia outra coisa.
   - `na`: a frase caiu no filtro mas não é dado verificável (ex.: "em 2026, o processo muda" sem estatística;
     a data da publicação; um exemplo hipotético marcado como tal).
   - `unverified`: ficou sem confirmar. **Bloqueia a entrega.** Ou vira `removed`, ou vira `verified`.
4. **Conferir:** `python3 SKILL_DIR/scripts/claims.py status post_data/claims.json` (saída 0 = tudo resolvido).
5. Rodar o lint com `--claims post_data/claims.json`. O check falha com qualquer `pending` ou `unverified`.

## Regras

- Fonte primária antes de secundária: o estudo original, a documentação oficial, o órgão público. Um blog que
  cita o estudo é pista, não fonte. Linke a primária.
- Dados dos últimos 24 meses quando existirem. Dado antigo pode entrar se for o único e o texto disser o ano.
- Dados de concorrentes diretos do cliente (listados em `nao_citar` do perfil) não entram como fonte.
- Se uma fonte for paywall ou PDF que não dá para abrir, peça ao usuário o trecho ou troque a fonte.
- Nunca "corrija" o número para bater com o argumento. Se a fonte derruba o argumento, muda o argumento.
- Quando o texto final mudar (nova seção, número novo), rode `extract` de novo: os ids reiniciam, então mantenha
  o arquivo anterior como `claims-v1.json` se precisar reaproveitar quotes.

## Exemplo de linha preenchida

```json
{"id": "c3", "section": "O que muda na prospecção outbound", "text": "Um SDR gasta cerca de 30% do dia pesquisando contas, segundo o relatório X de 2026.",
 "source_url": "https://fonte-primaria.com/relatorio-2026", "source_inline": true,
 "status": "verified", "quote": "Reps spend 31% of their selling time on account research (n=1,200, 2026).", "note": "Arredondado para 30% com 'cerca de'."}
```
