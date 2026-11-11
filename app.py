
import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Morelate - Check de Entrega", layout="centered")

query_params = st.query_params
nf_automatica = query_params.get("nf", "")

st.title("🚛 Confirmação de Entrega - Morelate")

if nf_automatica:
    st.success(f"📋 **Nota Fiscal Identificada:** {nf_automatica}")
else:
    st.warning("⚠️ Nenhum QR Code detectado.")
    nf_automatica = st.text_input("Digite a Nota Fiscal:")

motorista = st.selectbox("Entregador:", ["Selecione...", "Carlos Silva", "Marcos Souza", "Roberto Lima"])
status = st.radio("Status:", ["🟢 Pedido Entregue OK", "🔴 Cancelado / Recusado"])

motivo_selecionado = "N/A"
observacao = ""

if status == "🔴 Cancelado / Recusado":
    motivo_selecionado = st.selectbox(
        "Motivo Real:",
        ["Selecione...", "Cliente Ausente", "Recusa por Atraso", "Avaria na Mercadoria", "Erro de Preço/Boleto"]
    )
    observacao = st.text_area("Observações:")

arquivo_excel = "base_entregas_morelate.xlsx"

if st.button("🚀 Confirmar Registro", use_container_width=True):
    if not nf_automatica or motorista == "Selecione..." or (status == "🔴 Cancelado / Recusado" and motivo_selecionado == "Selecione..."):
        st.error("❌ Preencha todos os campos obrigatórios.")
    else:
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        dados = {
            "Data_Hora": [agora],
            "Nota_Fiscal": [nf_automatica],
            "Motorista": [motorista],
            "Status": [status],
            "Motivo_Real": [motivo_selecionado],
            "Observacoes": [observacao]
        }
        df_novo = pd.DataFrame(dados)
        
        try:
            if os.path.exists(arquivo_excel):
                df_final = pd.concat([pd.read_excel(arquivo_excel), df_novo], ignore_index=True)
            else:
                df_final = df_novo
                
            df_final.to_excel(arquivo_excel, index=False)
            st.balloons()
            st.success("✅ Salvo com sucesso no arquivo Excel!")
        except PermissionError:
            st.error("⚠️ Erro de Permissão: O arquivo Excel está aberto! Por favor, feche a planilha e tente novamente.")

if os.path.exists(arquivo_excel):
    st.divider()
    with open(arquivo_excel, "rb") as f:
        st.download_button(
            label="📥 Baixar Planilha Atualizada (.xlsx)",
            data=f,
            file_name="base_entregas_morelate.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
