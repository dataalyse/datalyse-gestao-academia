# Datalyse · Gestão Executiva de Academia

Painel executivo interativo para academias multimodalidade (musculação, lutas e balé): operação, alunos, retenção, comercial, financeiro e projeções, com um simulador do tipo "E se?".

Desenvolvido por **Datalyse · Inteligência de Dados**.

## O que tem no painel

| Página | Destaques |
|---|---|
| **Visão Geral** | 12 KPIs (MRR, Churn Rate, CAC, LTV, LTV/CAC, Break-even…), cada um com o cálculo e a decisão que apoia; velocímetro da meta de alunos, resultado operacional em 12 meses, alertas com ação recomendada |
| **Financeiro** | DRE em cascata, receita × custos × ponto de equilíbrio, despesas por categoria e centro de custo, saldo de caixa, DRE de 12 meses em tabela |
| **Notas fiscais** | Notas de entrada e de saída, cobertura fiscal das despesas, conciliação despesas × notas por categoria; adicionar nota manualmente ou pelo XML da NF-e/NFS-e e baixar a planilha com a aba NotasFiscais |
| **Alunos & Retenção** | Churn × retenção, movimentação da base, alunos por plano e origem, cadastro com busca e ordenação |
| **Comercial** | Funil de conversão, leads por origem, conversão por modalidade, motivos de perda |
| **Operação** | Ocupação por turma, mapa de calor dia × horário, margem por turma e por modalidade, ranking de professores |
| **Projeções** | Faturamento e alunos projetados e simulador de crescimento, churn, ticket, custos e margem |

Filtros em menus suspensos (período, modalidade, professor, plano, status, origem, forma de pagamento e centro de custo), filtro cruzado ao clicar nos gráficos, exportação em PDF e layout responsivo (celular a desktop).

## Como usar

- **Online:** abra o app publicado no Streamlit.
- **Offline:** baixe `dashboard_academia.html` e abra direto no navegador. Não precisa de servidor (só de internet para carregar as bibliotecas de gráficos).
- **Atualizar os dados:** preencha `Modelo_Gestao_Academia_V2_Executivo.xlsx` e use o botão **Carregar planilha** no topo do painel. Todos os indicadores são recalculados.

## Versão para celular (Python)

A pasta `mobile/` tem um app Streamlit pensado para a tela do celular: cartões em duas colunas, poucos gráficos por tela e barra de navegação inferior (Resumo, Finanças, Notas, Alunos e Mais). Usa os mesmos dados e as mesmas fórmulas corrigidas do painel web.

```bash
pip install -r mobile/requirements.txt
streamlit run mobile/app.py
```

No Streamlit Community Cloud, publique um app novo apontando para `mobile/app.py`. As notas lançadas pelo app ficam em `mobile/dados/notas_fiscais.csv`; no Streamlit Cloud esse arquivo volta ao estado inicial quando o app reinicia, então use **Baixar planilha com as notas** para guardar uma cópia.

## Notas fiscais

A aba `NotasFiscais` é opcional na planilha, com as colunas: Data Emissão, Número, Série, Tipo (Entrada/Saída), Emitente/Destinatário, CNPJ/CPF, Descrição, Categoria, Valor, Status (Válida/Cancelada), Chave de Acesso e Mês. No painel web, as notas adicionadas ficam salvas no navegador; o botão **Baixar planilha com as notas** gera o Excel completo com essa aba.

## Indicadores recalculados

O painel recalcula os indicadores a partir das abas de dados brutos, com correções em relação às fórmulas originais do modelo:

1. **LTV** = ticket médio × margem de contribuição ÷ churn mensal
2. **Ticket médio** considera apenas alunos ativos
3. **Margem por modalidade** usa a receita potencial das turmas contra o custo das turmas
4. **Churn real** do período no card; série de 12 meses da aba de cancelamentos
5. **DRE** usa as despesas reais nos meses realizados e as premissas nos projetados
6. **Ocupação média** considera só turmas com capacidade > 0
7. **Ponto de equilíbrio** também em número de alunos
8. Novos indicadores: **LTV/CAC** e **inadimplência**

## Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estrutura

```
app.py                                    # app Streamlit (exibe o painel em tela cheia)
dashboard_academia.html                   # painel completo, arquivo único com dados embutidos
mobile/                                   # versão para celular em Python (Streamlit + Plotly)
ferramentas/template_painel.html          # código-fonte do painel (sem os dados)
ferramentas/build_painel.py               # gera o dashboard_academia.html a partir da planilha
ferramentas/notas_fiscais_exemplo.json    # notas de exemplo usadas quando a planilha não tem a aba
Modelo_Gestao_Academia_V2_Executivo.xlsx  # modelo de planilha (fonte dos dados)
requirements.txt
.streamlit/config.toml                    # tema escuro da Datalyse
```

Para alterar o painel web, edite `ferramentas/template_painel.html` e rode `python ferramentas/build_painel.py`.

Tecnologias: HTML, CSS e JavaScript puro · Apache ECharts · SheetJS · Python · Streamlit · Plotly.
