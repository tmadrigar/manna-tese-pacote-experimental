# Regras de integridade

Os boletins são preenchidos nas escolas, sem pesquisador presente. Antes das análises, três regras fixas examinam o relato da descoberta, o texto em que o aluno conta o que descobriu na missão. Um boletim marcado continua visível para o professor e sai de todas as médias, trajetórias e índices. Nenhuma classificação por modelo de linguagem participa dessa seleção.

As regras são aplicadas dentro de cada aplicação, nesta ordem; um boletim já marcado por uma regra não é examinado pelas seguintes.

| Ordem | Regra | Código em `dados/bol.tsv` | Definição |
|---|---|---|---|
| 1 | Autoplágio | `autoplagio` | O mesmo aluno envia o mesmo texto em duas ou mais missões da aplicação. Todas as ocorrências são marcadas. |
| 2 | Cópia coletiva | `copia_coletiva` | O mesmo texto é enviado por dois ou mais alunos diferentes da aplicação. Todas as ocorrências são marcadas. |
| 3 | Ruído de teclado | `ruido` | O texto tem 8 ou mais caracteres seguidos sem vogal (expressão regular `[^aeiouáéíóúâêîôûãõàèìòùü\s]{8,}`, sem distinção de maiúsculas) ou um trecho de 1 a 3 caracteres que aparece cinco ou mais vezes seguidas (`(.{1,3})\1{4,}`). |

Nas duas regras de cópia, os textos são comparados exatamente como foram gravados, sem normalização.

Para o corte da tese, as marcas vindas do sistema em produção foram todas zeradas e as três regras foram reaplicadas à base congelada. O resultado, que `analises/03_integridade.py` reproduz a partir da coluna `regra`:

| Regra | Boletins |
|---|---:|
| Autoplágio | 1.130 |
| Ruído de teclado | 920 |
| Cópia coletiva | 142 |
| **Total marcado** | **2.192 de 19.373 (11,3%)** |

Os textos não fazem parte do pacote. Exemplos reais de relatos marcados e de relatos válidos estão no Capítulo 7 da tese.
