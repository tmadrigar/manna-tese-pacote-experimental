"""Tese · contagem dos boletins marcados pelas três regras de integridade (Capítulos 4 e 7).

As regras foram aplicadas ao corpus congelado antes da exportação (ver documentacao/REGRAS_DE_INTEGRIDADE.md);
a coluna `regra` de dados/bol.tsv diz qual delas marcou cada boletim.
Uso: python analises/03_integridade.py
Grava resultados/integridade_corte23out.json.
"""
import csv
import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
T = Path(__file__).resolve().parent.parent / "dados"
OUT = Path(__file__).resolve().parent.parent / "resultados" / "integridade_corte23out.json"
bol = pd.read_csv(T / "bol.tsv", sep="\t", quoting=csv.QUOTE_NONE, dtype=str, keep_default_na=False)
bol["prog"] = bol.prog.map({"MannaBRAx 2": "BRAx", "Manna Champion CHIP": "Chip"})
R = {}
for nome, X in [("Total", bol)] + [(g, bol[bol.prog == g]) for g in ("BRAx", "Chip")]:
    m = X[X.suspeito == "1"]
    R[nome] = {"boletins": len(X), "marcados": len(m), "marcados_pct": round(100 * len(m) / len(X), 1),
               "por_regra": {r: int((m.regra == r).sum()) for r in ("autoplagio", "ruido", "copia_coletiva")}}
json.dump(R, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(R, ensure_ascii=False, indent=1))
