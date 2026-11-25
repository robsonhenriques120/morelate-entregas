


import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="Morelate - Controle de Retira",
    page_icon="🏪",
    layout="wide"
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
        font-size: 26px;
        font-weight: 700;
        margin: 0;
    }
    .header-subtitle {
        color: #D9F2E2;
        font-size: 14px;
        margin-top: 4px;
    }
    div.stButton > button:first-child {
        background-color: #0B6E31;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border-radius: 10px;
        padding: 10px 20px;
        border: none;
    }
    div.stButton > button:first-child:hover {
        background-color: #085224;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Conexão corrigida (idêntica ao seu app de entregas)
@st.cache_resource
def conectar_planilha_retira():
    base_url = "https://googleapis.com" + "/auth/"
    escopos = [base_url + "spreadsheets", base_url + "drive"]
    credenciais_dict = dict(st.secrets["connections"]["gsheets"])
    creds = Credentials.from_service_account_info(credenciais_dict, scopes=escopos)
    cliente = gspread.authorize(creds)
    
    planilha = cliente.open_by_key("1I3V8UxkeQyP1tO7TZIVbQk7HQrxv-FSsz5l3ChCMsV4")
    abas_existentes = [aba.title for aba in planilha.worksheets()]
    
    if "Retira_Conferidos" not in abas_existentes:
        aba_conf = planilha.add_worksheet(title="Retira_Conferidos", rows="2000", cols="10")
        aba_conf.append_row([
            "Requisicao", "Dt_Cadastro", "Cliente", "Transportador", 
            "Valor", "Conferente", "Fim_Conferencia", "Data_Importacao"
        ])
    else:
        aba_conf = planilha.worksheet("Retira_Conferidos")
        
    if "Retira_Baixas" not in abas_existentes:
        aba_baixas = planilha.add_worksheet(title="Retira_Baixas", rows="2000", cols="6")
        aba_baixas.append_row([
            "Data_Hora_Retirada", "Requisicao", "Cliente", 
            "Retirado_Por", "Conferente_Balcao", "Observacao"
        ])
    else:
        aba_baixas = planilha.worksheet("Retira_Baixas")
        
    return aba_conf, aba_baixas

def processar_csv_jacsys(arquivo_csv):
    df = pd.read_csv(arquivo_csv, sep=";", encoding="latin1", dtype=str)
    df = df.dropna(subset=["Requisição"]).copy()
    df["Requisição"] = df["Requisição"].str.strip()
    df = df[df["Requisição"].str.isdigit()]
    
    df["Transportador"] = df["Transportador"].fillna("").str.strip()
    df = df[df["Transportador"].str.contains("RETIRA|BALCAO", case=False, na=False)]
    df = df.drop_duplicates(subset=["Requisição"], keep="first")
    
    colunas_finais = pd.DataFrame({
        "Requisicao": df["Requisição"],
        "Dt_Cadastro": df["Dt.Cadastro"].fillna("").str.strip(),
        "Cliente": df["Cliente"].fillna("").str.strip(),
        "Transportador": df["Transportador"],
        "Valor": df["Vlr.Total"].fillna("0,00").str.strip(),
        "Conferente": df["Conferente"].fillna("").str.strip(),
        "Fim_Conferencia": df["Fim Conf."].fillna("").str.strip()
    })
    return colunas_finais

st.markdown("""
    <div class="header-card">
        <p class="header-title">🏪 Controle de Retira & Balcão</p>
        <p class="header-subtitle">Painel de Pedidos Prontos e Comprovante de Retirada</p>
    </div>
""", unsafe_allow_html=True)

try:
    aba_conf, aba_baixas = conectar_planilha_retira()
    dados_conf = aba_conf.get_all_records()
    dados_baixas = aba_baixas.get_all_records()
except Exception as e:
    st.cache_resource.clear()
    st.error(f"Conexão interrompida pela rede. Clique no botão abaixo para reconectar. Detalhe: {e}")
    if st.button("🔄 Reconectar ao Google Sheets"):
        st.rerun()
    st.stop()

df_conf = pd.DataFrame(dados_conf)
df_baixas = pd.DataFrame(dados_baixas)

if not df_conf.empty:
    df_conf["Requisicao"] = df_conf["Requisicao"].astype(str).str.strip()
    reqs_baixadas = set()
    if not df_baixas.empty:
        reqs_baixadas = set(df_baixas["Requisicao"].astype(str).str.strip())
    df_pendentes = df_conf[~df_conf["Requisicao"].isin(reqs_baixadas)].copy()
else:
    df_pendentes = pd.DataFrame()

tab_painel, tab_baixa, tab_historico = st.tabs([
    "🟢 Prontos para Retirar", 
    "✅ Registrar Retirada (Balcão)", 
    "📋 Histórico de Retiradas"
])

with tab_painel:
    col_m1, col_m2, col_b = st.columns([2, 2, 1])
    with col_m1:
        st.metric("📦 Pedidos Prontos Aguardando Cliente", len(df_pendentes))
    with col_m2:
        st.metric("✅ Retiradas Concluídas", len(df_baixas))
    with col_b:
        if st.button("🔄 Atualizar Tela"):
            st.rerun()

    if not df_pendentes.empty:
        busca = st.text_input("🔍 Buscar por Número da Requisição ou Nome do Cliente:")
        df_exibir = df_pendentes.copy()
        if busca:
            df_exibir = df_exibir[
                df_exibir["Requisicao"].str.contains(busca, case=False, na=False) |
                df_exibir["Cliente"].str.contains(busca, case=False, na=False)
            ]
        st.dataframe(
            df_exibir[["Requisicao", "Dt_Cadastro", "Cliente", "Transportador", "Conferente", "Fim_Conferencia", "Valor"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhum pedido conferido aguardando retirada no momento. Suba o CSV do Jacsys na barra lateral para atualizar.")

with tab_baixa:
    if "enviando_retira" not in st.session_state:
        st.session_state.enviando_retira = False

    if not df_pendentes.empty:
        opcoes_req = ["Selecione o pedido..."] + [
            f"{row['Requisicao']} - {row['Cliente']}" for _, row in df_pendentes.iterrows()
        ]
        escolha = st.selectbox("📋 Selecione a Requisição Pronta:", opcoes_req)
        req_manual = ""
    else:
        escolha = "Selecione o pedido..."
        req_manual = st.text_input("📋 Digite o Número da Requisição:")

    retirado_por = st.text_input("👤 Nome / CPF / Placa de quem retirou:", placeholder="Ex: João Silva - CPF 123.456... ou Placa ABC-1234")
    conferente_balcao = st.text_input("🏷️ Conferente que entregou no balcão:", placeholder="Seu nome")
    obs_retira = st.text_area("📝 Observações (opcional):")

    if st.button("✅ Confirmar Entrega ao Cliente", use_container_width=True, disabled=st.session_state.enviando_retira):
        if escolha != "Selecione o pedido...":
            partes = escolha.split(" - ", 1)
            req_final = partes[0].strip()
            cliente_final = partes[1].strip() if len(partes) > 1 else ""
        else:
            req_final = req_manual.strip()
            cliente_final = "Informado Manualmente"

        if not req_final or not retirado_por.strip() or not conferente_balcao.strip():
            st.error("❌ Preencha a Requisição, quem retirou e o nome do conferente.")
        else:
            st.session_state.enviando_retira = True
            try:
                with st.spinner("Registrando retirada..."):
                    reqs_ja_baixadas = [str(r).strip() for r in aba_baixas.col_values(2)[1:]]
                    if req_final in reqs_ja_baixadas:
                        st.warning(f"⚠️ A Requisição {req_final} já foi baixada anteriormente!")
                    else:
                        agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
                        aba_baixas.append_row([
                            agora, req_final, cliente_final, 
                            retirado_por.strip().upper(), 
                            conferente_balcao.strip().upper(), 
                            obs_retira.strip()
                        ], value_input_option="USER_ENTERED")
                        st.success(f"✅ Requisição {req_final} entregue e registrada às {agora}!")
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {e}")
            finally:
                st.session_state.enviando_retira = False

with tab_historico:
    if not df_baixas.empty:
        st.dataframe(df_baixas.iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma retirada registrada ainda.")

st.sidebar.header("⚙️ Atualização Jacsys (Retira)")
senha_digitada = st.sidebar.text_input("Senha da equipe:", type="password")
senha_correta = st.secrets.get("SENHA_LOGISTICA", "morelate2026")

if senha_digitada == senha_correta:
    st.sidebar.success("Acesso liberado!")
    arquivo_up = st.sidebar.file_uploader("Subir arquivo cns_251_01 (.csv)", type=["csv"])
    
    if arquivo_up is not None:
        if st.sidebar.button("📤 Processar e Atualizar Fila"):
            try:
                with st.spinner("Limpando dados e sincronizando com Google Sheets..."):
                    df_novo = processar_csv_jacsys(arquivo_up)
                    reqs_existentes = set(str(r).strip() for r in aba_conf.col_values(1)[1:])
                    df_para_inserir = df_novo[~df_novo["Requisicao"].isin(reqs_existentes)].copy()
                    
                    if df_para_inserir.empty:
                        st.sidebar.info("Nenhum pedido novo de Retira encontrado neste arquivo.")
                    else:
                        agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
                        df_para_inserir["Data_Importacao"] = agora
                        linhas = df_para_inserir.values.tolist()
                        aba_conf.append_rows(linhas, value_input_option="USER_ENTERED")
                        st.sidebar.success(f"✅ {len(linhas)} novos pedidos do Retira adicionados!")
                        st.rerun()
            except Exception as erro:
                st.sidebar.error(f"Erro ao processar CSV: {erro}")
                
