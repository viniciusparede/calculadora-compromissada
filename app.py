import streamlit as st
import pandas as pd
import locale
from datetime import datetime, timedelta
import holidays
import plotly.express as px

# Definir locale para pt_BR (meses em português)
try:
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except locale.Error:
    pass  # caso o locale não esteja disponível, continua com padrão

# Configuração da página
st.set_page_config(
    page_title="Calculadora de Compromissadas",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Tabela de IOF regressivo (1 a 30 dias)
IOF_TABLE = {
    1: 96,
    2: 93,
    3: 90,
    4: 86,
    5: 83,
    6: 80,
    7: 76,
    8: 73,
    9: 70,
    10: 66,
    11: 63,
    12: 60,
    13: 56,
    14: 53,
    15: 50,
    16: 46,
    17: 43,
    18: 40,
    19: 36,
    20: 33,
    21: 30,
    22: 26,
    23: 23,
    24: 20,
    25: 16,
    26: 13,
    27: 10,
    28: 6,
    29: 3,
    30: 0,
}

st.title("Comparativo CDB vs Compromissada")

# Sidebar - Parâmetros de entrada
st.sidebar.header("Parâmetros de Entrada")
# Data de Início em formato DD/MM/YYYY
start_date = st.sidebar.date_input(
    "Data de Início", datetime.today(), format="DD/MM/YYYY"
)


principal = st.sidebar.number_input(
    "Valor Investido (R$)", value=10_000.0, step=10_000.0, format="%.2f"
)

selic_pct = (
    st.sidebar.number_input("Taxa Selic Atual (% a.a.)", value=15.00, step=0.25) / 100
)

cdb_cdi_pct = st.sidebar.number_input("CDB (% do CDI)", value=100, step=10) / 100

comp_cdi_pct = (
    st.sidebar.number_input("Compromissada (% do CDI)", value=50, step=5) / 100
)

n_days = st.sidebar.slider("Horizonte (dias úteis)", 1, 30, 22)

dias_uteis = 252

# Cálculo da taxa diária com base no CDI informado
cdi_pct = selic_pct - (0.1 / 100)
daily_cdi = (1 + cdi_pct) ** (1 / dias_uteis) - 1

# Preparar calendário financeiro BVMF e gerar próximos n_days dias úteis excluindo feriados
bvmf_hols = holidays.financial_holidays(market="BVMF")
business_dates = []
current = start_date
while len(business_dates) < n_days:
    current += timedelta(days=1)
    if current.weekday() < 5 and current not in bvmf_hols:
        business_dates.append(current)


rows = []
for business_idx, date in enumerate(business_dates, start=1):
    # calcular dias corridos desde o início (inclusive finais de semana)
    calendar_days = (date - start_date).days
    iof = IOF_TABLE.get(calendar_days, 0)

    # rendimentos compostos
    cdb_yield = (1 + daily_cdi * cdb_cdi_pct) ** business_idx - 1
    comp_yield = (1 + daily_cdi * comp_cdi_pct) ** business_idx - 1

    # valores em R$
    rend_cdb = principal * cdb_yield
    rend_comp = principal * comp_yield

    # IOF e IR
    iof_tax = rend_cdb * (iof / 100)
    cdb_net = (rend_cdb - iof_tax) * (1 - 0.225)
    comp_net = rend_comp * (1 - 0.225)

    # percentuais líquidos
    pct_cdb_net = cdb_net / principal * 100
    pct_comp_net = comp_net / principal * 100
    # equivalente ao CDB em %
    eq_cdb_pct = (pct_comp_net / pct_cdb_net * 100) if pct_cdb_net != 0 else 0

    rows.append(
        {
            "Dia útil": business_idx,
            "Data": date.strftime("%d/%m/%Y"),
            "IOF (%)": f"{iof}%",
            "CDB (R$)": cdb_net,
            "Compromissada (R$)": comp_net,
            "Equivalente ao CDB (%)": eq_cdb_pct,
        }
    )

# Cria DataFrame e exibe
df = pd.DataFrame(rows)

st.subheader("Tabela de Rendimentos Líquidos")
st.dataframe(
    df.style.format(
        {
            "Data": "{}",
            "IOF (%)": "{}",
            "CDB (R$)": "{:.2f}",
            "Compromissada (R$)": "{:.2f}",
            "Equivalente ao CDB (%)": "{:.2f}%",
        }
    ),
    use_container_width=True,
)

st.subheader("Evolução Acumulada Líquida")

# Supondo que df já contenha as colunas "Dia útil", "CDB (R$)" e "Compromissada (R$)"
# Se quiser, ajuste o nome das colunas para ficarem sem parênteses ou acentos.
df_plot = df.copy()


fig = px.line(
    df_plot,
    x="Dia útil",
    y=["CDB (R$)", "Compromissada (R$)"],
    title="Evolução Acumulada Líquida",
    labels={"value": "Valor (R$)", "Dia útil": "Dia Útil"},
    template="plotly_white",
)

# Marca pontos em cada valor
fig.update_traces(mode="lines+markers", marker=dict(size=6, symbol="circle"))

# Formatação de eixos
fig.update_layout(
    font=dict(family="Arial", size=14),
    xaxis=dict(
        dtick=1,  # um tick por dia útil
        title=dict(text="Dia Útil", font=dict(size=16)),
    ),
    yaxis=dict(
        title=dict(text="Valor (R$)", font=dict(size=16)),
        tickformat=",.2f",  # formata com vírgula de milhar e 2 decimais
    ),
    legend=dict(
        title="Instrumento",
        title_font_size=14,
        font_size=12,
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
    ),
    margin=dict(l=60, r=40, t=80, b=60),
)

st.plotly_chart(fig, use_container_width=True)
