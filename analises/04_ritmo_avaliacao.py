"""Tese · ritmo da avaliação no tempo: residentes que avaliam por mês, volume de boletins por mês e UF,
microcredenciais aplicadas por residente e atraso entre a liberação da microcredencial e a aplicação.
Lê os dados pseudonimizados de ../dados; grava só agregados em resultados/ritmo_avaliacao_corte23out.json."""
import csv, json, sys, unicodedata
from pathlib import Path
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
T = Path(__file__).resolve().parent.parent / "dados"
OUT = Path(__file__).resolve().parent.parent / "resultados" / "ritmo_avaliacao_corte23out.json"
ler = lambda n: pd.read_csv(T / f"{n}.tsv", sep="\t", quoting=csv.QUOTE_NONE, dtype=str, keep_default_na=False).replace("NULL", "")
PROG = {"MannaBRAx 2": "BRAx", "Manna Champion CHIP": "Chip"}
bol = ler("bol"); bol["prog"] = bol.prog.map(PROG); bol["dia"] = pd.to_datetime(bol.createdAt.str[:10])
bol["mes"] = bol.dia.dt.strftime("%Y-%m"); bol["sem"] = bol.dia.dt.to_period("W").astype(str)
mem = ler("membros"); res = {g: set(mem[(mem.prog == g) & (mem.ativo == "1")].userId) for g in ("BRAx", "Chip")}
R = {}
# 1. residentes que já avaliavam no sistema ao fim de cada mês
meses = sorted(bol.mes.unique()); R["avaliam_por_mes"] = {}
for g in ("BRAx", "Chip"):
    pri = bol[bol.prog == g].groupby("professorId").dia.min()
    pri = pri[pri.index.isin(res[g])]
    R["avaliam_por_mes"][g] = {m: [int((pri.dt.strftime("%Y-%m") <= m).sum()), round(100 * (pri.dt.strftime("%Y-%m") <= m).sum() / len(res[g]), 1)] for m in meses}
# 2. boletins por mês e por semana, por programa
R["boletins_por_mes"] = {g: bol[bol.prog == g].groupby("mes").size().to_dict() for g in ("BRAx", "Chip")}
R["boletins_por_semana"] = bol.groupby("sem").size().to_dict()
# 3. boletins por UF e mês (agosto a outubro), para ver interrupções regionais
norm = lambda x: unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode().strip().upper()
esc = ler("escola").set_index("bootcampId")
bol["uf"] = bol.bootcampId.map(esc.state).map(norm)
R["boletins_uf_mes"] = bol[bol.mes >= "2026-06"].pivot_table(index="uf", columns="mes", values="id", aggfunc="count", fill_value=0).astype(int).to_dict(orient="index")
# 4. microcredenciais aplicadas com avaliação por residente ativo e atraso em relação à liberação
def micro(m):
    for k, n in (("IoD", "IoD"), ("P4C", "P4C"), ("Eletrônica Digital II", "ED2"), ("Inteligência Artificial", "IA"), ("Inovação", "Inovação"), ("Microeletrônica", "Microeletrônica"), ("Fabricação", "Fabricação")):
        if k in m: return n
bol["micro"] = bol.mc.map(micro)
lib = bol.groupby("micro").dia.min()
R["liberacao"] = {k: str(v.date()) for k, v in lib.items()}
R["micros_por_residente"] = {}; R["atraso_semanas"] = {}
for g in ("BRAx", "Chip"):
    X = bol[(bol.prog == g) & bol.professorId.isin(res[g])]
    n = X.groupby("professorId").micro.nunique().reindex(list(res[g]), fill_value=0)
    R["micros_por_residente"][g] = n.value_counts().sort_index().to_dict()
    ini = X.groupby(["professorId", "micro"]).dia.min().reset_index()
    ini["atraso"] = (ini.dia - ini.micro.map(lib)).dt.days / 7
    R["atraso_semanas"][g] = {m: [round(float(v.median()), 1), int(len(v))] for m, v in ini.groupby("micro").atraso}
json.dump(R, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
for k in ("avaliam_por_mes", "boletins_por_mes", "liberacao", "micros_por_residente", "atraso_semanas"):
    print(k, json.dumps(R[k], ensure_ascii=False))
print("semanas", json.dumps(R["boletins_por_semana"]))
