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

# Estilo visual personalizado (Identidade Morelate + Mobile-First)
st.markdown("""
    <style>
    /* Cartão do cabeçalho */
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
    /* Botão principal no verde Morelate */
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
    /* Aumenta o toque dos botões de rádio no celular */
    div[role="radiogroup"] label {
        font-size: 17px !important;
        padding: 6px 0px;
    }
    </style>
""", unsafe_allow_html=True)

# Logo centralizado no topo
if os.path.exists("logo.png"):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.png", use_container_width=True)

# Cabeçalho Oficial estilo Cartão
st.markdown("""
    <div class="header-card">
        <p class="header-title">Controle de Entregas</p>
        <p class="header-subtitle">Registro rápido de baixa e ocorrências</p>
    </div>
""", unsafe_allow_html=True)

# Link direto da Planilha Google Morelate
LINK_PLANILHA = "https://docs.google.com/spreadsheets/d/1I3V8UxkeQyP1tO7TZIVbQk7HQrxv-FSsz5l3ChCMsV4/edit?gid=0#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)
df_existente = conn.read(spreadsheet=LINK_PLANILHA, ttl=0)

numero_nf = st.text_input("📋 Número da Nota Fiscal:", placeholder="Digite apenas números (Ex: 105432)")

tipo_motorista = st.radio(
    "🚛 Tipo de Motorista:",
    ["Motorista Morelate", "Motorista Agregado"],
    horizontal=True
)

if tipo_motorista == "Motorista Morelate":
    motorista = st.selectbox(
        "👤 Entregador Morelate:",
        [
            "Selecione...",
            "ALEXANDRE",            
            "EVALDO",
            "NIVALDO",
            "PAULO",
            "RAMON",
            "RICARDO"
        ]
    )
else:
    motorista = st.selectbox(
        "🚘 Placa / Motorista Agregado:",
        [
            "Selecione...",
            "QUT 1B82 - CREMILDA",
            "QPQ 6C07 - FELIPE",
            "DZZ 8077 - FELIPE",
            "UQK 9G88 - GABRIEL",
            "FYW 4D53 - GABRIEL",
            "GFV 6F29 - JOALDO"
        ]
    )

status = st.radio("📌 Status da Entrega:", ["🟢 Pedido Entregue OK", "🔴 Cancelado / Recusado"])

motivo_selecionado = "N/A"

if status == "🔴 Cancelado / Recusado":
    motivo_selecionado = st.selectbox(
        "⚠️ Motivo Real do Cancelamento:",
        [
            "Selecione...",
            "Erro na nota / Boleto / Preço divergente",
            "Pedido Duplicado / Cliente não pediu",
            "Endereço errado / Local não encontrado",
            "Mercadoria errada / Faltando / Avariada",
            "Atraso na entrega / Fora do horário",
            "Cliente ausente / Local fechado",
            "Cliente desistiu / Sem dinheiro ou espaço"
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
            
            st.success(f"✅ Nota Fiscal {nf_limpa} registrada com sucesso às {agora}!")

st.sidebar.header("🔒 Área da Logística")
senha = st.sidebar.text_input("Senha de acesso:", type="password")

if senha == "morelate2026":
    st.divider()
    st.subheader("📊 Últimos Registros na Planilha Google")
    st.dataframe(df_existente.tail(10), use_container_width=True)
