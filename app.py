import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
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

# Conexão segura e em cache com o Google Sheets via gspread
@st.cache_resource
def conectar_planilha():
    base_url = "https://www.googleapis.com" + "/auth/"
    escopos = [
        base_url + "spreadsheets",
        base_url + "drive"
    ]
    credenciais_dict = dict(st.secrets["connections"]["gsheets"])
    creds = Credentials.from_service_account_info(credenciais_dict, scopes=escopos)
    cliente = gspread.authorize(creds)
    
    # Abre a planilha pelo ID exato da base_entregas_morelate
    planilha = cliente.open_by_key("1I3V8UxkeQyP1tO7TZIVbQk7HQrxv-FSsz5l3ChCMsV4")
    return planilha.sheet1

# Logo centralizado
if os.path.exists("logo.png"):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.png", use_container_width=True)

# Cabeçalho
st.markdown("""
    <div class="header-card">
        <p class="header-title">Controle de Entregas</p>
        <p class="header-subtitle">Registro rápido de baixa e ocorrências</p>
    </div>
""", unsafe_allow_html=True)

# Controle de estado para evitar duplo clique no celular
if "enviando" not in st.session_state:
    st.session_state.enviando = False

# Formulário
numero_nf = st.text_input("📋 Número da Nota Fiscal:", placeholder="Digite apenas números (Ex: 105432)")

tipo_motorista = st.radio(
    "🚛 Tipo de Motorista:",
    ["Motorista Morelate", "Motorista Agregado"],
    horizontal=True
)

if tipo_motorista == "Motorista Morelate":
    motorista = st.selectbox(
        "👤 Entregador Morelate:",
        ["Selecione...", "ALEXANDRE", "EVALDO", "NIVALDO", "PAULO", "RAMON", "RICARDO"]
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

# Botão com trava de clique duplo
if st.button("✅ Confirmar Registro", use_container_width=True, disabled=st.session_state.enviando):
    nf_limpa = numero_nf.strip()
    
    if not nf_limpa or not nf_limpa.isdigit():
        st.error("❌ Digite apenas números válidos para a Nota Fiscal.")
    elif motorista == "Selecione..." or (status == "🔴 Cancelado / Recusado" and motivo_selecionado == "Selecione..."):
        st.error("❌ Preencha o Entregador e o Motivo do cancelamento.")
    else:
        st.session_state.enviando = True
        try:
            with st.spinner("Registrando entrega com segurança..."):
                aba = conectar_planilha()
                
                # Lê APENAS a coluna B (Nota_Fiscal) para checar duplicidade de forma ultra-rápida
                notas_coluna = aba.col_values(2)[1:] # Ignora o cabeçalho
                notas_limpas = [str(n).replace(".0", "").strip() for n in notas_coluna]
                
                if nf_limpa in notas_limpas:
                    st.warning(f"⚠️ Atenção: A Nota Fiscal {nf_limpa} já foi registrada anteriormente!")
                else:
                    fuso_br = ZoneInfo("America/Sao_Paulo")
                    agora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")
                    
                    nova_linha = [
                        agora,
                        nf_limpa,
                        motorista,
                        status,
                        motivo_selecionado,
                        observacao.strip()
                    ]
                    
                    # Insere a linha no final sem tocar nas outras linhas (100% seguro contra concorrência)
                    aba.append_row(nova_linha, value_input_option="USER_ENTERED")
                    st.success(f"✅ Nota Fiscal {nf_limpa} registrada com sucesso às {agora}!")
                    
        except Exception as erro:
            st.error(f"❌ Detalhe do erro: {erro}")
        finally:
            st.session_state.enviando = False

# Área restrita na barra lateral
st.sidebar.header("🔒 Área da Logística")
senha = st.sidebar.text_input("Senha de acesso:", type="password")

# Busca a senha dos Secrets (ou usa fallback caso ainda não tenha configurado lá)
senha_correta = st.secrets.get("SENHA_LOGISTICA", "morelate2026")

if senha == senha_correta:
    st.divider()
    st.subheader("📊 Últimos Registros na Planilha Google")
    try:
        aba = conectar_planilha()
        dados = aba.get_all_records()
        if dados:
            df_logistica = pd.DataFrame(dados)
            st.dataframe(df_logistica.tail(10), use_container_width=True)
        else:
            st.info("Nenhum registro encontrado ainda.")
    except Exception as erro:
        st.error(f"Não foi possível carregar os dados da planilha: {erro}")
