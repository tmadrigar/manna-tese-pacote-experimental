# Pacote experimental da tese: Metodologia Manna

Dados pseudonimizados, rotinas de análise e resultados da tese de doutorado

> **Metodologia Manna: avaliação formativa adaptativa e computacional em escala nacional, da residência docente à sala de aula para a Educação 5.0**
>
> Tiago Tadeu Madrigar. Programa de Pós-Graduação em Ciência da Computação, Universidade Estadual de Maringá (UEM), 2026.
> Orientadora: Profa. Dra. Linnyer Beatrys Ruiz Aylon. Coorientador: Prof. Dr. Rodrigo Calvo.

Este repositório permite auditar e repetir as análises das residências Manna BRAx e Manna Champion Chip apresentadas na tese. Os dados vêm do Manna Evidência, o sistema que registra as aplicações da Metodologia Manna nas escolas, no corte congelado de outubro de 2026: 19.373 boletins de missão de 2.627 alunos, em 455 aplicações de 113 professores.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `dados/` | Onze tabelas em TSV, uma por instrumento (boletins, rubricas, inventários, avaliações de KDT, equipes, avaliação entre pares) e por informação de contexto (residentes, primeira oficina, escola e município, gênero, missões por aplicação). O [dicionário de dados](dados/DICIONARIO.md) descreve cada coluna. |
| `analises/` | Os scripts que produzem os números da tese, em Python. |
| `resultados/` | Os resultados agregados que a tese cita, em JSON. |
| `documentacao/` | As [regras de integridade](documentacao/REGRAS_DE_INTEGRIDADE.md) aplicadas aos boletins. |

## Como reproduzir

Com Python 3.11 ou mais recente:

```bash
pip install -r requirements.txt
python analises/01_analise_residencias.py   # corpus, cascata, perfil, evolução, professor x alunos, KDT, selo, consistência
python analises/02_tabelas_paf_por_micro.py # médias do PAF-5D por microcredencial
python analises/03_integridade.py           # boletins marcados por regra
python analises/04_ritmo_avaliacao.py       # adesão e volume de avaliação ao longo dos meses
```

Cada script grava o seu JSON em `resultados/`. Os arquivos gerados são idênticos, byte a byte, aos que a tese usa.

| Script | Resultado | Onde aparece na tese |
|---|---|---|
| `01_analise_residencias.py` | `residencias_corte23out.json` | Capítulos 1, 9 e 10 |
| `02_tabelas_paf_por_micro.py` | `paf_por_micro_corte23out.json` | Capítulo 9 |
| `03_integridade.py` | `integridade_corte23out.json` | Capítulos 4 e 7 |
| `04_ritmo_avaliacao.py` | `ritmo_avaliacao_corte23out.json` | Capítulo 9 |

Os scripts `01`, `02` e `04` são cópias dos usados na tese com duas mudanças, as únicas: os caminhos das pastas e a ordem cronológica, que passa a usar a coluna `ordem` no lugar do horário, retirado dos dados.

O arquivo `resultados/cruzamento_mannaid_evidencia.json` traz o cruzamento entre o MannaID, o sistema da fase inaugural, e o Manna Evidência. Ele sustenta o Capítulo 10 e entra só como resultado agregado: o pareamento dos professores usa nome e e-mail, que não podem ser publicados.

O script `analises/00_exportar_dados.py` mostra como as tabelas de `dados/` foram geradas a partir da base privada. Ele não roda fora do ambiente do autor.

## Privacidade

Os alunos são, em sua maioria, crianças e adolescentes. Por isso:

- todos os identificadores (aluno, CPF, professor, aplicação, equipe, escola, município e cada registro) foram trocados por códigos sequenciais, sem tabela de correspondência pública;
- as datas não têm horário;
- nenhum texto escrito por alunos ou professores foi incluído, nem nome, e-mail ou CPF;
- o município aparece só como código; o estado aparece como cadastrado pela escola.

O exportador verifica, ao final, que nenhum número de 11 dígitos nem identificador do sistema sobrou nas tabelas.

## O que não está aqui

O código-fonte do Manna Evidência e do MannaID não faz parte do pacote, porque os sistemas estão em processo de registro de software. Os algoritmos que a tese usa (índices do Manna Analytics, inventário único, distribuição da avaliação entre pares, selo, insígnias e regras de integridade) estão descritos em pseudocódigo no Capítulo 7 da tese.

## Licenças

O código da pasta `analises/` está sob a licença MIT ([LICENSE](LICENSE)). Os dados, os resultados e a documentação estão sob a licença Creative Commons Atribuição 4.0 Internacional ([LICENCA-DADOS](LICENCA-DADOS)).

## Como citar

MADRIGAR, Tiago Tadeu. **Metodologia Manna**: avaliação formativa adaptativa e computacional em escala nacional, da residência docente à sala de aula para a Educação 5.0. 2026. Tese (Doutorado em Ciência da Computação) – Universidade Estadual de Maringá, Maringá, 2026.

Os metadados de citação estão em [CITATION.cff](CITATION.cff).
