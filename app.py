import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Morelate - Check de Entrega", layout="centered")

st.title("🚛 Confirmação de Entrega - Morelate")
st.write("Preencha os dados abaixo para registrar o status da entrega.")

# Link direto da sua Planilha Google
LINK_PLANILHA = "https://docs.google.com/spreadsheets/d/1I3V8UxkeQyP1tO7TZIVbQk7HQrxv-FSsz5l3ChCMsV4/edit?gid=0#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)
df_existente = conn.read(spreadsheet=LINK_PLANILHA, ttl=0)

numero_nf = st.text_input("📋 Número da Nota Fiscal:", placeholder="Ex: 105432")
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

observacao = st.text_area("📝 Observações (opcional):", placeholder="Descreva brevemente o ocorrido...")

if st.button("🚀 Confirmar Registro", use_container_width=True):
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
                "Observacoes": observacao.strip()
            }])

            df_final = pd.concat([df_existente, df_novo], ignore_index=True)
            conn.update(spreadsheet=LINK_PLANILHA, data=df_final)
            st.balloons()
            st.success(f"✅ Nota Fiscal {nf_limpa} salva na nuvem com sucesso às {agora}!")

st.sidebar.header("🔒 Área da Logística")
senha = st.sidebar.text_input("Senha de acesso:", type="password")

if senha == "morelate2026":
    st.divider()
    st.subheader("📊 Últimos Registros na Planilha Google")
    st.dataframe(df_existente.tail(10), use_container_width=True)
