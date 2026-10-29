# Dicionário de dados

Corte congelado do Manna Evidência em outubro de 2026, residências Manna BRAx e Manna Champion Chip. Todas as tabelas são TSV em UTF-8, com cabeçalho. `NULL` indica campo sem valor.

## Códigos

Os identificadores foram trocados por códigos sequenciais. O mesmo código aponta para a mesma entidade em todas as tabelas.

| Prefixo | Entidade |
|---|---|
| `B` | boletim de missão |
| `A` | aluno no sistema (um cadastro por turma) |
| `E` | estudante (a mesma pessoa em mais de uma turma ou microcredencial) |
| `C` | aplicação de uma microcredencial numa turma (no banco, `bootcamp`) |
| `P` | professor residente |
| `Q` | equipe |
| `S` | escola |
| `U` | município |
| `I` | inventário inicial |
| `R` | rubrica do professor |
| `K` | avaliação de KDT |

Datas estão no formato `AAAA-MM-DD`, sem horário. Onde a ordem cronológica importa, a coluna `ordem` dá a posição do registro pelo horário original (1 = o mais antigo).

## Protocolos e escalas

Cada aplicação usa um protocolo de boletim, indicado em `modalidade`:

| Protocolo | Etapa | Escala das dimensões |
|---|---|---|
| `PAF` | PAF-5D, protocolo das microcredenciais de IoD, P4C e Eletrônica Digital II | 2 a 5 (14 boletins, de maio e junho de 2026, têm algum valor 1, levado a 0 na escala de 0 a 100) |
| `EM` | PAA-5D, ensino médio | 2 a 5 |
| `F2` | PAA-5D, anos finais do ensino fundamental | 1 a 4 |
| `F1` | PAA-5D, anos iniciais do ensino fundamental | 1 a 3 |

Para comparar protocolos, os scripts levam cada resposta a uma escala de 0 a 100 pela amplitude da escala do protocolo.

## `bol.tsv`: boletins de missão

Um boletim por aluno e missão. 19.373 linhas.

| Coluna | Descrição |
|---|---|
| `id` | código do boletim (`B`) |
| `alunoId` | código do aluno no sistema (`A`) |
| `cpf` | código do estudante (`E`); o CPF original não está no pacote |
| `bootcampId` | código da aplicação (`C`) |
| `professorId` | código do professor (`P`) |
| `mc` | nome da microcredencial |
| `prog` | residência: `MannaBRAx 2` ou `Manna Champion CHIP` |
| `modalidade` | protocolo da aplicação: `PAF`, `EM`, `F2` ou `F1` |
| `paaModalidade` | etapa do PAA-5D (`NULL` no PAF) |
| `numero` | missão, de 1 a 4 |
| `exploracao`, `experimentacao`, `reflexao`, `colaboracao`, `impacto` | autoavaliação do aluno nas cinco dimensões |
| `engajamento` | item de engajamento, de 2 a 5 (só no PAF; `NULL` no PAA) |
| `suspeito` | 1 se o boletim foi marcado por uma regra de integridade |
| `regra` | regra que marcou o boletim: `autoplagio`, `copia_coletiva` ou `ruido` (vazio se não marcado) |
| `createdAt` | data do envio |
| `ordem` | posição cronológica do envio |

O item de Impacto entrou no boletim no fim de junho de 2026. Os boletins anteriores receberam a nota por uma coleta retroativa, e por isso as análises do Impacto usam só trajetórias iniciadas a partir de 30/06/2026.

## `rub.tsv`: rubricas do professor

Uma rubrica por equipe e missão, na escala de 1 a 5.

| Coluna | Descrição |
|---|---|
| `id` | código da rubrica (`R`) |
| `equipeId` | código da equipe (`Q`) |
| `bootcampId` | código da aplicação (`C`) |
| `numero` | missão, de 1 a 4 |
| `professorId` | código do professor (`P`) |
| `exploracao`, `experimentacao`, `reflexao`, `colaboracao` | nota do professor em cada dimensão |
| `impacto` | sempre `NULL`: a rubrica avalia só as quatro dimensões de processo |
| `createdAt` | data |

## `eq.tsv`: alunos em equipes

| Coluna | Descrição |
|---|---|
| `alunoId` | código do aluno (`A`) |
| `equipeId` | código da equipe (`Q`) |
| `bootcampId` | código da aplicação (`C`) |

## `pares.tsv`: avaliação entre pares

Uma linha por avaliação feita por um aluno sobre um colega da equipe.

| Coluna | Descrição |
|---|---|
| `avaliadorId` | código do aluno que avaliou (`A`) |
| `avaliadoId` | código do colega avaliado (`A`) |
| `bootcampId` | código da aplicação (`C`) |

## `inv.tsv`: inventários iniciais

| Coluna | Descrição |
|---|---|
| `id` | código do inventário (`I`) |
| `alunoId` | código do aluno (`A`) |
| `bootcampId` | código da aplicação (`C`) |
| `paaModalidade` | etapa do PAA-5D (`NULL` no PAF) |
| `exploracao`, `experimentacao`, `reflexao`, `colaboracao`, `impacto` | média dos itens de cada dimensão no inventário |
| `createdAt` | data |

## `kdt.tsv`: avaliação dos kits pelos alunos

| Coluna | Descrição |
|---|---|
| `id` | código da avaliação (`K`) |
| `alunoId` | código do aluno (`A`) |
| `bootcampId` | código da aplicação (`C`) |
| `tipo` | quem avaliou (`ALUNO`) |
| `kdt` | nome do kit |
| `motivacao`, `curiosidade`, `diversao`, `aprendizagemPratica`, `facilitacaoConceitos`, `aplicacaoConhecimento`, `impactoDesempenho`, `integracaoProfessor` | itens de 1 a 5 |
| `essencialAprendizagem` | o kit foi essencial para aprender: `SIM`, `TALVEZ` ou `NAO` |
| `recomendaria` | recomendaria o kit a outros: `SIM`, `TALVEZ` ou `NAO` |
| `createdAt` | data |
| `ordem` | posição cronológica; quando o aluno avaliou o mesmo kit mais de uma vez na aplicação, vale a última |

## `membros.tsv`: residentes

| Coluna | Descrição |
|---|---|
| `userId` | código do professor (`P`) |
| `prog` | residência: `BRAx` ou `Chip` |
| `ativo` | 1 se o cadastro do residente estava ativo no corte |

## `oficinas.tsv`: primeira oficina

| Coluna | Descrição |
|---|---|
| `professorId` | código do professor (`P`) |
| `primeira` | data da primeira oficina registrada nas residências |

## `escola.tsv`: escola e município de cada aplicação

| Coluna | Descrição |
|---|---|
| `bootcampId` | código da aplicação (`C`) |
| `escolaId` | código da escola (`S`) |
| `city` | código do município (`U`) |
| `state` | estado, como cadastrado pela escola (sigla ou nome) |
| `educationLevels` | etapas de ensino da turma |

## `genero.tsv`: gênero do estudante

Gênero pelo cadastro escolar, para os estudantes do corpus.

| Coluna | Descrição |
|---|---|
| `cpf` | código do estudante (`E`) |
| `gender` | `FEMININO` ou `MASCULINO` |

## `nmiss.tsv`: missões por aplicação

| Coluna | Descrição |
|---|---|
| `bootcampId` | código da aplicação (`C`) |
| `n_miss` | número de missões cadastradas (4 em todas) |
