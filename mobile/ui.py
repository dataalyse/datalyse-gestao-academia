"""Tema e componentes da versão para celular (preto e vermelho, igual ao painel)."""
from __future__ import annotations

import html

import plotly.graph_objects as go
import streamlit as st

C = {"bg": "#0B0B0C", "surface": "#141416", "surface2": "#1C1C1F", "border": "#2A2A2E", "grid": "#222225",
     "text": "#F2F0EE", "muted": "#9A979A", "r700": "#6E1F24", "r600": "#8E2A30", "r500": "#A63A40",
     "r400": "#C0595E", "r300": "#D48A8D", "r200": "#E6BDBE", "g500": "#6B686C", "g300": "#B5B2B4"}
PALETA = [C["r500"], C["r300"], C["r700"], C["g300"], C["r400"], C["g500"]]

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@500;600;700&display=swap');
html,body,.stApp,[data-testid="stAppViewContainer"]{background:#0B0B0C!important;color:#F2F0EE}
.stApp,.stApp p,.stApp label,.stApp input,.stApp textarea,.stApp button,.stApp li{font-family:'Inter',system-ui,sans-serif}
.stApp h1,.stApp h2,.stApp h3{font-family:'Sora',system-ui,sans-serif!important;letter-spacing:-.01em}
.stApp::before{content:"";position:fixed;inset:0 0 auto 0;height:2px;background:#8E2A30;z-index:1001}
header[data-testid="stHeader"],[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="stDecoration"],
[data-testid="stToolbar"],[data-testid="stStatusWidget"]{display:none!important}
.block-container,[data-testid="stMainBlockContainer"]{max-width:520px!important;padding:14px 14px 104px!important;margin:0 auto}
[data-testid="stVerticalBlock"]{gap:.65rem}
/* topo */
.topo{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:4px 0 2px}
.topo .m{display:flex;align-items:center;gap:9px}
.topo .n{font:700 16px/1.1 'Sora';color:#F2F0EE}
.topo .s{font:600 9.5px 'Inter';letter-spacing:.09em;text-transform:uppercase;color:#9A979A}
.topo .d{font-size:11px;color:#9A979A;text-align:right;line-height:1.3}
.pg{font:600 22px/1.2 'Sora';margin:6px 0 0;color:#F2F0EE}
.pg-s{font-size:12.5px;color:#9A979A;margin:2px 0 4px}
.sec{font:600 14.5px 'Sora';margin:12px 0 2px;color:#F2F0EE}
.sec-s{font-size:11.5px;color:#9A979A;margin:0 0 2px}
/* cartões */
.hero{background:linear-gradient(135deg,#1C1C1F 0%,#141416 55%,rgba(110,31,36,.55) 130%);border:1px solid #2A2A2E;border-radius:18px;padding:16px 16px 14px}
.hero .l{font:700 10.5px 'Inter';letter-spacing:.08em;text-transform:uppercase;color:#C9C6C8}
.hero .s{font-size:11px;color:#9A979A}
.hero .v{font:600 30px/1.1 'Sora';margin:8px 0 10px;color:#F2F0EE}
.hero .bar{height:8px;border-radius:5px;background:#2A2A2E;overflow:hidden}
.hero .bar i{display:block;height:100%;border-radius:5px;background:linear-gradient(90deg,#8E2A30,#C0595E)}
.hero .r{display:flex;justify-content:space-between;font-size:11.5px;color:#9A979A;margin-top:7px}
.hero .r b{color:#F2F0EE}
.kg{display:grid;grid-template-columns:1fr 1fr;gap:9px}
.k{background:#141416;border:1px solid #2A2A2E;border-radius:14px;padding:11px 12px 10px 13px;position:relative;overflow:hidden;min-width:0}
.k::before{content:"";position:absolute;left:0;top:12px;bottom:12px;width:2px;border-radius:2px;background:#8E2A30}
.k .l{font:700 10px 'Inter';letter-spacing:.06em;text-transform:uppercase;color:#C9C6C8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.k .s{font-size:10.5px;color:#9A979A;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.k .v{font:600 19px/1.15 'Sora';margin:7px 0 3px;color:#F2F0EE;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-variant-numeric:tabular-nums}
.k .v.neg{color:#D48A8D}
.k .r{font-size:10.5px;color:#9A979A;line-height:1.3}
.k .r .bad{color:#D48A8D;font-weight:600}.k .r .ok{color:#B5B2B4;font-weight:600}
.al{background:#1C1C1F;border:1px solid #2A2A2E;border-left:3px solid #A63A40;border-radius:12px;padding:10px 12px}
.al.at{border-left-color:#D48A8D}
.al .sv{font:700 9px 'Inter';letter-spacing:.1em;text-transform:uppercase;color:#9A979A}
.al .t{font-weight:600;font-size:13px;margin-top:1px}
.al .s{font-size:11.5px;color:#9A979A;margin-top:2px}
.al .a{font-size:11.5px;color:#F2F0EE;margin-top:5px}.al .a::before{content:"→ ";color:#D48A8D;font-weight:700}
.it{background:#141416;border:1px solid #2A2A2E;border-radius:13px;padding:10px 12px;display:flex;justify-content:space-between;gap:10px;align-items:flex-start}
.it .t{font-weight:600;font-size:13px;line-height:1.3}
.it .s{font-size:11.5px;color:#9A979A;margin-top:2px;line-height:1.35}
.it .v{font:600 14px 'Sora';white-space:nowrap;text-align:right;font-variant-numeric:tabular-nums}
.it .v small{display:block;font:500 10.5px 'Inter';color:#9A979A;margin-top:3px}
.it.canc{opacity:.55}.it.canc .v{text-decoration:line-through}
.tg{display:inline-block;padding:1px 7px;border-radius:999px;font-size:10px;font-weight:600;border:1px solid;margin-right:4px;vertical-align:1px}
.tg.in{color:#E6BDBE;border-color:rgba(166,58,64,.5);background:rgba(166,58,64,.15)}
.tg.out{color:#B5B2B4;border-color:rgba(181,178,180,.3);background:rgba(181,178,180,.08)}
.tg.bad{color:#D48A8D;border-color:rgba(166,58,64,.5);background:rgba(166,58,64,.15)}
.nota{font-size:11px;color:#9A979A;line-height:1.45}
/* widgets */
.stButton>button,.stDownloadButton>button,.stFormSubmitButton>button,[data-testid="stPopover"] button{border-radius:11px;border:1px solid #2A2A2E;background:#1C1C1F;color:#F2F0EE;font-weight:600;min-height:42px}
button[data-testid="stBaseButton-primary"],button[data-testid="stBaseButton-primaryFormSubmit"]{background:#6E1F24!important;border-color:#8E2A30!important}
.stTextInput input,.stNumberInput input,.stDateInput input,[data-baseweb="select"]>div{background:#1C1C1F!important;border-color:#2A2A2E!important;border-radius:10px!important;min-height:42px}
[data-testid="stForm"]{border:1px solid #2A2A2E;border-radius:14px;background:#141416;padding:12px}
[data-testid="stExpander"] details{border:1px solid #2A2A2E;border-radius:12px;background:#141416}
[data-testid="stButtonGroup"] button[data-selected="true"]{background:#6E1F24!important;border-color:#8E2A30!important}
[data-testid="stButtonGroup"] button[data-selected="true"] p{color:#F2F0EE!important}
/* barra de navegação inferior */
.st-key-barra{position:fixed;left:0;right:0;bottom:0;z-index:999;background:rgba(14,14,16,.96);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px);
  border-top:1px solid #2A2A2E;padding:6px max(8px,calc((100vw - 520px)/2)) calc(6px + env(safe-area-inset-bottom))!important;display:flex!important;
  flex-direction:row!important;justify-content:space-between;gap:2px!important}
.st-key-barra>div{flex:1;min-width:0}
.st-key-barra [data-testid="stPageLink"] a,.st-key-barra [data-testid="stPopover"] button{display:flex!important;flex-direction:column;align-items:center;justify-content:center;
  gap:2px;padding:6px 2px!important;border-radius:11px;min-height:52px;width:100%;background:transparent!important;border:0!important}
.st-key-barra [data-testid="stPageLink"] a p,.st-key-barra [data-testid="stPageLink"] a span:not([data-testid="stIconMaterial"]),.st-key-barra [data-testid="stPopover"] button p{font-size:10.5px!important;font-weight:600;color:#9A979A;line-height:1.1;text-align:center;margin:0}
.st-key-barra [data-testid="stPopoverButton"] div[aria-hidden="true"]{display:none!important}
.st-key-barra [data-testid="stPopoverButton"] [title]{max-width:none!important}
.st-key-barra [data-testid="stPopoverButton"] [title]>span{display:flex!important;flex-direction:column;align-items:center;gap:2px}
.st-key-barra [data-testid="stPageLink"] a[aria-current="page"],.st-key-barra [data-testid="stPageLink-NavLink"][aria-current="page"]{background:rgba(166,58,64,.18)!important}
.st-key-barra [data-testid="stPageLink"] a[aria-current="page"] p,.st-key-barra [data-testid="stPageLink"] a[aria-current="page"] span:not([data-testid="stIconMaterial"]){color:#F2F0EE}
.st-key-barra [data-testid="stIconMaterial"]{color:#D48A8D;font-size:22px!important}
.st-key-barra [data-testid="stPopover"] button [data-testid="stIconMaterial"]{margin:0}
</style>
"""

_LOGO = ('<svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="9" fill="#6E1F24"/>'
         '<rect x="8" y="17" width="4.2" height="8" rx="1.6" fill="#D48A8D"/><rect x="13.9" y="12" width="4.2" height="13" rx="1.6" fill="#E6BDBE"/>'
         '<rect x="19.8" y="7" width="4.2" height="18" rx="1.6" fill="#F2F0EE"/></svg>')


def aplicar_tema():
    st.markdown(_CSS, unsafe_allow_html=True)


def e(s) -> str:
    return html.escape("" if s is None else str(s))


def topo(linha_direita: str):
    st.markdown(f'<div class="topo"><div class="m">{_LOGO}<div><div class="n">Datalyse</div><div class="s">Gestão · Academia</div></div></div>'
                f'<div class="d">{linha_direita}</div></div>', unsafe_allow_html=True)


def titulo(t: str, s: str = ""):
    st.markdown(f'<div class="pg">{e(t)}</div>' + (f'<div class="pg-s">{e(s)}</div>' if s else ""), unsafe_allow_html=True)


def secao(t: str, s: str = ""):
    st.markdown(f'<div class="sec">{e(t)}</div>' + (f'<div class="sec-s">{e(s)}</div>' if s else ""), unsafe_allow_html=True)


def hero(rotulo: str, sub: str, valor: str, progresso: float | None = None, esquerda: str = "", direita: str = ""):
    barra = f'<div class="bar"><i style="width:{max(0, min(1, progresso)) * 100:.1f}%"></i></div>' if progresso is not None else ""
    st.markdown(f'<div class="hero"><div class="l">{e(rotulo)}</div><div class="s">{e(sub)}</div><div class="v">{e(valor)}</div>{barra}'
                f'<div class="r"><span>{esquerda}</span><span>{direita}</span></div></div>', unsafe_allow_html=True)


def kpis(itens: list[dict]):
    """itens: {l, s, v, r (html), neg}"""
    cards = "".join(f'<div class="k"><div class="l">{e(i["l"])}</div><div class="s">{e(i.get("s", ""))}</div>'
                    f'<div class="v{" neg" if i.get("neg") else ""}">{e(i["v"])}</div><div class="r">{i.get("r", "")}</div></div>' for i in itens)
    st.markdown(f'<div class="kg">{cards}</div>', unsafe_allow_html=True)


def tendencia(texto: str, ruim: bool, sobe: bool) -> str:
    return f'<span class="{"bad" if ruim else "ok"}">{"▲" if sobe else "▼"} {e(texto)}</span>'


def alertas(lista: list[dict]):
    st.markdown("".join(f'<div class="al{"" if a["sev"] == "Crítico" else " at"}"><div class="sv">{e(a["sev"])}</div>'
                        f'<div class="t">{e(a["t"])}</div><div class="s">{e(a["s"])}</div><div class="a">{e(a["a"])}</div></div>'
                        for a in lista), unsafe_allow_html=True)


def item(titulo_: str, sub: str, valor: str, valor_sub: str = "", classe: str = "", tags: str = ""):
    st.markdown(f'<div class="it {classe}"><div><div class="t">{tags}{e(titulo_)}</div><div class="s">{sub}</div></div>'
                f'<div class="v">{e(valor)}<small>{e(valor_sub)}</small></div></div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Gráficos (Plotly) no mesmo tema
# ----------------------------------------------------------------------------
def figura(fig: go.Figure, altura: int = 240, legenda: bool = True) -> go.Figure:
    fig.update_layout(
        height=altura, margin=dict(l=4, r=8, t=30 if legenda else 8, b=4), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color=C["muted"], size=11), separators=",.", showlegend=legenda,
        legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0, font=dict(size=10.5)), dragmode=False,
        hoverlabel=dict(bgcolor=C["surface2"], bordercolor=C["border"], font=dict(color=C["text"], family="Inter", size=12)),
        bargap=.32)
    fig.update_xaxes(showgrid=False, zeroline=False, showline=False, fixedrange=True, tickfont=dict(size=10.5))
    fig.update_yaxes(gridcolor=C["grid"], zeroline=False, showline=False, fixedrange=True, tickfont=dict(size=10.5))
    return fig


def grafico(fig: go.Figure, altura: int = 240, legenda: bool = True, chave: str | None = None):
    st.plotly_chart(figura(fig, altura, legenda), width="stretch", key=chave,
                    config={"displayModeBar": False, "scrollZoom": False, "locale": "pt-BR"})
