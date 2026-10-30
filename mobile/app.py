"""Datalyse · Gestão da Academia — versão para celular (Streamlit).

Mesmos dados e fórmulas corrigidas do painel web, reorganizados para telas pequenas:
cartões em duas colunas, poucos gráficos por tela e navegação na barra inferior.

Rodar:  streamlit run mobile/app.py
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import calculos as calc
import notas as nf
import ui
from ui import C

st.set_page_config(page_title="Academia · Datalyse", page_icon=":material/fitness_center:", layout="centered",
                   initial_sidebar_state="collapsed")
ui.aplicar_tema()

MODELO = Path(__file__).resolve().parent.parent / "Modelo_Gestao_Academia_V2_Executivo.xlsx"
b, p0 = calc.brl, calc.pct


# ----------------------------------------------------------------------------
# Dados
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def planilha_padrao():
    return calc.ler_planilha(MODELO)


book = st.session_state.get("book_enviado") or planilha_padrao()
fonte = st.session_state.get("nome_enviado", "Planilha modelo")
D, AVISOS = calc.carregar(book)
B = calc.base_12m(D)
NOTAS = nf.mesclar([nf.normalizar(r, "planilha") for r in D["notas_planilha"] if r.get("valor") not in (None, "")], nf.carregar())


def filtros_atuais():
    return st.session_state.get("f_per"), st.session_state.get("f_mod")


def cabecalho(titulo: str, sub: str, chave: str, com_filtros: bool = True):
    ui.topo(f"Dados até {calc.data_br(B['ultima_data'])}<br>{ui.e(fonte)}")
    ui.titulo(titulo, sub)
    if AVISOS and chave == "resumo":
        st.warning("Atenção aos dados: " + " ".join(AVISOS), icon=":material/warning:")
    if not com_filtros:
        return
    per, mod = filtros_atuais()
    opcoes_per = [None] + calc.periodos(D, NOTAS)
    opcoes_mod = [None] + calc.modalidades(D)
    rot = f"{'Todos os meses' if not per else calc.mlabel(per)} · {mod or 'Todas as modalidades'}"
    with st.popover(rot, icon=":material/tune:", width="stretch"):
        per = st.selectbox("Período", opcoes_per, index=opcoes_per.index(per) if per in opcoes_per else 0,
                           format_func=lambda k: "Todos" if k is None else calc.mlabel(k), key=f"w_per_{chave}")
        mod = st.selectbox("Modalidade", opcoes_mod, index=opcoes_mod.index(mod) if mod in opcoes_mod else 0,
                           format_func=lambda m: "Todas" if m is None else m, key=f"w_mod_{chave}")
        st.session_state["f_per"], st.session_state["f_mod"] = per, mod


def visao():
    per, mod = filtros_atuais()
    return calc.visao(D, B, per, mod)


# ----------------------------------------------------------------------------
# Páginas
# ----------------------------------------------------------------------------
def pg_resumo():
    cabecalho("Resumo", "Os números que importam hoje", "resumo")
    V, P = visao(), D["prem"]
    at = len(V["ativos"])
    ui.hero("MRR", "Receita recorrente mensal", b(V["mrr"]), at / P["meta"] if P["meta"] else 0,
            f"<b>{at}</b> alunos ativos", f"meta {calc.inteiro(P['meta'])} · <b>{p0(at / P['meta'] if P['meta'] else 0)}</b>")
    ui.kpis([
        {"l": "Receita recebida", "s": "Entrada de caixa", "v": calc.money(V["receb"]), "r": f"de {calc.money(V['prev'])} previstos"},
        {"l": "Ticket médio", "s": "Mensalidade média", "v": b(V["ticket"]), "r": "só alunos ativos"},
        {"l": "Churn Rate", "s": "Taxa de cancelamento", "v": p0(V["churn"]),
         "r": ui.tendencia(f"premissa {p0(P['churn'])}", V["churn"] > P["churn"], V["churn"] > P["churn"])},
        {"l": "LTV/CAC", "s": "Retorno da aquisição", "v": f"{V['ltv_cac']:.1f}x".replace(".", ","),
         "r": ui.tendencia("saudável" if V["ltv_cac"] >= 3 else "abaixo de 3x", V["ltv_cac"] < 3, V["ltv_cac"] >= 3)},
        {"l": "Break-even", "s": "Alunos para empatar", "v": f"{V['pe_alunos']} alunos" if V["pe_alunos"] else "—", "r": f"{calc.brl0(V['pe'])} por mês"},
        {"l": "Inadimplência", "s": "Previsto não recebido", "v": p0(V["inad"]), "neg": V["inad"] > 1 - P["taxa_receb"],
         "r": f"{calc.money(V['prev'] - V['receb'])} em aberto"},
        {"l": "Taxa de ocupação", "s": "Uso das turmas", "v": p0(V["ocup"]), "r": f"{len(V['tcap'])} turmas"},
        {"l": "Novos alunos", "s": "Matrículas no período", "v": calc.inteiro(len(V["al"])), "r": f"{V['novos_leads']} vindos de leads"},
    ])
    ui.secao("Alertas", "Gerados por regras de negócio, com a ação sugerida")
    ui.alertas(calc.alertas(D, B, V))
    ui.secao("Resultado operacional · 12 meses", "Linha sólida = realizado · tracejada = projetado")
    dre = B["dre"]
    fig = go.Figure()
    fig.add_hline(y=0, line=dict(color=C["g500"], width=1))
    fig.add_scatter(x=[m["rotulo"] for m in dre], y=[m["res"] if m["real"] else None for m in dre], name="Realizado",
                    mode="lines+markers", line=dict(color=C["r500"], width=3), marker=dict(size=9),
                    hovertemplate="%{x}: <b>R$ %{y:,.0f}</b><extra>realizado</extra>")
    fig.add_scatter(x=[m["rotulo"] for m in dre], y=[m["res"] if (not m["real"] or i == B["ult_real"]) else None for i, m in enumerate(dre)],
                    name="Projetado", mode="lines+markers", line=dict(color=C["r400"], width=2, dash="dash"), marker=dict(size=5),
                    hovertemplate="%{x}: <b>R$ %{y:,.0f}</b><extra>projetado</extra>")
    ui.grafico(fig, 230)


def pg_financeiro():
    cabecalho("Financeiro", "Receitas, despesas e resultado do período", "fin")
    V, P = visao(), D["prem"]
    res = V["receb"] - V["desp"]
    ui.kpis([
        {"l": "Receita prevista", "s": "Faturamento esperado", "v": calc.money(V["prev"]), "r": f"{len(V['rec'])} lançamentos"},
        {"l": "Receita recebida", "s": "Entrada de caixa", "v": calc.money(V["receb"]), "r": f"{p0(V['receb'] / V['prev'] if V['prev'] else 0)} do previsto"},
        {"l": "Despesas", "s": "Fixas + variáveis", "v": calc.money(V["desp"]), "r": f"{len(V['des'])} lançamentos"},
        {"l": "Resultado", "s": "Lucro ou prejuízo de caixa", "v": calc.money(res), "neg": res < 0,
         "r": ui.tendencia("déficit" if res < 0 else "superávit", res < 0, res >= 0)},
        {"l": "Inadimplência", "s": "Previsto não recebido", "v": p0(V["inad"]), "neg": V["inad"] > 1 - P["taxa_receb"], "r": f"{calc.money(V['prev'] - V['receb'])} em aberto"},
        {"l": "Break-even", "s": "Ponto de equilíbrio", "v": calc.brl0(V["pe"]), "r": f"margem {p0(P['margem'], 0)}"},
    ])
    per, _ = filtros_atuais()
    rec = [r for r in D["receitas"] if not per or r["mes"] == per]
    des = [d for d in D["despesas"] if not per or d["mes"] == per]
    ui.secao("DRE em cascata", "Da receita bruta ao resultado (valores realizados)")
    if rec or des:
        rb = sum(r["previsto"] for r in rec)
        inad = rb - sum(r["recebido"] for r in rec)
        cv = sum(d["valor"] for d in des if d["tipo"] == "Variável")
        cf = sum(d["valor"] for d in des if d["tipo"] == "Fixa")
        fig = go.Figure(go.Waterfall(
            x=["Receita<br>bruta", "Inadim-<br>plência", "Custos<br>variáveis", "Margem", "Custos<br>fixos", "Resultado"],
            measure=["absolute", "relative", "relative", "total", "relative", "total"], y=[rb, -inad, -cv, 0, -cf, 0],
            text=[calc.compacto(v) for v in [rb, -inad, -cv, rb - inad - cv, -cf, rb - inad - cv - cf]], textposition="outside",
            textfont=dict(color=C["text"], size=10), connector=dict(line=dict(color=C["g500"], width=1, dash="dot")),
            increasing=dict(marker=dict(color=C["g300"])), decreasing=dict(marker=dict(color=C["r700"], line=dict(color=C["r500"], width=1))),
            totals=dict(marker=dict(color=C["r500"])), hovertemplate="%{x}: <b>R$ %{y:,.2f}</b><extra></extra>"))
        fig.update_yaxes(showticklabels=False)
        ui.grafico(fig, 260, legenda=False)
    else:
        st.info("Sem lançamentos no período.", icon=":material/inbox:")
    ui.secao("Despesas por categoria")
    cats = {}
    for d in V["des"]:
        cats[d["categoria"]] = cats.get(d["categoria"], 0) + d["valor"]
    if cats:
        itens = sorted(cats.items(), key=lambda x: x[1])
        tot = sum(cats.values())
        fig = go.Figure(go.Bar(y=[k for k, _ in itens], x=[v for _, v in itens], orientation="h", marker=dict(color=C["r500"], cornerradius=4),
                               text=[f"{calc.compacto(v)} · {p0(v / tot, 0)}" for _, v in itens], textposition="outside",
                               textfont=dict(color=C["text"], size=10.5), cliponaxis=False, hovertemplate="%{y}: <b>R$ %{x:,.2f}</b><extra></extra>"))
        fig.update_xaxes(showticklabels=False, showgrid=False, range=[0, max(cats.values()) * 1.45])
        ui.grafico(fig, 40 + 30 * len(itens), legenda=False)
    with st.expander("DRE gerencial · 12 meses", icon=":material/table_chart:"):
        linhas = [("Receita bruta", "rb"), ("(−) Inadimplência", "inad"), ("Receita líquida", "rl"), ("(−) Custos variáveis", "cv"),
                  ("Margem de contribuição", "mc"), ("(−) Custos fixos", "cf"), ("Resultado", "res")]
        tabela = {"Mês": [m["rotulo"] + ("" if m["real"] else " *") for m in B["dre"]]}
        for nome, k in linhas:
            tabela[nome] = [calc.brl0(m[k]) for m in B["dre"]]
        st.dataframe(tabela, hide_index=True, width="stretch")
        st.caption("* mês projetado a partir das premissas")


def _form_nota():
    @st.dialog("Adicionar nota fiscal", width="small")
    def dialogo():
        st.caption("Envie o XML da NF-e/NFS-e para preencher sozinho, ou digite os dados.")
        arq = st.file_uploader("XML da nota (opcional)", type=["xml"], key="nf_xml")
        pre = {}
        if arq is not None:
            try:
                pre = nf.ler_xml(arq.getvalue())
                st.success("XML lido. Confira os campos e escolha a categoria.", icon=":material/check_circle:")
            except ValueError as err:
                st.error(str(err))
        sufixo = arq.file_id if arq is not None else "manual"
        cats = sorted({d["categoria"] for d in D["despesas"]} | {"Produtos", "Mensalidades", "Serviços", "Outros"})
        with st.form(f"nf_form_{sufixo}", border=False):
            tipo = st.radio("Tipo", ["Entrada", "Saída"], horizontal=True, captions=["compra ou serviço", "emitida pela academia"])
            c1, c2 = st.columns(2)
            data = c1.date_input("Emissão", value=calc.parse_data(pre.get("data")) or dt.date.today(), format="DD/MM/YYYY")
            numero = c2.text_input("Número", value=pre.get("numero", ""))
            c3, c4 = st.columns(2)
            serie = c3.text_input("Série", value=pre.get("serie", ""))
            valor = c4.number_input("Valor (R$)", min_value=0.0, step=10.0, format="%.2f", value=calc.num(pre.get("valor")))
            parceiro = st.text_input("Emitente / destinatário", value=pre.get("parceiro", ""))
            doc = st.text_input("CNPJ / CPF", value=nf.fmt_doc(pre.get("doc", "")))
            categoria = st.selectbox("Categoria", cats, index=None, placeholder="Escolha ou digite", accept_new_options=True)
            descricao = st.text_input("Descrição", value=pre.get("descricao", ""))
            status = st.radio("Status", ["Válida", "Cancelada"], horizontal=True)
            chave = st.text_input("Chave de acesso (44 dígitos, opcional)", value=pre.get("chave", ""))
            ok = st.form_submit_button("Salvar nota", type="primary", width="stretch")
        if ok:
            faltam = [n for n, v in [("número", numero.strip()), ("emitente/destinatário", parceiro.strip()), ("valor", valor > 0)] if not v]
            digitos = "".join(c for c in chave if c.isdigit())
            if faltam:
                st.error("Preencha: " + ", ".join(faltam) + ".")
            elif digitos and len(digitos) != 44:
                st.error("A chave de acesso deve ter 44 dígitos (ou deixe em branco).")
            else:
                nova = nf.normalizar({"data": data, "numero": numero, "serie": serie, "tipo": tipo, "parceiro": parceiro, "doc": doc,
                                      "descricao": descricao, "categoria": categoria or "Outros", "valor": valor, "status": status,
                                      "chave": digitos}, "app")
                erro = nf.adicionar(nova) if not any(nf.chave_unica(n) == nf.chave_unica(nova) for n in NOTAS) else \
                    "Esta nota já está lançada (mesmo número, série e emitente ou mesma chave)."
                if erro:
                    st.error(erro)
                else:
                    st.session_state["_aviso"] = f"Nota {numero} adicionada"
                    st.rerun()

    dialogo()


def pg_notas():
    cabecalho("Notas fiscais", "Controle das notas de entrada e de saída", "nf")
    per, _ = filtros_atuais()
    lista = [n for n in NOTAS if not per or n["mes"] == per]
    val = [n for n in lista if n["status"] == "Válida"]
    ent, sai = [n for n in val if n["tipo"] == "Entrada"], [n for n in val if n["tipo"] == "Saída"]
    des = [d for d in D["despesas"] if not per or d["mes"] == per]
    cats = sorted({d["categoria"] for d in des} | {n["categoria"] for n in ent})
    conc = [(c, sum(d["valor"] for d in des if d["categoria"] == c), sum(n["valor"] for n in ent if n["categoria"] == c)) for c in cats]
    tot_des = sum(x[1] for x in conc)
    coberto = sum(min(d, n) for _, d, n in conc)
    cob = coberto / tot_des if tot_des else 0
    if st.button("Adicionar nota fiscal", icon=":material/add:", type="primary", width="stretch"):
        _form_nota()
    ui.kpis([
        {"l": "Notas no período", "s": "Notas válidas", "v": calc.inteiro(len(val)), "r": f"{len(lista) - len(val)} cancelada(s)"},
        {"l": "Entradas", "s": "Compras e serviços", "v": calc.money(sum(n["valor"] for n in ent)), "r": f"{len(ent)} nota(s)"},
        {"l": "Saídas", "s": "Emitidas pela academia", "v": calc.money(sum(n["valor"] for n in sai)), "r": f"{len(sai)} nota(s)"},
        {"l": "Cobertura fiscal", "s": "Despesas com nota", "v": p0(cob), "r": ui.tendencia("boa" if cob >= .8 else "abaixo de 80%", cob < .8, cob >= .8) if tot_des else ""},
    ])
    if tot_des - coberto > 0:
        st.markdown(f'<div class="nota">{calc.money(tot_des - coberto)} em despesas do período sem nota fiscal. '
                    f'Folha de pagamento e aluguel costumam ter outros comprovantes (holerite, recibo).</div>', unsafe_allow_html=True)
    ui.secao("Notas lançadas")
    tipo = st.segmented_control("Tipo", ["Todas", "Entradas", "Saídas"], default="Todas", label_visibility="collapsed", width="stretch")
    busca = st.text_input("Buscar", placeholder="Número, fornecedor ou descrição", label_visibility="collapsed", icon=":material/search:")
    q = calc.norm(busca)
    mostrar = [n for n in lista if (tipo in (None, "Todas") or n["tipo"] == ("Entrada" if tipo == "Entradas" else "Saída"))
               and (not q or q in calc.norm(" ".join([n["numero"], n["serie"], n["parceiro"], n["descricao"], n["categoria"], n["doc"]])))]
    mostrar.sort(key=lambda n: n["data"] or dt.date.min, reverse=True)
    if not mostrar:
        st.info("Nenhuma nota encontrada.", icon=":material/inbox:")
    for n in mostrar[:30]:
        tag = '<span class="tg in">↓ Entrada</span>' if n["tipo"] == "Entrada" else '<span class="tg out">↑ Saída</span>'
        if n["status"] == "Cancelada":
            tag += '<span class="tg bad">Cancelada</span>'
        sub = f'Nº {ui.e(n["numero"])}{" / " + ui.e(n["serie"]) if n["serie"] else ""} · {ui.e(n["categoria"])}<br>{ui.e(n["descricao"])}'
        ui.item(n["parceiro"], sub, b(n["valor"]), calc.data_br(n["data"]), "canc" if n["status"] == "Cancelada" else "", tag)
    if len(mostrar) > 30:
        st.caption(f"Mostrando 30 de {len(mostrar)} notas. Use a busca para encontrar as demais.")
    if conc:
        ui.secao("Conciliação por categoria", "Despesas lançadas × notas de entrada")
        conc_ord = sorted(conc, key=lambda x: x[1])
        fig = go.Figure()
        fig.add_bar(y=[c for c, _, _ in conc_ord], x=[d for _, d, _ in conc_ord], name="Despesas", orientation="h",
                    marker=dict(color=C["g500"], cornerradius=3), hovertemplate="%{y}: <b>R$ %{x:,.2f}</b><extra>despesas</extra>")
        fig.add_bar(y=[c for c, _, _ in conc_ord], x=[n for _, _, n in conc_ord], name="Notas de entrada", orientation="h",
                    marker=dict(color=C["r500"], cornerradius=3), hovertemplate="%{y}: <b>R$ %{x:,.2f}</b><extra>notas</extra>")
        fig.update_layout(barmode="group", bargap=.25)
        fig.update_xaxes(tickprefix="R$ ", tickformat="~s")
        ui.grafico(fig, 60 + 38 * len(conc_ord))
    app = [n for n in NOTAS if n["origem"] == "app"]
    with st.expander("Excluir uma nota", icon=":material/delete:"):
        if app:
            alvo = st.selectbox("Nota", app, format_func=lambda n: f"Nº {n['numero']} · {n['parceiro']} · {b(n['valor'])}", key="nf_del")
            if st.button("Excluir nota", width="stretch"):
                nf.excluir(alvo["id"])
                st.session_state["_aviso"] = f"Nota {alvo['numero']} excluída"
                st.rerun()
        else:
            st.caption("Nenhuma nota lançada pelo app.")
    st.download_button("Baixar planilha com as notas", nf.exportar_xlsx(book, NOTAS), icon=":material/download:", width="stretch",
                       file_name=f"Academia_dados_{dt.date.today().isoformat()}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.markdown('<div class="nota">A planilha baixada traz todas as abas mais a aba NotasFiscais, e pode ser carregada no painel web.</div>',
                unsafe_allow_html=True)


def pg_alunos():
    cabecalho("Alunos", "Base, cancelamentos e retenção", "alu")
    V, P = visao(), D["prem"]
    hoje = dt.date.today()
    casa = [(hoje - a["matricula"]).days for a in V["ativos"] if a["matricula"]]
    ui.kpis([
        {"l": "Base ativa", "s": "Matrículas ativas", "v": calc.inteiro(len(V["ativos"])), "r": f"{len(V['al'])} no filtro"},
        {"l": "Cancelamentos", "s": "Alunos que saíram", "v": calc.inteiro(len(V["canc"])), "r": "no período"},
        {"l": "Churn Rate", "s": "Taxa de cancelamento", "v": p0(V["churn"]), "r": ui.tendencia(f"premissa {p0(P['churn'])}", V["churn"] > P["churn"], V["churn"] > P["churn"])},
        {"l": "Retention Rate", "s": "Taxa de retenção", "v": p0(1 - V["churn"] if V["al"] else 0), "r": "1 − churn rate"},
        {"l": "Tempo de casa", "s": "Média dos ativos", "v": f"{round(sum(casa) / len(casa))} dias" if casa else "—", "r": "desde a matrícula"},
        {"l": "LTV", "s": "Valor gerado pelo aluno", "v": calc.money(V["ltv"]), "r": f"ticket {b(V['ticket'])}"},
    ])
    if B["churn12"]:
        ui.secao("Churn × retenção · 12 meses")
        ch = B["churn12"]
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_scatter(x=[c["rotulo"] for c in ch], y=[c["churn"] for c in ch], name="Churn", line=dict(color=C["r500"], width=3),
                        hovertemplate="%{x}: <b>%{y:.1%}</b><extra>churn</extra>", secondary_y=False)
        fig.add_scatter(x=[c["rotulo"] for c in ch], y=[c["ret"] for c in ch], name="Retenção", line=dict(color=C["g300"], width=2),
                        hovertemplate="%{x}: <b>%{y:.1%}</b><extra>retenção</extra>", secondary_y=True)
        fig.update_yaxes(tickformat=".0%", secondary_y=False, rangemode="tozero")
        fig.update_yaxes(tickformat=".0%", secondary_y=True, showgrid=False)
        ui.grafico(fig, 220)
    ui.secao("Cadastro")
    busca = st.text_input("Buscar aluno", placeholder="Nome do aluno", label_visibility="collapsed", icon=":material/search:")
    q = calc.norm(busca)
    for a in sorted((a for a in V["al"] if not q or q in calc.norm(a["nome"])), key=lambda a: (a["status"] != "Ativo", a["nome"])):
        tag = '<span class="tg out">Ativo</span>' if a["status"] == "Ativo" else '<span class="tg bad">Cancelado</span>'
        ui.item(a["nome"], f'{ui.e(a["modalidade"])} · {ui.e(a["plano"])} · {ui.e(a["origem"])}', b(a["mensalidade"]),
                f"desde {calc.data_br(a['matricula'])}", "", tag)


def pg_comercial():
    cabecalho("Comercial", "Do lead à matrícula", "com")
    V = visao()
    ui.kpis([
        {"l": "Leads", "s": "Interessados", "v": calc.inteiro(len(V["leads"])), "r": f"{len({l['origem'] for l in V['leads']})} origens"},
        {"l": "Experimentais", "s": "Aulas agendadas", "v": calc.inteiro(V["exp"]), "r": f"{p0(V['exp'] / len(V['leads']) if V['leads'] else 0)} dos leads"},
        {"l": "Show Rate", "s": "Comparecimento", "v": p0(V["show_rate"]), "r": f"{V['comp']} de {V['exp']}"},
        {"l": "Conversion Rate", "s": "Taxa de conversão", "v": p0(V["conv"]), "r": f"{V['novos_leads']} matrículas"},
        {"l": "CAC", "s": "Custo por aluno", "v": b(V["cac"]), "r": "real" if V["cac_real"] is not None else "premissa"},
        {"l": "LTV/CAC", "s": "Retorno da aquisição", "v": f"{V['ltv_cac']:.1f}x".replace(".", ","),
         "r": ui.tendencia("saudável" if V["ltv_cac"] >= 3 else "abaixo de 3x", V["ltv_cac"] < 3, V["ltv_cac"] >= 3)},
    ])
    if not V["leads"]:
        st.info("Sem leads no período.", icon=":material/inbox:")
        return
    ui.secao("Funil de conversão")
    etapas = ["Leads", "Experimental", "Compareceram", "Matricularam"]
    vals = [len(V["leads"]), V["exp"], V["comp"], V["novos_leads"]]
    fig = go.Figure(go.Funnel(y=etapas, x=vals, textinfo="value+percent previous", marker=dict(color=[C["g500"], C["r700"], C["r600"], C["r500"]]),
                              textfont=dict(color=C["text"]), connector=dict(fillcolor=C["surface2"]), hovertemplate="%{y}: <b>%{x}</b><extra></extra>"))
    ui.grafico(fig, 220, legenda=False)
    ui.secao("Leads × matrículas por origem")
    orig = sorted({l["origem"] for l in V["leads"]})
    fig = go.Figure()
    fig.add_bar(x=orig, y=[sum(1 for l in V["leads"] if l["origem"] == o) for o in orig], name="Leads", marker=dict(color=C["g500"], cornerradius=4))
    fig.add_bar(x=orig, y=[sum(1 for l in V["leads"] if l["origem"] == o and l["matriculou"]) for o in orig], name="Matrículas",
                marker=dict(color=C["r500"], cornerradius=4))
    fig.update_layout(barmode="group")
    fig.update_yaxes(dtick=1)
    ui.grafico(fig, 220)


def pg_operacao():
    cabecalho("Operação", "Turmas, ocupação e margem", "op")
    V = visao()
    cap, mat = sum(t["capacidade"] for t in V["tur"]), sum(t["matriculados"] for t in V["tur"])
    pres = sum(t["presenca"] for t in V["tur"])
    ui.kpis([
        {"l": "Taxa de ocupação", "s": "Uso da capacidade", "v": p0(V["ocup"]), "r": f"{len(V['tcap'])} turmas"},
        {"l": "Taxa de presença", "s": "Comparecem às aulas", "v": p0(pres / mat if mat else 0), "r": f"{calc.inteiro(pres)} por aula"},
        {"l": "Matriculados", "s": "Vagas ocupadas", "v": calc.inteiro(mat), "r": f"de {calc.inteiro(cap)} vagas"},
        {"l": "Vagas livres", "s": "Receita potencial", "v": calc.inteiro(max(0, cap - mat)), "r": "para campanhas"},
    ])
    if V["tcap"]:
        ui.secao("Ocupação por turma", "Referências em 50% e 80%")
        tc = sorted(V["tcap"], key=lambda t: t["ocup"])
        cor = {"Alta": C["r500"], "Média": C["r300"], "Baixa": C["g500"]}
        fig = go.Figure(go.Bar(y=[f"{t['codigo']}" for t in tc], x=[t["ocup"] for t in tc], orientation="h",
                               marker=dict(color=[cor[t["status"]] for t in tc], cornerradius=4),
                               text=[p0(t["ocup"], 0) for t in tc], textposition="outside", textfont=dict(color=C["text"], size=10.5), cliponaxis=False,
                               customdata=[[t["modalidade"], t["dia"], t["horario"], int(t["matriculados"]), int(t["capacidade"])] for t in tc],
                               hovertemplate="<b>%{y}</b> · %{customdata[0]}<br>%{customdata[1]} %{customdata[2]}<br>%{customdata[3]}/%{customdata[4]} vagas<extra></extra>"))
        for ref in (.5, .8):
            fig.add_vline(x=ref, line=dict(color=C["g500"], width=1, dash="dot"))
        fig.update_xaxes(tickformat=".0%", range=[0, max(1.1, max(t["ocup"] for t in tc) * 1.15)])
        ui.grafico(fig, 50 + 26 * len(tc), legenda=False)
    ui.secao("Margem por modalidade", "Receita potencial das turmas − custo das turmas")
    for m in calc.margem_modalidade(V["tur"]):
        neg = m["margem"] < 0
        ui.item(m["modalidade"], f'{calc.inteiro(m["alunos"])} matrículas · receita {calc.brl0(m["rec"])} · custo {calc.brl0(m["custo"])}',
                calc.brl0(m["margem"]), p0(m["pct"]) if m["pct"] is not None else "—", "", '<span class="tg bad">negativa</span>' if neg else "")


def pg_projecoes():
    cabecalho("Projeções", "Simule cenários para os próximos 12 meses", "proj", com_filtros=False)
    P = D["prem"]
    with st.expander("Simulador “E se?”", icon=":material/tune:", expanded=True):
        cresc = st.slider("Crescimento mensal (%)", 0.0, 15.0, P["cresc"] * 100, .5, format="%.1f%%") / 100
        churn = st.slider("Churn mensal (%)", 0.0, 15.0, P["churn"] * 100, .5, format="%.1f%%") / 100
        ticket = st.slider("Ticket médio (R$)", 80, 400, int(round(B["ticket_total"] or P["mens_lutas"])), 5)
        custo = st.slider("Custos fixos (R$)", 5000, 40000, int(P["custo_fixo"]), 500)
        margem = st.slider("Margem de contribuição (%)", 30, 90, int(round(P["margem"] * 100)), 1) / 100
    pr = calc.projecao(D, B, {"cresc": cresc, "churn": churn, "ticket": ticket, "custo_fixo": custo, "margem": margem})
    ult = pr["linhas"][-1]
    ui.kpis([
        {"l": "Resultado no mês 12", "s": "Lucro ou prejuízo", "v": calc.money(ult["res"]), "neg": ult["res"] < 0, "r": ult["rotulo"]},
        {"l": "Break-even", "s": "Mês em que empata", "v": pr["linhas"][pr["be"]]["rotulo"] if pr["be"] is not None else "Não atinge",
         "r": f"precisa de {calc.brl0(pr['pe'])}/mês"},
        {"l": "Alunos p/ break-even", "s": "Base mínima", "v": calc.inteiro(pr["alunos_pe"]) if pr["alunos_pe"] else "—", "r": f"ticket {calc.brl0(ticket)}"},
        {"l": "LTV simulado", "s": "Valor do aluno", "v": calc.money(pr["ltv"]), "r": f"crescimento líquido {p0(pr['g'])}"},
    ])
    ui.secao("Faturamento projetado", "Linha tracejada = ponto de equilíbrio")
    L = pr["linhas"]
    fig = go.Figure()
    fig.add_scatter(x=[l["rotulo"] for l in L], y=[l["fat"] for l in L], name="Faturamento", mode="lines+markers",
                    line=dict(color=C["g300"], width=3), hovertemplate="%{x}: <b>R$ %{y:,.0f}</b><extra></extra>")
    fig.add_hline(y=pr["pe"], line=dict(color=C["r300"], width=1.5, dash="dash"),
                  annotation=dict(text=f"break-even {calc.compacto(pr['pe'])}", font=dict(color=C["r300"], size=10.5)), annotation_position="top left")
    fig.update_yaxes(tickprefix="R$ ", tickformat="~s", rangemode="tozero")
    ui.grafico(fig, 230, legenda=False)
    ui.secao("Alunos projetados × meta")
    if pr["meta_idx"] is None:
        st.markdown(f'<div class="al at"><div class="t">Meta de {calc.inteiro(P["meta"])} alunos não atingida em 12 meses</div>'
                    f'<div class="s">Faltam {calc.inteiro(P["meta"] - L[-1]["alunos"])} alunos no mês 12.</div></div>', unsafe_allow_html=True)
    fig = go.Figure(go.Bar(x=[l["rotulo"] for l in L], y=[l["alunos"] for l in L], marker=dict(color=C["r500"], cornerradius=4),
                           hovertemplate="%{x}: <b>%{y:.1f}</b> alunos<extra></extra>"))
    fig.add_hline(y=P["meta"], line=dict(color=C["r300"], width=1.5, dash="dash"),
                  annotation=dict(text=f"meta {calc.inteiro(P['meta'])}", font=dict(color=C["r300"], size=10.5)), annotation_position="top left")
    ui.grafico(fig, 220, legenda=False)


def pg_planilha():
    cabecalho("Planilha", "Atualize os dados ou baixe uma cópia", "plan", com_filtros=False)
    st.markdown(f'<div class="nota">Fonte atual: <b>{ui.e(fonte)}</b>. Envie uma versão nova do modelo '
                f'<i>Modelo_Gestao_Academia_V2_Executivo.xlsx</i> e todos os indicadores são recalculados.</div>', unsafe_allow_html=True)
    arq = st.file_uploader("Planilha atualizada (.xlsx)", type=["xlsx", "xlsm"])
    if arq is not None and st.button("Usar esta planilha", type="primary", width="stretch"):
        try:
            novo = calc.ler_planilha(arq)
            calc.carregar(novo)
            st.session_state["book_enviado"], st.session_state["nome_enviado"] = novo, arq.name
            st.session_state["_aviso"] = f"Planilha “{arq.name}” carregada"
            st.rerun()
        except Exception as err:  # arquivo corrompido ou fora do modelo
            st.error(f"Não foi possível ler a planilha: {err}")
    if "book_enviado" in st.session_state and st.button("Voltar à planilha modelo", width="stretch"):
        st.session_state.pop("book_enviado"), st.session_state.pop("nome_enviado", None)
        st.rerun()
    st.download_button("Baixar planilha com as notas fiscais", nf.exportar_xlsx(book, NOTAS), icon=":material/download:", width="stretch",
                       file_name=f"Academia_dados_{dt.date.today().isoformat()}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.markdown('<div class="nota" style="margin-top:14px">Versão completa, com todos os gráficos e filtros, no painel web para computador.</div>',
                unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Navegação: barra inferior estilo aplicativo
# ----------------------------------------------------------------------------
PAGINAS = {
    "resumo": st.Page(pg_resumo, title="Resumo", icon=":material/space_dashboard:", url_path="resumo", default=True),
    "financeiro": st.Page(pg_financeiro, title="Finanças", icon=":material/payments:", url_path="financeiro"),
    "notas": st.Page(pg_notas, title="Notas", icon=":material/receipt_long:", url_path="notas"),
    "alunos": st.Page(pg_alunos, title="Alunos", icon=":material/groups:", url_path="alunos"),
    "comercial": st.Page(pg_comercial, title="Comercial", icon=":material/campaign:", url_path="comercial"),
    "operacao": st.Page(pg_operacao, title="Operação", icon=":material/fitness_center:", url_path="operacao"),
    "projecoes": st.Page(pg_projecoes, title="Projeções", icon=":material/trending_up:", url_path="projecoes"),
    "planilha": st.Page(pg_planilha, title="Planilha", icon=":material/upload_file:", url_path="planilha"),
}
nav = st.navigation(list(PAGINAS.values()), position="hidden")

aviso = st.session_state.pop("_aviso", None)
if aviso:
    st.toast(aviso, icon=":material/check_circle:")

nav.run()

with st.container(key="barra", horizontal=True):
    for k in ("resumo", "financeiro", "notas", "alunos"):
        st.page_link(PAGINAS[k], label=PAGINAS[k].title, icon=PAGINAS[k].icon, width="stretch")
    with st.popover("Mais", icon=":material/more_horiz:", width="stretch"):
        for k in ("comercial", "operacao", "projecoes", "planilha"):
            st.page_link(PAGINAS[k], label=PAGINAS[k].title, icon=PAGINAS[k].icon, width="stretch")
