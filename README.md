# Datalyse · Gestão Executiva de Academia

Painel executivo interativo para academias multimodalidade (musculação, lutas e balé): operação, alunos, retenção, comercial, financeiro e projeções, com um simulador do tipo "E se?".

Desenvolvido por **Datalyse · Inteligência de Dados**.

## O que tem no painel

| Página | Destaques |
|---|---|
| **Visão Geral** | 12 KPIs (MRR, Churn Rate, CAC, LTV, LTV/CAC, Break-even…), cada um com o cálculo e a decisão que apoia; velocímetro da meta de alunos, resultado operacional em 12 meses, alertas com ação recomendada |
| **Financeiro** | DRE em cascata, receita × custos × ponto de equilíbrio, despesas por categoria e centro de custo, saldo de caixa, DRE de 12 meses em tabela |
| **Alunos & Retenção** | Churn × retenção, movimentação da base, alunos por plano e origem, cadastro com busca e ordenação |
| **Comercial** | Funil de conversão, leads por origem, conversão por modalidade, motivos de perda |
| **Operação** | Ocupação por turma, mapa de calor dia × horário, margem por turma e por modalidade, ranking de professores |
| **Projeções** | Faturamento e alunos projetados e simulador de crescimento, churn, ticket, custos e margem |

Filtros em menus suspensos (período, modalidade, professor, plano, status, origem, forma de pagamento e centro de custo), filtro cruzado ao clicar nos gráficos, exportação em PDF e layout responsivo (celular a desktop).

## Como usar

- **Online:** abra o app publicado no Streamlit.
- **Offline:** baixe `dashboard_academia.html` e abra direto no navegador. Não precisa de servidor (só de internet para carregar as bibliotecas de gráficos).
- **Atualizar os dados:** preencha `Modelo_Gestao_Academia_V2_Executivo.xlsx` e use o botão **Carregar planilha** no topo do painel. Todos os indicadores são recalculados.

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
Modelo_Gestao_Academia_V2_Executivo.xlsx  # modelo de planilha (fonte dos dados)
requirements.txt
.streamlit/config.toml                    # tema escuro da Datalyse
```

Tecnologias: HTML, CSS e JavaScript puro · Apache ECharts · SheetJS · Streamlit.
