"""Tese · exporta os dados pseudonimizados do pacote experimental público da tese (corte 23/10/2026).

Lê os TSVs privados do corpus congelado (00_exportar_corpus.sh) e grava, na pasta dados/ do pacote,
os mesmos arquivos com:
  - todos os identificadores trocados por códigos sequenciais (B = boletim, A = aluno no sistema,
    E = estudante/CPF, C = aplicação, P = professor, Q = equipe, S = escola, U = município,
    I = inventário, R = rubrica, K = avaliação de KDT);
  - datas sem horário e uma coluna `ordem` (posição cronológica do registro) no lugar da hora,
    para que as análises que dependem da ordem dêem o mesmo resultado;
  - a regra de integridade de cada boletim marcado (autoplagio, copia_coletiva, ruido), sem o texto;
  - nenhum texto livre, nome, e-mail ou CPF; só o que pertence às aplicações do corpus.
Os nomes das colunas são os mesmos das extrações, para que os scripts de análise rodem sem mudança.

Uso: python 19_exportar_pacote_publico.py <pasta_tsv> <regra.tsv> <pasta_dados_do_pacote>
"""
import csv
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

S, REGRA, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)


def ler(nome):
    return pd.read_csv(S / f"{nome}.tsv", sep="\t", quoting=csv.QUOTE_NONE, dtype=str, keep_default_na=False)


def gravar(df, nome):
    df.to_csv(OUT / f"{nome}.tsv", sep="\t", index=False, quoting=csv.QUOTE_NONE, lineterminator="\n")
    print(f"  {nome}.tsv: {len(df)} linhas")


COD = {}


def codigo(prefixo, valores, largura=5):
    """Mapa determinístico valor -> código, pela ordem dos valores originais (não reversível)."""
    m = COD.setdefault(prefixo, {})
    for v in sorted(set(valores) - set(m) - {"", "NULL"}):
        m[v] = f"{prefixo}{len(m) + 1:0{largura}d}"
    return m


def troca(serie, prefixo):
    m = codigo(prefixo, serie)
    return serie.map(lambda v: m.get(v, v))


def ordem(df):
    """Posição cronológica pelo horário original e, no empate, pelo id original."""
    return df.sort_values(["createdAt", "id"]).assign(o=range(1, len(df) + 1)).o.reindex(df.index)


dia = lambda s: s.str[:10]

# ---------------- boletins (base do corpus)
bol = ler("bol")
reg = pd.read_csv(REGRA, sep="\t", dtype=str, keep_default_na=False).set_index("id").regra
bol["regra"] = bol.id.map(reg).fillna("")
assert (bol.suspeito == "1").sum() == (bol.regra != "").sum(), "regra sem marca ou marca sem regra"
BCS = set(bol.bootcampId)
bol["ordem"] = ordem(bol)
for c, p in (("id", "B"), ("cpf", "E"), ("alunoId", "A"), ("bootcampId", "C"), ("professorId", "P")):
    bol[c] = troca(bol[c], p)
bol["createdAt"] = dia(bol.createdAt)
print("data/")
gravar(bol, "bol")
CPFS = set(ler("bol").cpf)

# ---------------- residentes e primeira oficina
mem = ler("membros"); mem["userId"] = troca(mem.userId, "P")
gravar(mem, "membros")
of = ler("oficinas"); of["professorId"] = troca(of.professorId, "P")
gravar(of, "oficinas")

# ---------------- escola, município e etapas de cada aplicação
esc = ler("escola"); esc = esc[esc.bootcampId.isin(BCS)].copy()
# município codificado depois da mesma normalização de 01_analise_residencias.py (acentos, caixa e nome do estado)
norm = lambda x: unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode().strip().upper()
UFN = {"ACRE": "AC", "ALAGOAS": "AL", "AMAPA": "AP", "AMAZONAS": "AM", "CEARA": "CE", "GOIAS": "GO", "MINAS GERAIS": "MG",
       "PARANA": "PR", "PARA": "PA", "PERNAMBUCO": "PE", "PIAUI": "PI", "RIO DE JANEIRO": "RJ", "RIO GRANDE DO SUL": "RS",
       "RONDONIA": "RO", "SERGIPE": "SE", "TOCANTINS (TO)": "TO", "BAHIA": "BA", "MARANHAO": "MA", "PARAIBA": "PB",
       "SANTA CATARINA": "SC", "SAO PAULO": "SP", "ESPIRITO SANTO": "ES", "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS",
       "RIO GRANDE DO NORTE": "RN", "RORAIMA": "RR", "DISTRITO FEDERAL": "DF"}
uf = lambda s: UFN.get(norm(s), norm(s))
chave = esc.city.map(norm) + "|" + esc.state.map(uf)
esc["city"] = troca(chave.where(esc.city.map(norm) != "", ""), "U")
esc["bootcampId"] = troca(esc.bootcampId, "C"); esc["escolaId"] = troca(esc.escolaId, "S")
gravar(esc, "escola")

# ---------------- gênero dos alunos do corpus
gen = ler("genero"); gen = gen[gen.cpf.isin(CPFS)].copy(); gen["cpf"] = troca(gen.cpf, "E")
gravar(gen, "genero")

# ---------------- equipes, rubricas do professor e avaliação entre pares
eq = ler("eq"); eq = eq[eq.bootcampId.isin(BCS)].copy()
for c, p in (("alunoId", "A"), ("equipeId", "Q"), ("bootcampId", "C")):
    eq[c] = troca(eq[c], p)
gravar(eq, "eq")
rub = ler("rub"); rub = rub[rub.bootcampId.isin(BCS)].copy()
for c, p in (("id", "R"), ("equipeId", "Q"), ("bootcampId", "C"), ("professorId", "P")):
    rub[c] = troca(rub[c], p)
rub["createdAt"] = dia(rub.createdAt)
gravar(rub, "rub")
par = ler("pares"); par = par[par.bootcampId.isin(BCS)].copy()
for c, p in (("avaliadorId", "A"), ("avaliadoId", "A"), ("bootcampId", "C")):
    par[c] = troca(par[c], p)
gravar(par, "pares")

# ---------------- inventário inicial, avaliação dos KDTs e missões por aplicação
inv = ler("inv"); inv = inv[inv.bootcampId.isin(BCS)].copy()
for c, p in (("id", "I"), ("alunoId", "A"), ("bootcampId", "C")):
    inv[c] = troca(inv[c], p)
inv["createdAt"] = dia(inv.createdAt)
gravar(inv, "inv")
kd = ler("kdt"); kd = kd[kd.bootcampId.isin(BCS)].copy()
kd["ordem"] = ordem(kd)
for c, p in (("id", "K"), ("alunoId", "A"), ("bootcampId", "C")):
    kd[c] = troca(kd[c], p)
kd["createdAt"] = dia(kd.createdAt)
gravar(kd, "kdt")
nm = ler("nmiss"); nm = nm[nm.bootcampId.isin(BCS)].copy(); nm["bootcampId"] = troca(nm.bootcampId, "C")
gravar(nm, "nmiss")

# nenhum CPF de 11 dígitos nem id do sistema pode sobrar
for f in OUT.glob("*.tsv"):
    t = f.read_text(encoding="utf-8", errors="replace")
    assert not re.search(r"(?<!\d)\d{11}(?!\d)", t), f"CPF em {f.name}"
    assert not re.search(r"\bc[a-z0-9]{24}\b", t), f"id do sistema em {f.name}"
print("ok: sem CPF e sem identificadores do sistema")
