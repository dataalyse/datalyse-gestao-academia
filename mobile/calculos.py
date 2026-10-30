"""Leitura da planilha e cálculo dos indicadores — mesmas fórmulas corrigidas do painel web.

As abas brutas são lidas pelo nome das colunas (tolerando acentos, colunas extras e
linhas novas). Nenhuma célula com fórmula da planilha é usada.
"""
from __future__ import annotations

import datetime as dt
import math
import re
import unicodedata

import openpyxl

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
DIAS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]

# coluna lógica -> (apelidos normalizados, obrigatória)
SPEC = {
    "Premissas": {"param": (["parametro"], 1), "valor": (["valor"], 1)},
    "Alunos": {"id": (["id"], 0), "nome": (["nome"], 1), "modalidade": (["modalidade"], 1), "plano": (["plano"], 0),
               "matricula": (["data matricula", "matricula"], 1), "mensalidade": (["mensalidade"], 1),
               "status": (["status"], 1), "cancelamento": (["data cancelamento", "cancelamento"], 0), "origem": (["origem"], 0)},
    "Turmas": {"codigo": (["codigo", "turma"], 1), "modalidade": (["modalidade"], 1), "dia": (["dia", "dias"], 1),
               "horario": (["horario"], 1), "professor": (["professor"], 1), "capacidade": (["capacidade"], 1),
               "matriculados": (["matriculados"], 1), "presenca": (["presenca media", "presenca"], 1), "custo": (["custo mensal", "custo"], 1)},
    "Receitas": {"data": (["data"], 1), "cliente": (["cliente"], 0), "modalidade": (["modalidade"], 0), "tipo": (["tipo"], 0),
                 "previsto": (["valor previsto"], 1), "recebido": (["valor recebido"], 1),
                 "forma": (["forma pagamento", "forma de pagamento"], 0), "status": (["status"], 0), "mes": (["mes"], 0)},
    "Despesas": {"data": (["data"], 1), "categoria": (["categoria"], 1), "descricao": (["descricao"], 0),
                 "tipo": (["fixa/variavel", "fixa / variavel", "fixa ou variavel", "tipo"], 1),
                 "centro": (["centro custo", "centro de custo"], 1), "valor": (["valor"], 1), "mes": (["mes"], 0)},
    "Leads": {"data": (["data"], 1), "nome": (["nome"], 0), "origem": (["origem"], 1), "interesse": (["interesse"], 1),
              "experimental": (["experimental"], 1), "compareceu": (["compareceu"], 1), "matriculou": (["matriculou"], 1),
              "valor_plano": (["valor plano"], 0), "cac": (["cac"], 0), "status": (["status"], 0)},
    "Churn_Cancelamentos": {"base": (["base inicial"], 1), "novos": (["novos alunos", "novos"], 1), "cancel": (["cancelamentos"], 1)},
    "Ocupacao_Horarios": {"horario": (["horario"], 1), "capacidade": (["capacidade"], 1), "matriculados": (["matriculados"], 1),
                          "presenca": (["presenca media", "presenca"], 1)},
    "NotasFiscais": {"data": (["data emissao", "data de emissao", "emissao", "data"], 1), "numero": (["numero", "n"], 0),
                     "serie": (["serie"], 0), "tipo": (["tipo"], 0),
                     "parceiro": (["emitente/destinatario", "emitente / destinatario", "emitente", "fornecedor", "destinatario", "parceiro", "cliente"], 0),
                     "doc": (["cnpj/cpf", "cnpj", "cpf"], 0), "descricao": (["descricao"], 0), "categoria": (["categoria"], 0),
                     "valor": (["valor total", "valor"], 1), "status": (["status", "situacao"], 0), "chave": (["chave de acesso", "chave"], 0),
                     "mes": (["mes"], 0)},
}
PREM_PADRAO = {"mens_musc": 150, "mens_lutas": 190, "mens_bale": 140, "taxa_receb": .97, "churn": .05, "cac": 100,
               "margem": .65, "cresc": .03, "custo_fixo": 18000, "meta": 300, "dias": 26}
_PREM_REGRAS = [
    ("mens_musc", lambda s: "mensalidade" in s and "muscula" in s), ("mens_lutas", lambda s: "mensalidade" in s and "luta" in s),
    ("mens_bale", lambda s: "mensalidade" in s and "bale" in s), ("taxa_receb", lambda s: "recebimento" in s),
    ("churn", lambda s: "churn" in s), ("cac", lambda s: re.search(r"\bcac\b", s) is not None), ("margem", lambda s: "margem" in s),
    ("cresc", lambda s: "crescimento" in s), ("custo_fixo", lambda s: "custo" in s and "fixo" in s), ("meta", lambda s: "meta" in s),
    ("dias", lambda s: "dias" in s),
]


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def norm(s) -> str:
    s = unicodedata.normalize("NFD", "" if s is None else str(s))
    return re.sub(r"\s+", " ", "".join(c for c in s if unicodedata.category(c) != "Mn")).strip().lower()


def txt(v) -> str:
    return "" if v is None else str(v).strip()


def num(v) -> float:
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v) if math.isfinite(v) else 0.0
    s = re.sub(r"[R$\s% ]", "", str(v))
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def sim(v) -> bool:
    return norm(v) in ("sim", "s", "yes", "y", "1", "true", "x", "ok")


def parse_data(v) -> dt.date | None:
    if v is None or v == "":
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    if isinstance(v, (int, float)) and v > 1000:
        return dt.date(1899, 12, 30) + dt.timedelta(days=int(v))
    s = str(v).strip()
    m = re.match(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})", s)
    if m:
        a = int(m[3]) + (2000 if int(m[3]) < 100 else 0)
        try:
            return dt.date(a, int(m[2]), int(m[1]))
        except ValueError:
            return None
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", s)
    return dt.date(int(m[1]), int(m[2]), int(m[3])) if m else None


def mkey(d: dt.date | None) -> str | None:
    return f"{d.year}-{d.month:02d}" if d else None


def parse_mes(v) -> str | None:
    if v is None or v == "":
        return None
    if isinstance(v, str):
        m = re.match(r"^\s*(\d{1,2})[/\-](\d{4})\s*$", v)
        if m:
            return f"{m[2]}-{int(m[1]):02d}"
        m = re.match(r"^\s*(\d{4})[/\-](\d{1,2})\s*$", v)
        if m:
            return f"{m[1]}-{int(m[2]):02d}"
    return mkey(parse_data(v))


def mlabel(k: str | None) -> str:
    if not k:
        return "—"
    a, m = k.split("-")
    return f"{MESES[int(m) - 1]}/{a[2:]}"


def add_meses(k: str, n: int) -> str:
    a, m = map(int, k.split("-"))
    t = a * 12 + (m - 1) + n
    return f"{t // 12}-{t % 12 + 1:02d}"


def fim_do_mes(k: str) -> dt.date:
    return dt.date.fromisoformat(add_meses(k, 1) + "-01") - dt.timedelta(days=1)


def faixa(horario) -> tuple[int, int] | None:
    n = norm(horario)
    m = re.search(r"(\d{1,2})\s*(?:h|:\d\d)?\s*(?:-|–|a|ate|as)\s*(\d{1,2})", n)
    if m:
        return int(m[1]), int(m[2])
    m = re.search(r"(\d{1,2})", n)
    return (int(m[1]), int(m[1]) + 1) if m else None


def expandir_dias(s) -> list[int]:
    n = norm(s).replace("–", "-")
    m = re.match(r"^([a-z]{3})[a-z]*\.?\s*(?:-|a|ate)\s*([a-z]{3})", n)
    if m and m[1] in DIAS and m[2] in DIAS and DIAS.index(m[2]) >= DIAS.index(m[1]):
        return list(range(DIAS.index(m[1]), DIAS.index(m[2]) + 1))
    return sorted({DIAS.index(t[:3]) for t in re.split(r"[,/;e ]+", n) if t[:3] in DIAS})


# ----------------------------------------------------------------------------
# Leitura da planilha
# ----------------------------------------------------------------------------
def ler_planilha(origem) -> dict[str, list[list]]:
    """Abas -> linhas (valores). `origem` pode ser caminho ou arquivo em memória."""
    wb = openpyxl.load_workbook(origem, data_only=True, read_only=True)
    out = {}
    for ws in wb.worksheets:
        linhas = [list(r) for r in ws.iter_rows(values_only=True)]
        out[ws.title] = [l for l in linhas if any(v not in (None, "") for v in l)]
    wb.close()
    return out


def _aba(book, nome):
    alvo = norm(nome).replace(" ", "").replace("_", "")
    for k, v in book.items():
        if norm(k).replace(" ", "").replace("_", "") == alvo:
            return v
    return None


def _tabela(book, nome, avisos) -> list[dict]:
    linhas = _aba(book, nome)
    if linhas is None:
        avisos.append(f"Aba “{nome}” não encontrada.")
        return []
    h = next((i for i, l in enumerate(linhas) if sum(v not in (None, "") for v in l) >= 2), None)
    if h is None:
        return []
    cab = [norm(c) for c in linhas[h]]
    idx, faltam = {}, []
    for k, (apelidos, obrig) in SPEC[nome].items():
        i = next((j for j, c in enumerate(cab) if c in apelidos), None)
        if i is None:
            i = next((j for j, c in enumerate(cab) if any(c.startswith(a) for a in apelidos)), None)
        idx[k] = i
        if i is None and obrig:
            faltam.append(apelidos[0])
    if faltam:
        avisos.append(f"Aba “{nome}”: coluna(s) não encontrada(s) — {', '.join(faltam)}.")
    return [{k: (l[i] if i is not None and i < len(l) else None) for k, i in idx.items()} for l in linhas[h + 1:]]


def status_ocup(o):
    return "Sem turma" if o is None else "Alta" if o >= .8 else "Média" if o >= .5 else "Baixa"


def carregar(book) -> tuple[dict, list[str]]:
    avisos: list[str] = []
    P = dict(PREM_PADRAO)
    vistos = set()
    for r in _tabela(book, "Premissas", avisos):
        s = norm(r["param"])
        for k, f in _PREM_REGRAS:
            if k not in vistos and f(s):
                v = num(r["valor"])
                P[k] = v / 100 if k in ("taxa_receb", "churn", "margem", "cresc") and v > 1 else v
                vistos.add(k)
                break

    def mens(mod):
        n = norm(mod)
        return P["mens_musc"] if "muscula" in n else P["mens_bale"] if "bale" in n else P["mens_lutas"]

    alunos = []
    for i, r in enumerate(_tabela(book, "Alunos", avisos), 1):
        st_ = norm(r["status"])
        status = "Ativo" if st_.startswith("ativ") else "Cancelado" if st_.startswith(("cancel", "inativ")) else txt(r["status"]) or "—"
        m = parse_data(r["matricula"])
        alunos.append({"id": r["id"] or i, "nome": txt(r["nome"]) or f"Aluno {i}", "modalidade": txt(r["modalidade"]) or "—",
                       "plano": txt(r["plano"]) or "—", "matricula": m, "mk": mkey(m), "mensalidade": num(r["mensalidade"]),
                       "status": status, "cancelamento": parse_data(r["cancelamento"]), "origem": txt(r["origem"]) or "—"})
    turmas = []
    for r in _tabela(book, "Turmas", avisos):
        cap, mat, custo, mod = num(r["capacidade"]), num(r["matriculados"]), num(r["custo"]), txt(r["modalidade"]) or "—"
        oc = mat / cap if cap > 0 else None
        rec = mat * mens(mod)
        fx = faixa(r["horario"])
        turmas.append({"codigo": txt(r["codigo"]), "modalidade": mod, "dia": txt(r["dia"]), "horario": txt(r["horario"]),
                       "professor": txt(r["professor"]) or "—", "capacidade": cap, "matriculados": mat, "presenca": num(r["presenca"]),
                       "custo": custo, "ocup": oc, "rec_pot": rec, "margem": rec - custo, "margem_pct": (rec - custo) / rec if rec else None,
                       "status": status_ocup(oc), "dias": expandir_dias(r["dia"]), "hora": fx[0] if fx else None})
    receitas = []
    for r in _tabela(book, "Receitas", avisos):
        d = parse_data(r["data"])
        receitas.append({"data": d, "mes": parse_mes(r["mes"]) or mkey(d), "modalidade": txt(r["modalidade"]) or "—",
                         "tipo": txt(r["tipo"]) or "—", "cliente": txt(r["cliente"]), "previsto": num(r["previsto"]),
                         "recebido": num(r["recebido"]), "forma": txt(r["forma"]) or "—", "status": txt(r["status"])})
    despesas = []
    for r in _tabela(book, "Despesas", avisos):
        d = parse_data(r["data"])
        despesas.append({"data": d, "mes": parse_mes(r["mes"]) or mkey(d), "categoria": txt(r["categoria"]) or "Outros",
                         "descricao": txt(r["descricao"]), "tipo": "Fixa" if norm(r["tipo"]).startswith("fix") else "Variável",
                         "centro": txt(r["centro"]) or "—", "valor": num(r["valor"])})
    leads = []
    for r in _tabela(book, "Leads", avisos):
        d = parse_data(r["data"])
        exp, comp, mat = sim(r["experimental"]), sim(r["compareceu"]), sim(r["matriculou"])
        status = txt(r["status"]) or ("Matriculado" if mat else "Sem comparecimento" if not comp else "Não convertido")
        leads.append({"data": d, "mk": mkey(d), "nome": txt(r["nome"]), "origem": txt(r["origem"]) or "—",
                      "interesse": txt(r["interesse"]) or "—", "experimental": exp, "compareceu": comp, "matriculou": mat,
                      "valor_plano": num(r["valor_plano"]), "cac": num(r["cac"]), "status": status})
    churn_rows = [{"base": r["base"], "novos": num(r["novos"]), "cancel": num(r["cancel"])}
                  for r in _tabela(book, "Churn_Cancelamentos", avisos)]
    ocupacao = []
    for r in _tabela(book, "Ocupacao_Horarios", avisos):
        cap, mat = num(r["capacidade"]), num(r["matriculados"])
        oc = mat / cap if cap > 0 else None
        ocupacao.append({"horario": txt(r["horario"]), "capacidade": cap, "matriculados": mat, "presenca": num(r["presenca"]),
                         "ocup": oc, "status": status_ocup(oc)})
    notas = _tabela(book, "NotasFiscais", []) if _aba(book, "NotasFiscais") is not None else []
    D = {"prem": P, "alunos": alunos, "turmas": turmas, "receitas": receitas, "despesas": despesas, "leads": leads,
         "churn_rows": churn_rows, "ocupacao": ocupacao, "notas_planilha": notas}
    return D, avisos


# ----------------------------------------------------------------------------
# Base de 12 meses (DRE, caixa, churn) — independente de filtros
# ----------------------------------------------------------------------------
def base_12m(D) -> dict:
    P = D["prem"]
    fin = sorted({x["mes"] for x in D["receitas"] + D["despesas"] if x["mes"]})
    outros = sorted({x for x in [a["mk"] for a in D["alunos"]] + [l["mk"] for l in D["leads"]] if x})
    primeiro = (fin or outros or [mkey(dt.date.today())])[0]
    meses = [add_meses(primeiro, i) for i in range(12)]
    ativos = [a for a in D["alunos"] if a["status"] == "Ativo"]
    ticket = sum(a["mensalidade"] for a in ativos) / len(ativos) if ativos else 0
    dre, ult_rb, ult_real = [], None, -1
    for i, k in enumerate(meses):
        rec = [r for r in D["receitas"] if r["mes"] == k]
        des = [d for d in D["despesas"] if d["mes"] == k]
        real = bool(rec or des)
        if real:
            rb = sum(r["previsto"] for r in rec)
            inad = rb - sum(r["recebido"] for r in rec)
            rl = rb - inad
            cv = sum(d["valor"] for d in des if d["tipo"] == "Variável") if des else rl * (1 - P["margem"])
            cf = sum(d["valor"] for d in des if d["tipo"] == "Fixa") if des else P["custo_fixo"]
            ult_rb, ult_real = rb, i
        else:
            base = ult_rb if ult_rb is not None else len(ativos) * ticket
            rb = base * (1 + P["cresc"]) ** (i - ult_real)
            inad = rb * (1 - P["taxa_receb"])
            cv = (rb - inad) * (1 - P["margem"])
            cf = P["custo_fixo"]
        rl = rb - inad
        dre.append({"k": k, "rotulo": mlabel(k), "real": real, "rb": rb, "inad": inad, "rl": rl, "cv": cv, "mc": rl - cv,
                    "cf": cf, "res": rl - cv - cf})
    saldo = 0
    for m in dre:
        saldo += m["rl"] - m["cv"] - m["cf"]
        m["saldo"] = saldo
    churn12, b = [], num(D["churn_rows"][0]["base"]) if D["churn_rows"] else 0
    for i, r in enumerate(D["churn_rows"]):
        ini = b
        fim = ini + r["novos"] - r["cancel"]
        ch = r["cancel"] / ini if ini > 0 else 0
        churn12.append({"rotulo": mlabel(add_meses(primeiro, i)), "ini": ini, "novos": r["novos"], "cancel": r["cancel"],
                        "fim": fim, "churn": ch, "ret": 1 - ch})
        b = fim
    datas = [x for a in D["alunos"] for x in (a["matricula"], a["cancelamento"]) if x] + \
            [x["data"] for x in D["receitas"] + D["despesas"] + D["leads"] if x["data"]]
    return {"meses": meses, "rotulos": [mlabel(k) for k in meses], "dre": dre, "churn12": churn12, "ult_real": ult_real,
            "ativos_total": len(ativos), "ticket_total": ticket, "ultima_data": max(datas) if datas else None}


def periodos(D, notas=()) -> list[str]:
    ks = {x["mes"] for x in D["receitas"] + D["despesas"]} | {a["mk"] for a in D["alunos"]} | {l["mk"] for l in D["leads"]}
    ks |= {n["mes"] for n in notas}
    return sorted(k for k in ks if k)


def modalidades(D) -> list[str]:
    vistos, out = set(), []
    for m in [t["modalidade"] for t in D["turmas"]] + [a["modalidade"] for a in D["alunos"]] + [l["interesse"] for l in D["leads"]]:
        if m and norm(m) not in vistos and norm(m) not in ("diversas", "—", "-"):
            vistos.add(norm(m))
            out.append(m)
    return out


# ----------------------------------------------------------------------------
# Indicadores com filtros (período e modalidade)
# ----------------------------------------------------------------------------
def visao(D, B, periodo: str | None = None, modalidade: str | None = None) -> dict:
    P = D["prem"]
    em = (lambda m: not modalidade or m == modalidade)
    al = [a for a in D["alunos"] if em(a["modalidade"]) and (not periodo or a["mk"] == periodo)]
    rec = [r for r in D["receitas"] if (not periodo or r["mes"] == periodo) and em(r["modalidade"])]
    des = [d for d in D["despesas"] if not periodo or d["mes"] == periodo]
    leads = [l for l in D["leads"] if (not periodo or l["mk"] == periodo) and em(l["interesse"])]
    tur = [t for t in D["turmas"] if em(t["modalidade"])]
    ativos = [a for a in al if a["status"] == "Ativo"]
    canc = [a for a in al if a["status"] == "Cancelado"]
    ticket = sum(a["mensalidade"] for a in ativos) / len(ativos) if ativos else 0           # correção 2
    churn = len(canc) / (len(ativos) + len(canc)) if ativos or canc else 0                 # correção 4
    prev, receb = sum(r["previsto"] for r in rec), sum(r["recebido"] for r in rec)
    inad = (prev - receb) / prev if prev else 0                                             # correção 8
    novos_leads = sum(1 for l in leads if l["matriculou"])
    cac_real = sum(l["cac"] for l in leads) / novos_leads if novos_leads else None
    cac = cac_real if cac_real is not None else P["cac"]
    ltv = ticket * P["margem"] / P["churn"] if P["churn"] > 0 else 0                        # correção 1
    pe = P["custo_fixo"] / P["margem"] if P["margem"] > 0 else 0
    tcap = [t for t in tur if t["capacidade"] > 0]
    exp = sum(1 for l in leads if l["experimental"])
    comp = sum(1 for l in leads if l["experimental"] and l["compareceu"])
    return {
        "al": al, "ativos": ativos, "canc": canc, "rec": rec, "des": des, "leads": leads, "tur": tur, "tcap": tcap,
        "mrr": sum(a["mensalidade"] for a in ativos), "ticket": ticket, "churn": churn, "prev": prev, "receb": receb, "inad": inad,
        "novos_leads": novos_leads, "cac_real": cac_real, "cac": cac, "ltv": ltv, "ltv_cac": ltv / cac if cac else 0,
        "pe": pe, "pe_alunos": math.ceil(pe / ticket) if ticket else None,                    # correção 7
        "ocup": sum(t["ocup"] for t in tcap) / len(tcap) if tcap else 0,                      # correção 6
        "desp": sum(d["valor"] for d in des), "exp": exp, "comp": comp,
        "show_rate": comp / exp if exp else 0, "conv": novos_leads / len(leads) if leads else 0,
        "meta": P["meta"],
    }


def margem_modalidade(tur) -> list[dict]:
    g: dict[str, dict] = {}
    for t in tur:
        x = g.setdefault(t["modalidade"], {"modalidade": t["modalidade"], "alunos": 0, "rec": 0, "custo": 0})
        x["alunos"] += t["matriculados"]
        x["rec"] += t["rec_pot"]
        x["custo"] += t["custo"]
    out = [{**x, "margem": x["rec"] - x["custo"], "pct": (x["rec"] - x["custo"]) / x["rec"] if x["rec"] else None} for x in g.values()]
    return sorted(out, key=lambda x: -x["margem"])


def alertas(D, B, V) -> list[dict]:
    P, A = D["prem"], []
    neg = sum(1 for m in B["dre"] if m["res"] < 0)
    acc = sum(m["res"] for m in B["dre"])
    if neg:
        A.append({"sev": "Crítico", "t": "Resultado negativo em todos os 12 meses" if neg == 12 else f"Resultado negativo em {neg} de 12 meses",
                  "s": f"Déficit acumulado de {brl0(abs(acc))}.", "a": "Teste no simulador (Projeções) mais alunos, ticket maior ou custos menores."})
    pm = len(V["ativos"]) / P["meta"] if P["meta"] else 0
    A.append({"sev": "Crítico" if pm < .5 else "Atenção", "t": f"Base atual = {pct(pm)} da meta",
              "s": f"{len(V['ativos'])} de {int(P['meta'])} alunos ativos.", "a": "Concentre a captação nos canais que mais convertem."})
    baixas = sorted((t for t in V["tcap"] if t["ocup"] < .5), key=lambda t: t["ocup"])
    if baixas:
        t = baixas[0]
        A.append({"sev": "Atenção", "t": f"Turma {t['codigo']} com ocupação de {pct(t['ocup'], 0)}",
                  "s": f"{int(t['matriculados'])} de {int(t['capacidade'])} vagas · {t['modalidade']} · {t['dia']} {t['horario']}.",
                  "a": "Avalie juntar turmas, mudar o horário ou fazer campanha."})
    if V["prev"] and V["inad"] > 1 - P["taxa_receb"]:
        A.append({"sev": "Atenção", "t": f"Inadimplência de {pct(V['inad'])}", "s": f"{brl(V['prev'] - V['receb'])} em aberto.",
                  "a": "Acione os pendentes e ofereça PIX ou cartão recorrente."})
    return A[:4]


def projecao(D, B, s: dict) -> dict:
    P = D["prem"]
    g = max(-.99, s["cresc"] - (s["churn"] - P["churn"]))  # crescimento da planilha já é líquido com o churn da premissa
    pe = s["custo_fixo"] / s["margem"] if s["margem"] > 0 else math.inf
    linhas, acum = [], 0
    for m in range(12):
        alunos = B["ativos_total"] * (1 + g) ** m
        fat = alunos * s["ticket"]
        acum += fat
        linhas.append({"rotulo": B["rotulos"][m], "alunos": alunos, "fat": fat, "acum": acum, "res": fat * s["margem"] - s["custo_fixo"]})
    be = next((i for i, l in enumerate(linhas) if l["fat"] >= pe), None)
    meta = next((i for i, l in enumerate(linhas) if l["alunos"] >= P["meta"]), None)
    return {"linhas": linhas, "pe": pe, "g": g, "be": be, "meta_idx": meta,
            "alunos_pe": math.ceil(pe / s["ticket"]) if s["ticket"] else None,
            "ltv": s["ticket"] * s["margem"] / s["churn"] if s["churn"] else 0}


# ----------------------------------------------------------------------------
# Formatação pt-BR
# ----------------------------------------------------------------------------
def _milhar(v: float, casas: int) -> str:
    return f"{abs(v):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def brl(v, casas: int = 2) -> str:
    v = num(v)
    return ("-R$ " if v < 0 else "R$ ") + _milhar(v, casas)


def brl0(v) -> str:
    return brl(v, 0)


def money(v) -> str:
    return brl0(v) if abs(num(v)) >= 10000 else brl(v)


def compacto(v) -> str:
    v = num(v)
    s = "-" if v < 0 else ""
    a = abs(v)
    if a >= 1e6:
        return f"{s}R$ {a / 1e6:.1f} mi".replace(".", ",")
    if a >= 1e3:
        return f"{s}R$ {a / 1e3:.1f} mil".replace(".", ",")
    return f"{s}R$ {a:.0f}"


def pct(v, casas: int = 1) -> str:
    return f"{num(v) * 100:.{casas}f}".replace(".", ",") + "%"


def inteiro(v) -> str:
    return _milhar(round(num(v)), 0)


def data_br(d) -> str:
    return d.strftime("%d/%m/%Y") if d else "—"
