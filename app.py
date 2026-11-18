import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os

st.set_page_config(
    page_title="Morelate - Controle de Entregas",
    page_icon="📦",
    layout="centered"
)

st.markdown("""
    <style>
    .header-card {
        background-color: #0B6E31;
        padding: 18px 15px 14px 15px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .header-title {
        color: #FFFFFF;
        font-size: 24px;
        font-weight: 700;
        margin-top: 4px;
        margin-bottom: 0px;
        letter-spacing: 0.5px;
    }
    .header-subtitle {
        color: #D9F2E2;
        font-size: 14px;
        margin-top: 2px;
        margin-bottom: 4px;
    }
    div.stButton > button:first-child {
        background-color: #0B6E31;
        color: white;
        font-size: 18px;
        font-weight: bold;
        border-radius: 10px;
        padding: 12px 20px;
        border: none;
        transition: 0.2s;
    }
    div.stButton > button:first-child:hover {
        background-color: #085224;
        color: white;
    }
    div[role="radiogroup"] label {
        font-size: 17px !important;
        padding: 6px 0px;
    }
    </style>
""", unsafe_allow_html=True)

if os.path.exists("logo.png"):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.png", use_container_width=True)

st.markdown("""
    <div class="header-card">
        <p class="header-title">Controle de Entregas</p>
        <p class="header-subtitle">Registro rápido de baixa e ocorrências</p>
    </div>
""", unsafe_allow_html=True)

LINK_PLANILHA = "https://google.com"

conn = st.connection("gsheets", type=GSheetsConnection)
df_existente = conn.read(spreadsheet=LINK_PLANILHA, ttl=0)

numero_nf = st.text_input("📋 Número da Nota Fiscal:", placeholder="Digite apenas números (Ex: 105432)")
motorista = st.selectbox("👤 Entregador:", ["Selecione...", "Carlos Silva", "Marcos Souza", "Roberto Lima"])
status = st.radio("📌 Status da Entrega:", ["🟢 Pedido Entregue OK", "🔴 Cancelado / Recusado"])

motivo_selecionado = "N/A"

if status == "🔴 Cancelado / Recusado":
    motivo_selecionado = st.selectbox(
        "⚠️ Motivo Real do Cancelamento:",
        [
            "Selecione...",
            "Dados da Fatura / Boleto Incorretos",
            "Emissão Indevida / Pedido Duplicado",
            "Desistência da Compra",
            "Avaria / Erro de Aplicação",
            "Cliente Ausente / Loja Fechada",
            "Recusa por Atraso"
        ]
    )

observacao = st.text_area("📝 Observações (opcional):", placeholder="Descreva brevemente o ocorrido, se necessário...")

st.write("")
if st.button("✅ Confirmar Registro", use_container_width=True):
    nf_limpa = numero_nf.strip()
    
    if not nf_limpa or not nf_limpa.isdigit():
        st.error("❌ Digite apenas números válidos para a Nota Fiscal.")
    elif motorista == "Selecione..." or (status == "🔴 Cancelado / Recusado" and motivo_selecionado == "Selecione..."):
        st.error("❌ Preencha o Entregador e o Motivo do cancelamento.")
    else:
        notas_registradas = (
            df_existente["Nota_Fiscal"]
            .dropna()
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.strip()
            .values
        )
        
        if nf_limpa in notas_registradas:
            st.warning(f"⚠️ Atenção: A Nota Fiscal {nf_limpa} já foi registrada anteriormente!")
        else:
            fuso_br = ZoneInfo("America/Sao_Paulo")
            agora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")
            
            df_novo = pd.DataFrame([{
                "Data_Hora": agora,
                "Nota_Fiscal": nf_limpa,
                "Motorista": motorista,
                "Status": status,
                "Motivo_Real": motivo_selecionado,
                "Observações": observacao.strip()
            }])
            
            df_final = pd.concat([df_existente, df_novo], ignore_index=True)
            conn.update(spreadsheet=LINK_PLANILHA, data=df_final)
            st.balloons()
            st.success(f"✅ Nota Fiscal {nf_limpa} registrada com sucesso às {agora}!")

st.sidebar.header("🔒 Área da Logística")
senha = st.sidebar.text_input("Senha de acesso:", type="password")

if senha == "morelate2026":
    st.divider()
    st.subheader("📊 Últimos Registros na Planilha Google")
    st.dataframe(df_existente.tail(10), use_container_width=True)
