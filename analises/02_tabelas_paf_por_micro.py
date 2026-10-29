"""Tese · médias brutas do PAF-5D por microcredencial (M1 e M4) para as tabelas do Capítulo 9.
Reaproveita o carregamento de 01_analise_residencias.py. Grava resultados/paf_por_micro_corte23out.json."""
import json, runpy, sys
from pathlib import Path
sys.argv = ["x"]
g = runpy.run_path(str(Path(__file__).with_name("01_analise_residencias.py")))
F, D4 = g["F"], g["D4"]
out = {}
for mi, X in F[F.protocolo == "PAF"].groupby("micro"):
    out[mi] = {"trajetorias": int(X.traj.nunique())}
    for d in D4 + ["engajamento"]:
        w = X.pivot_table(index="traj", columns="numero", values=d)
        out[mi][d] = [round(float(w[1].mean()), 2), round(float(w[4].mean()), 2)]
json.dump(out, open(Path(__file__).resolve().parent.parent / "resultados" / "paf_por_micro_corte23out.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(out, ensure_ascii=False))
