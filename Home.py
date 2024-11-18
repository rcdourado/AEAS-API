import datetime
import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# Token de autenticação
TOKEN = st.secrets["TOKEN"]
BASE_URL = "https://web.sisobras.com.br/AssociacaoAPI"
hoje = datetime.today()

# Função para buscar dados de um endpoint
def fetch_data(endpoint):
    url = f"{BASE_URL}{endpoint}?token={TOKEN}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Erro ao buscar dados de {endpoint}: {response.status_code}")
        return []

# Formatar datas para o formato desejado (dd/mm/aaaa)
def format_date_column(df, column_name):
    if column_name in df.columns:
        df[column_name] = pd.to_datetime(df[column_name], errors='coerce').dt.strftime('%d/%m/%Y')
    return df

# Aplicar filtros de datas e texto
def apply_filters(df, date_column, start_date, end_date, text_filters):
    if start_date:
        df = df[pd.to_datetime(df[date_column], format='%d/%m/%Y', errors='coerce') >= pd.to_datetime(start_date)]
    if end_date:
        df = df[pd.to_datetime(df[date_column], format='%d/%m/%Y', errors='coerce') <= pd.to_datetime(end_date)]
    for col, values in text_filters.items():
        if values:
            df = df[df[col].isin(values)]
    return df

# Calcular totais
def calculate_totals(df):
    recebido = df["valorTituloRecebido"].fillna(0).sum()
    a_receber = df[
        (pd.to_datetime(df["dataVencimento"], format='%d/%m/%Y', errors='coerce') >= hoje) &
        (df["valorTituloRecebido"].fillna(0) == 0)
    ]["valorTituloOriginal"].fillna(0).sum()
    em_atraso = df[
        (pd.to_datetime(df["dataVencimento"], format='%d/%m/%Y', errors='coerce') < hoje) &
        (df["valorTituloRecebido"].fillna(0) == 0)
    ]["valorTituloOriginal"].fillna(0).sum()
    return recebido, a_receber, em_atraso

def calculate_totals_desp(df):
    total_pago = df["valorTituloPago"].fillna(0).sum()
    a_pagar = df[
        (pd.to_datetime(df["dataVencimento"], format='%d/%m/%Y', errors='coerce') >= hoje) &
        (df["valorTituloPago"].fillna(0) == 0)
    ]["valorTituloOriginal"].fillna(0).sum()
    em_atraso = df[
        (pd.to_datetime(df["dataVencimento"], format='%d/%m/%Y', errors='coerce') < hoje) &
        (df["valorTituloPago"].fillna(0) == 0)
    ]["valorTituloOriginal"].fillna(0).sum()
    return total_pago, a_pagar, em_atraso

#Configurações da Página
st.set_page_config(page_title="Dasboard AEAS", page_icon="img/icon 100x100.png", layout="wide", initial_sidebar_state="collapsed", menu_items={'Get Help': 'https://www.rcdourado.com'})

#         section[data-testid="stSidebar"][aria-expanded="true"]{display: none;}
hide_default_format = """
       <style>
        #MainMenu {visibility: hidden; }
        footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)
st.sidebar.title("Filtros")

# Carregar dados de todos os endpoints
with st.spinner("Carregando dados..."):
    receitas = pd.DataFrame(fetch_data("/SisAssociate/Financeiro/LancamentoReceitas"))
    despesas = pd.DataFrame(fetch_data("/SisAssociate/Financeiro/LancamentoDespesas"))
    saldo = pd.read_excel('saldoSicredi.xlsx')

# Garantir que as datas estão formatadas corretamente
receitas = format_date_column(receitas, 'dataVencimento')
receitas = format_date_column(receitas, 'dataPagamento')
despesas = format_date_column(despesas, 'dataVencimento')
despesas = format_date_column(despesas, 'dataPagamento')

# Definir datas padrão
primeiro_dia_mes = hoje.replace(day=1)
if hoje.month == 1 or hoje.month == 3 or hoje.month == 5 or hoje.month == 7  or hoje.month == 8  or hoje.month == 10 or hoje.month == 12:
    ultimo_dia_mes = hoje.replace(day=31)
else:
    ultimo_dia_mes = hoje.replace(day=30)

# Sidebar - Filtros
st.sidebar.subheader("Filtros das Receitas")
data_vencimento_inicio_rec = st.sidebar.date_input("Data de Vencimento - Início (Receitas)", value=primeiro_dia_mes)
data_vencimento_fim_rec = st.sidebar.date_input("Data de Vencimento - Fim (Receitas)", value=ultimo_dia_mes)
data_pagamento_inicio_rec = st.sidebar.date_input("Data de Pagamento - Início (Receitas)", value=primeiro_dia_mes)
data_pagamento_fim_rec = st.sidebar.date_input("Data de Pagamento - Fim (Receitas)", value=ultimo_dia_mes)
razao_social_rec = st.sidebar.multiselect("Parceiro de Negócio (Receitas)", receitas["razaoSocial"].dropna().unique())
tipo_recebimento_rec = st.sidebar.multiselect("Tipo de Recebimento (Receitas)", receitas["tipoRecebimento"].dropna().unique())
tipo_lancamento_rec = st.sidebar.multiselect("Tipo de Lançamento (Receitas)", receitas["tipoLancamento"].dropna().unique())
numero_documento_rec = st.sidebar.text_input("Número do Documento (Receitas)")

st.sidebar.subheader("Filtros das Despesas")
data_vencimento_inicio_desp = st.sidebar.date_input("Data de Vencimento - Início (Despesas)", value=primeiro_dia_mes)
data_vencimento_fim_desp = st.sidebar.date_input("Data de Vencimento - Fim (Despesas)", value=ultimo_dia_mes)
data_pagamento_inicio_desp = st.sidebar.date_input("Data de Pagamento - Início (Despesas)", value=primeiro_dia_mes)
data_pagamento_fim_desp = st.sidebar.date_input("Data de Pagamento - Fim (Despesas)", value=ultimo_dia_mes)
razao_social_desp = st.sidebar.multiselect("Parceiro de Negócio (Despesas)", despesas["razaoSocial"].dropna().unique())
tipo_recebimento_desp = st.sidebar.multiselect("Tipo de Recebimento (Despesas)", despesas["tipoRecebimento"].dropna().unique())
tipo_lancamento_desp = st.sidebar.multiselect("Tipo de Lançamento (Despesas)", despesas["tipoLancamento"].dropna().unique())
numero_documento_desp = st.sidebar.text_input("Número do Documento (Despesas)")


# Aplicar filtros
text_filters_rec = {
    "tipoRecebimento": tipo_recebimento_rec,
    "tipoLancamento": tipo_lancamento_rec,
    "razaoSocial": razao_social_rec
}
text_filters_desp = {
    "tipoRecebimento": tipo_recebimento_desp,
    "tipoLancamento": tipo_lancamento_desp,
    "razaoSocial": razao_social_desp
}

receitas_filtradas = apply_filters(
    receitas,
    "dataVencimento",
    data_vencimento_inicio_rec,
    data_vencimento_fim_rec,
    text_filters_rec
)

despesas_filtradas = apply_filters(
    despesas,
    "dataVencimento",
    data_vencimento_inicio_desp,
    data_vencimento_fim_desp,
    text_filters_desp
)

# Filtrar número do documento, se fornecido
if numero_documento_rec:
    receitas_filtradas = receitas_filtradas[
        receitas_filtradas["numeroDocumento"].astype(str).str.contains(numero_documento_rec, na=False)
    ]

if numero_documento_desp:
    despesas_filtradas = despesas_filtradas[
        despesas_filtradas["numeroDocumento"].astype(str).str.contains(numero_documento_desp, na=False)
    ]

# Separar boletos reemitidos e não reemitidos
def separate_reissued(df, col_name):
    reissued = df[df[col_name].str.endswith("R", na=False)]
    normal = df[~df[col_name].str.endswith("R", na=False)]
    return normal, reissued

receitas_normais, receitas_reemitidas = separate_reissued(receitas_filtradas, "numeroDocumento")

# Calcular totais respeitando os filtros
recebido_normal, a_receber_normal, em_atraso_normal = calculate_totals(receitas_normais)
recebido_reemitidas, a_receber_reemitidas, em_atraso_reemitidas = calculate_totals(receitas_reemitidas)
despesas_pagas, despesas_a_pagar, despesas_em_atraso = calculate_totals_desp(despesas_filtradas)

# Calculos adicionais
saldo_sicredi = saldo['Saldo'].sum()
total_receitas = receitas_filtradas["valorTituloOriginal"].fillna(0).sum()
total_receitas_reemitidas = receitas_reemitidas["valorTituloOriginal"].fillna(0).sum()
total_despesas = despesas_filtradas["valorTituloOriginal"].fillna(0).sum()
saldo_operacional_total = total_receitas + total_receitas_reemitidas - total_despesas
saldo_operacional = recebido_normal + recebido_reemitidas - despesas_pagas

# Exibir Resumo Financeiro
colA, colB, colC = st.columns(3)
with colA:
    st.title("Resumo Financeiro")
with colB:
    st.metric(label="Saldo Operacional (Recebido - Pago)", value=f"R$ {saldo_operacional:,.2f}")
with colC:
    st.metric(label="Saldo Sicredi", value=f"R$ {saldo_sicredi:,.2f}")

# Exibir métricas para receitas normais
st.divider()
st.title(f"Receitas R$ {total_receitas:,.2f}")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Recebido", f"R$ {recebido_normal:,.2f}")
with col2:
    st.metric("Total A Receber", f"R$ {a_receber_normal:,.2f}")
with col3:
    st.metric("Total Em Atraso", f"R$ {em_atraso_normal:,.2f}")
st.divider()
st.subheader("Lista de Receitas")
#st.dataframe(receitas_normais)
st.dataframe(receitas_normais[['dataVencimento', 'razaoSocial', 'descricao', 'dataPagamento', 'tipoRecebimento', 'valorTituloOriginal','valorTituloRecebido','numeroDocumento', 'tipoLancamento', 'observacao']],hide_index=True)

# Exibir métricas para receitas reemitidas
st.divider()
st.title(f"Boletos Reemitidos R$ {total_receitas_reemitidas:,.2f}")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Recebido", f"R$ {recebido_reemitidas:,.2f}")
with col2:
    st.metric("Total A Receber", f"R$ {a_receber_reemitidas:,.2f}")
with col3:
    st.metric("Total Em Atraso", f"R$ {em_atraso_reemitidas:,.2f}")
st.divider()
st.subheader("Lista de Boletos Reemitidos")
#st.dataframe(receitas_reemitidas)
st.dataframe(receitas_reemitidas[['dataVencimento', 'razaoSocial', 'descricao', 'dataPagamento', 'tipoRecebimento', 'valorTituloOriginal','valorTituloRecebido','numeroDocumento', 'tipoLancamento', 'observacao']],hide_index=True)

# Exibir métricas para despesas
st.divider()
st.title(f"Despesas R$ {total_despesas:,.2f}")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Pago", f"R$ {despesas_pagas:,.2f}")
with col2:
    st.metric("Total A Pagar", f"R$ {despesas_a_pagar:,.2f}")
with col3:
    st.metric("Total Em Atraso", f"R$ {despesas_em_atraso:,.2f}")
st.divider()
st.subheader("Lista de Despesas")
#st.dataframe(despesas_filtradas)
st.dataframe(despesas_filtradas[['dataVencimento', 'razaoSocial', 'descricao', 'dataPagamento', 'tipoRecebimento', 'valorTituloOriginal','valorTituloPago','numeroDocumento', 'tipoLancamento', 'observacao', 'mesAnoCompetencia']],hide_index=True)

# Exibir métricas para Associados
st.divider()
st.title("Associados")
st.text("Disponível em breve.")
#st.write("Associados", associados)

# Exibir métricas para Contribuições
st.title("Contribuições")
st.text("Disponível em breve.")
#st.write("Contribuições", contribuicoes)

st.divider()

#st.write("Beneficiários", beneficiarios)
#st.write("Endereços", enderecos)

#Rodapé
st.divider()
st.text("Associação dos Engenheiros e Arquitetos de Sorocaba - Todos os direitos reservados.")
st.text("Dados com início em 01/01/2017.")