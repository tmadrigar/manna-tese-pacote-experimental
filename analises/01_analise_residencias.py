"""Tese · análise das residências Manna BRAx e Manna Champion Chip (Capítulos 9 e 10).

Corpus: corte de 23/10/2026, dados pseudonimizados em ../dados (datas sem horário). Cópia de
TESE/analises/01_analise_residencias.py com duas mudanças, as únicas: os caminhos e a ordem cronológica,
que usa a coluna `ordem` (posição do registro pelo horário original) no lugar da hora, retirada dos dados.
Dois protocolos: PAF-5D (IoD, P4C, ED2) e PAA-5D por etapa (EM, F2, F1).

Escalas do boletim: PAF e PAA-EM de 2 a 5; PAA-F2 de 1 a 4; PAA-F1 de 1 a 3. Para comparar protocolos,
cada resposta é levada a 0-100 pela amplitude da sua escala. A rubrica do professor (1 a 5) usa (v-1)*25,
como no painel do sistema. O PAA não tem item de engajamento.

Uso: python analises/01_analise_residencias.py
Grava resultados/residencias_corte23out.json (só agregados; nenhum dado pessoal).
"""
import csv
import datetime as dt
import json
import math
import sys
import unicodedata
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import wilcoxon

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
T = Path(__file__).resolve().parent.parent / "dados"
OUT = Path(__file__).resolve().parent.parent / "resultados" / "residencias_corte23out.json"
OUT.parent.mkdir(exist_ok=True)
D4 = ["exploracao", "experimentacao", "reflexao", "colaboracao"]
D5 = D4 + ["impacto"]
# o Impacto entrou no boletim com o commit 3890f56 do Manna Evidência (29/06/2026, 10h18); os boletins anteriores
# receberam a nota pela coleta retroativa em planilha (5.385 boletins), então só valem os criados a partir de 30/06
IMPACTO_DESDE = "2026-06-30"
ESCALA = {"PAF": (2, 5), "EM": (2, 5), "F2": (1, 4), "F1": (1, 3)}
PROG = {"MannaBRAx 2": "BRAx", "Manna Champion CHIP": "Chip"}
R = {}


def ler(nome):
    df = pd.read_csv(T / f"{nome}.tsv", sep="\t", quoting=csv.QUOTE_NONE, dtype=str, keep_default_na=False)
    return df.replace("NULL", "")


def num(df, cols):
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None, None]
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * p, 1), round(100 * (c - h), 1), round(100 * (c + h), 1)]


def ic(x):
    x = np.asarray(pd.Series(x).dropna(), float)
    if len(x) < 2:
        return [None, None, None]
    m = x.mean(); e = 1.96 * x.std(ddof=1) / math.sqrt(len(x))
    return [round(m, 3), round(m - e, 3), round(m + e, 3)]


def micro_curta(m):
    for chave, nome in (("IoD", "IoD"), ("P4C", "P4C"), ("Eletrônica Digital II", "ED2"), ("Inteligência Artificial", "IA"),
                        ("Inovação", "Inovação"), ("Microeletrônica", "Microeletrônica"), ("Fabricação", "Fabricação")):
        if chave in m:
            return nome
    return m


# ---------------------------------------------------------------- dados
bol = num(ler("bol"), D5 + ["engajamento", "numero", "suspeito", "ordem"])
bol["prog"] = bol.prog.map(PROG)
bol["micro"] = bol.mc.map(micro_curta)
bol["protocolo"] = np.where(bol.modalidade == "PAF", "PAF", "PAA")
bol["etapa"] = bol.modalidade
for d in D5:
    lo = bol.etapa.map(lambda e: ESCALA[e][0]); hi = bol.etapa.map(lambda e: ESCALA[e][1])
    bol[f"{d}_n"] = ((bol[d] - lo) / (hi - lo) * 100).clip(0, 100)
L = bol[bol.suspeito == 0].copy()
L["traj"] = L.alunoId + "|" + L.bootcampId
nm = L.groupby("traj").numero.nunique()
F = L[L.traj.isin(nm[nm >= 4].index) & L.numero.between(1, 4)].copy()

# ---------------------------------------------------------------- 1. corpus
corp = {}
grupos = [("Total", bol)] + [(g, bol[bol.prog == g]) for g in ("BRAx", "Chip")]
grupos += [(f"{g}|{p}", bol[(bol.prog == g) & (bol.protocolo == p)]) for g in ("BRAx", "Chip") for p in ("PAF", "PAA")]
grupos += [(f"micro|{m}", bol[bol.micro == m]) for m in bol.micro.unique()]
grupos += [(f"micro|{m}|{e}", bol[(bol.micro == m) & (bol.etapa == e)]) for m, e in bol[["micro", "etapa"]].drop_duplicates().values]
for nome, X in grupos:
    Fx = F[F.bootcampId.isin(set(X.bootcampId))]
    corp[nome] = {"aplicacoes": X.bootcampId.nunique(), "professores": X.professorId.nunique(), "alunos": X.cpf.nunique(),
                  "boletins": len(X), "marcados": int(X.suspeito.sum()), "trajetorias": int(Fx.traj.nunique())}
R["corpus"] = corp

# ---------------------------------------------------------------- 2. cascata
mem = ler("membros")
res = {g: set(mem[(mem.prog == g) & (mem.ativo == "1")].userId) for g in ("BRAx", "Chip")}
res_all = res["BRAx"] | res["Chip"]
of = {r.professorId: dt.date.fromisoformat(r.primeira) for r in ler("oficinas").itertuples() if r.primeira}
avaliam = {g: set(bol[bol.prog == g].professorId) for g in ("BRAx", "Chip")}
ev = dt.date(2026, 3, 15)
casc = {"residentes": len(res_all), "oficina": wilson(len(res_all & set(of)), len(res_all)),
        "avaliam": wilson(len(res_all & (avaliam["BRAx"] | avaliam["Chip"])), len(res_all)),
        "mediana_semanas_primeira_oficina": round(float(np.median([(of[p] - ev).days / 7 for p in res_all & set(of)])), 1)}
for g in ("BRAx", "Chip"):
    casc[g] = {"residentes": len(res[g]), "oficina_n": len(res[g] & set(of)), "oficina": wilson(len(res[g] & set(of)), len(res[g])),
               "avaliam_n": len(res[g] & avaliam[g]), "avaliam": wilson(len(res[g] & avaliam[g]), len(res[g])),
               "avaliam_paf_n": len(res[g] & set(bol[(bol.prog == g) & (bol.protocolo == "PAF")].professorId)),
               "avaliam_paa_n": len(res[g] & set(bol[(bol.prog == g) & (bol.protocolo == "PAA")].professorId))}
R["cascata"] = casc

# ---------------------------------------------------------------- 3. perfil e alcance
norm = lambda x: unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode().strip().upper()
UFN = {"ACRE": "AC", "ALAGOAS": "AL", "AMAPA": "AP", "AMAZONAS": "AM", "CEARA": "CE", "GOIAS": "GO", "MINAS GERAIS": "MG",
       "PARANA": "PR", "PARA": "PA", "PERNAMBUCO": "PE", "PIAUI": "PI", "RIO DE JANEIRO": "RJ", "RIO GRANDE DO SUL": "RS",
       "RONDONIA": "RO", "SERGIPE": "SE", "TOCANTINS (TO)": "TO", "BAHIA": "BA", "MARANHAO": "MA", "PARAIBA": "PB",
       "SANTA CATARINA": "SC", "SAO PAULO": "SP", "ESPIRITO SANTO": "ES", "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS",
       "RIO GRANDE DO NORTE": "RN", "RORAIMA": "RR", "DISTRITO FEDERAL": "DF"}
uf = lambda s: UFN.get(norm(s), norm(s))
esc = ler("escola").set_index("bootcampId")
gen = ler("genero").drop_duplicates("cpf").set_index("cpf").gender
perf = {}
for g, X in [("Total", bol)] + [(g, bol[bol.prog == g]) for g in ("BRAx", "Chip")]:
    E = esc.loc[esc.index.intersection(set(X.bootcampId))]
    E = E[E.escolaId != ""]
    gx = gen.reindex(X.cpf.unique()).dropna()
    f, m = int((gx == "FEMININO").sum()), int((gx == "MASCULINO").sum())
    perf[g] = {"escolas": E.escolaId.nunique(), "municipios": len({(norm(c), uf(s)) for c, s in zip(E.city, E.state)}),
               "ufs": len({uf(s) for s in E.state if s}), "lista_ufs": sorted({uf(s) for s in E.state if s}), "meninas_pct": round(100 * f / (f + m), 1) if f + m else None,
               "alunos_com_genero": f + m}
R["perfil"] = perf

# ---------------------------------------------------------------- 4. evolução M1 -> M4
def evolucao(X, dims, sufixo=""):
    e = {"trajetorias": int(X.traj.nunique()), "dims": {}}
    for d in dims:
        c = d + sufixo
        if X[c].notna().sum() == 0:
            continue
        w = X.pivot_table(index="traj", columns="numero", values=c)
        if not {1, 4} <= set(w.columns):
            continue
        e["dims"][d] = {"m1": ic(w[1]), "m4": ic(w[4]), "dif": round(float((w[4] - w[1]).mean()), 3),
                        "serie": [ic(w[m]) if m in w.columns else [None] * 3 for m in (1, 2, 3, 4)]}
    return e


def modelo(X, d, fixos):
    f = f"{d} ~ C(numero)" + "".join(f" + C({v})" for v in fixos if X[v].nunique() > 1)
    m = smf.mixedlm(f, X, groups=X["traj"]).fit(reml=True)
    lo, hi = m.conf_int().loc["C(numero)[T.4]"]
    return [round(float(m.params["C(numero)[T.4]"]), 3), round(float(lo), 3), round(float(hi), 3), float(m.pvalues["C(numero)[T.4]"])]


evo = {}
for g in ("BRAx", "Chip"):
    Pf = F[(F.prog == g) & (F.protocolo == "PAF")]
    Pa = F[(F.prog == g) & (F.protocolo == "PAA")]
    evo[g] = {"PAF": evolucao(Pf, D4 + ["engajamento"]), "PAA_norm": evolucao(Pa, D4, "_n"),
              "PAF_norm": evolucao(Pf, D4, "_n"), "por_micro": {}}
    for d in D4:
        evo[g]["PAF"]["dims"][d]["modelo"] = modelo(Pf, d, ["micro"])
        if len(Pa):
            evo[g]["PAA_norm"]["dims"][d]["modelo"] = modelo(Pa, f"{d}_n", ["micro", "etapa"])
    for (mi, et), X in F[F.prog == g].groupby(["micro", "etapa"]):
        evo[g]["por_micro"][f"{mi}|{et}"] = evolucao(X, D4, "_n")
    # Impacto: trajetórias iniciadas depois da entrada do item no boletim (IMPACTO_DESDE)
    for p, X in (("PAF", Pf), ("PAA", Pa)):
        X = X.copy(); X["dtc"] = X.createdAt.str[:10]
        ok = X.groupby("traj").dtc.min() >= IMPACTO_DESDE
        Xi = X[X.traj.isin(ok[ok].index)]
        w = Xi.pivot_table(index="traj", columns="numero", values="impacto_n").dropna()
        if {1, 4} <= set(w.columns) and len(w):
            evo[g][f"impacto_{p}_norm"] = {"n": int(len(w)), "m1": round(float(w[1].mean()), 1), "m4": round(float(w[4].mean()), 1)}
        wb = Xi.pivot_table(index="traj", columns="numero", values="impacto").dropna()
        if p == "PAF" and {1, 4} <= set(wb.columns) and len(wb):
            evo[g]["impacto_PAF"] = {"n": int(len(wb)), "m1": round(float(wb[1].mean()), 2), "m4": round(float(wb[4].mean()), 2)}
R["evolucao"] = evo

# ---------------------------------------------------------------- 5. professor x alunos
rub = num(ler("rub"), D4 + ["numero"])
for d in D4:
    rub[f"{d}_p"] = (rub[d] - 1) * 25
rub["prof"] = rub[[f"{d}_p" for d in D4]].mean(axis=1)
eq = ler("eq")
la = L[["alunoId", "bootcampId", "numero", "prog", "protocolo"] + D4 + [f"{d}_n" for d in D4]].copy()
for d in D4:  # PAF segue o A6 e o painel do sistema; no PAA cada etapa tem a sua escala
    la[f"{d}_a"] = np.where(la.protocolo == "PAF", (la[d] - 1) * 25, la[f"{d}_n"])
team = eq.merge(la, on=["alunoId", "bootcampId"]).groupby(["equipeId", "bootcampId", "numero", "prog", "protocolo"])[[f"{d}_a" for d in D4]].mean().reset_index()
team["alunos"] = team[[f"{d}_a" for d in D4]].mean(axis=1)
P = rub.merge(team, on=["equipeId", "bootcampId", "numero"])
P["dist"] = sum((P[f"{d}_a"] - P[f"{d}_p"]).abs() for d in D4) / 4
pa = {}
for g in ("BRAx", "Chip"):
    for p in ("PAF", "PAA"):
        X = P[(P.prog == g) & (P.protocolo == p)]
        if not len(X):
            continue
        wc = X.pivot_table(index="equipeId", columns="numero", values="dist")
        wc = wc[[1, 4]].dropna() if {1, 4} <= set(wc.columns) else wc.iloc[0:0]
        pa[f"{g}|{p}"] = {"pares": int(len(X)), "professores": int(X.professorId.nunique()),
                          "prof_m1": ic(X[X.numero == 1].prof), "prof_m4": ic(X[X.numero == 4].prof),
                          "alunos_m1": ic(X[X.numero == 1].alunos), "alunos_m4": ic(X[X.numero == 4].alunos),
                          # série na escala de origem (1 a 5): no PAF, (v-1)*25 desfeito nos dois lados
                          "serie_1a5": {m: {"prof": ic(X[X.numero == m].prof / 25 + 1), "alunos": ic(X[X.numero == m].alunos / 25 + 1),
                                            "n": int((X.numero == m).sum())} for m in (1, 2, 3, 4)} if p == "PAF" else None,
                          "equipes_m1_m4": int(len(wc)), "dist_m1": round(float(wc[1].mean()), 1) if len(wc) else None,
                          "dist_m4": round(float(wc[4].mean()), 1) if len(wc) else None,
                          "aproximou_pct": round(100 * float(((wc[1] - wc[4]) > 8).mean()), 1) if len(wc) else None,
                          # queda da distância na mesma equipe (M1 - M4): média com IC 95% e teste de Wilcoxon pareado
                          "dist_queda": ic(wc[1] - wc[4]) if len(wc) else None,
                          "dist_queda_p": round(float(wilcoxon(wc[1], wc[4]).pvalue), 4) if len(wc) else None}
R["professor_alunos"] = pa

# ---------------------------------------------------------------- 6. KDTs
IT = ["integracaoProfessor", "curiosidade", "aprendizagemPratica", "aplicacaoConhecimento", "diversao",
      "impactoDesempenho", "motivacao", "facilitacaoConceitos"]
K = num(ler("kdt"), IT + ["ordem"])
info = bol.drop_duplicates("bootcampId").set_index("bootcampId")[["prog", "protocolo"]]
K = K[K.bootcampId.isin(info.index) & (K.alunoId != "")].sort_values("ordem").drop_duplicates(["alunoId", "bootcampId"], keep="last")
K = K.join(info, on="bootcampId")
kd = {}
for nome, X in [(g, K[K.prog == g]) for g in ("BRAx", "Chip")] + [(f"{g}|{p}", K[(K.prog == g) & (K.protocolo == p)]) for g in ("BRAx", "Chip") for p in ("PAF", "PAA")]:
    kd[nome] = {"avaliacoes": len(X), "itens": {i: ic(X[i]) for i in IT},
                "essencial": wilson(int((X.essencialAprendizagem == "SIM").sum()), len(X)),
                "recomendaria": wilson(int((X.recomendaria == "SIM").sum()), len(X))}
R["kdts"] = kd

# ---------------------------------------------------------------- 7. selo (inventário + todas as missões + avaliação do KDT)
nmiss = num(ler("nmiss"), ["n_miss"]).set_index("bootcampId").n_miss
mt = bol.groupby(["alunoId", "bootcampId"]).size().rename("n_bol").reset_index().join(info, on="bootcampId")
mt["n_miss"] = mt.bootcampId.map(nmiss).fillna(0)
inv = ler("inv"); inv_set = set(zip(inv.alunoId, inv.bootcampId))
kit_set = set(zip(K.alunoId, K.bootcampId))
eq_set = set(zip(eq.alunoId, eq.bootcampId)); par = ler("pares"); par_set = set(zip(par.avaliadorId, par.bootcampId))
mt["inv"] = [(a, b) in inv_set for a, b in zip(mt.alunoId, mt.bootcampId)]
mt["mis"] = (mt.n_bol >= mt.n_miss) & (mt.n_miss > 0)
mt["kit"] = [(a, b) in kit_set for a, b in zip(mt.alunoId, mt.bootcampId)]
mt["selo"] = mt.inv & mt.mis & mt.kit
mt["equipe"] = [(a, b) in eq_set for a, b in zip(mt.alunoId, mt.bootcampId)]
mt["pares"] = [(a, b) in par_set for a, b in zip(mt.alunoId, mt.bootcampId)]
sl = {}
for nome, X in [(g, mt[mt.prog == g]) for g in ("BRAx", "Chip")] + [(f"{g}|{p}", mt[(mt.prog == g) & (mt.protocolo == p)]) for g in ("BRAx", "Chip") for p in ("PAF", "PAA")]:
    Eq = X[X.equipe]
    sl[nome] = {"matriculas": len(X), "inventario_pct": round(100 * X.inv.mean(), 1), "missoes_pct": round(100 * X.mis.mean(), 1),
                "kit_pct": round(100 * X.kit.mean(), 1), "selo": wilson(int(X.selo.sum()), len(X)),
                "pares_pct": round(100 * Eq.pares.mean(), 1) if len(Eq) else None}
R["selo"] = sl

# ---------------------------------------------------------------- 8. consistência (alfa) por protocolo
def alpha(M):
    M = np.asarray(M, float); k = M.shape[1]
    return k / (k - 1) * (1 - M.var(axis=0, ddof=1).sum() / M.sum(axis=1).var(ddof=1))


cons = {}
for p in ("PAF", "PAA"):
    X = L[(L.protocolo == p) & (L.createdAt >= IMPACTO_DESDE)].dropna(subset=[f"{d}_n" for d in D5])
    cr = X[[f"{d}_n" for d in D5]].corr().values; off = cr[np.triu_indices(5, 1)]
    cons[p] = {"n": len(X), "alfa": round(float(alpha(X[[f"{d}_n" for d in D5]])), 3), "r_min": round(float(off.min()), 2), "r_max": round(float(off.max()), 2)}
R["consistencia"] = cons

# ---------------------------------------------------------------- 9. o mesmo aluno em mais de uma microcredencial
F["v_n"] = F[[f"{d}_n" for d in D4]].mean(axis=1)
tr = F.groupby(["cpf", "traj", "micro", "protocolo"]).agg(inicio=("ordem", "min")).reset_index()
m1 = F[F.numero == 1].groupby("traj").v_n.mean(); m4 = F[F.numero == 4].groupby("traj").v_n.mean()
tr["m1"] = tr.traj.map(m1); tr["m4"] = tr.traj.map(m4)
tr = tr[tr.cpf != ""].sort_values(["cpf", "inicio"])
multi = tr.groupby("cpf").filter(lambda x: x.micro.nunique() >= 2)
pri = multi.groupby("cpf").nth(0).set_index("cpf"); seg = multi.groupby("cpf").nth(1).set_index("cpf")
long = {"alunos_2_ou_mais_micros": int(multi.cpf.nunique()),
        "sequencias": multi.groupby("cpf").apply(lambda x: " > ".join(x.micro)).value_counts().head(8).to_dict(),
        "primeira": {"m1": ic(pri.m1), "m4": ic(pri.m4)}, "segunda": {"m1": ic(seg.m1), "m4": ic(seg.m4)},
        "m1_segunda_menos_m1_primeira": ic(seg.m1 - pri.m1), "m4_segunda_menos_m4_primeira": ic(seg.m4 - pri.m4)}
ambos_paf = (pri.protocolo == "PAF") & (seg.protocolo == "PAF")
long["so_paf"] = {"alunos": int(ambos_paf.sum()), "primeira": {"m1": ic(pri.m1[ambos_paf]), "m4": ic(pri.m4[ambos_paf])},
                  "segunda": {"m1": ic(seg.m1[ambos_paf]), "m4": ic(seg.m4[ambos_paf])},
                  "m1_segunda_menos_m1_primeira": ic((seg.m1 - pri.m1)[ambos_paf]),
                  "m1_segunda_menos_m4_primeira": ic((seg.m1 - pri.m4)[ambos_paf])}
long["m1_segunda_menos_m4_primeira"] = ic(seg.m1 - pri.m4)
R["longitudinal"] = long

json.dump(R, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False,
          default=lambda o: int(o) if isinstance(o, np.integer) else float(o) if isinstance(o, np.floating) else str(o))

# ---------------------------------------------------------------- resumo na tela
print("CASCATA", json.dumps(casc, ensure_ascii=False))
print("PERFIL", json.dumps(perf, ensure_ascii=False))
for g in ("BRAx", "Chip"):
    for k in ("PAF", "PAA_norm"):
        e = evo[g][k]
        print(f"EVO {g} {k} traj={e['trajetorias']}", " | ".join(f"{d[:5]} {v['m1'][0]}->{v['m4'][0]} mod {v.get('modelo', ['-'])[0]} [{v.get('modelo', [0, '-'])[1]}; {v.get('modelo', [0, 0, '-'])[2]}]" for d, v in e["dims"].items()))
    print(f"  impacto {g}:", {k: v for k, v in evo[g].items() if k.startswith('impacto')})
print("PROF x ALUNOS", json.dumps(pa, ensure_ascii=False))
print("KDT", {k: (v["avaliacoes"], v["essencial"][0], v["itens"]["integracaoProfessor"][0]) for k, v in kd.items()})
print("SELO", {k: (v["matriculas"], v["selo"][0], v["pares_pct"]) for k, v in sl.items()})
print("ALFA", cons)
print("LONGITUDINAL", json.dumps(long, ensure_ascii=False, default=str))
