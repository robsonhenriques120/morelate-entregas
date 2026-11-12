
codigo_app = """import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="Morelate - Check de Entrega", layout="centered")

st.title("🚛 Confirmação de Entrega - Morelate")
st.write("Preencha os dados abaixo para registrar o status da entrega.")

numero_nf = st.text_input("📋 Número da Nota Fiscal:", placeholder="Ex: 105432")

motorista = st.selectbox("👤 Entregador:", ["Selecione...", "Carlos Silva", "Marcos Souza", "Roberto Lima"])
status = st.radio("📌 Status da Entrega:", ["🟢 Pedido Entregue OK", "🔴 Cancelado / Recusado"])

motivo_selecionado = "N/A"
observacao = ""

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

arquivo_excel = "base_entregas_morelate.xlsx"

if st.button("🚀 Confirmar Registro", use_container_width=True):
    nf_limpa = numero_nf.strip()
    
    if not nf_limpa or motorista == "Selecione..." or (status == "🔴 Cancelado / Recusado" and motivo_selecionado == "Selecione..."):
        st.error("❌ Preencha o número da Nota Fiscal, o Entregador e o Motivo (se cancelado).")
    else:
        fuso_br = ZoneInfo("America/Sao_Paulo")
        agora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")
        
        dados = {
            "Data_Hora": [agora],
            "Nota_Fiscal": [nf_limpa],
            "Motorista": [motorista],
            "Status": [status],
            "Motivo_Real": [motivo_selecionado],
            "Observacoes": [observacao.strip()]
        }
        df_novo = pd.DataFrame(dados)
        
        try:
            if os.path.exists(arquivo_excel):
                df_existente = pd.read_excel(arquivo_excel, dtype={"Nota_Fiscal": str})
                if nf_limpa in df_existente["Nota_Fiscal"].values:
                    st.warning(f"⚠️ Atenção: A Nota Fiscal {nf_limpa} já foi registrada anteriormente!")
                    st.stop()
                df_final = pd.concat([df_existente, df_novo], ignore_index=True)
            else:
                df_final = df_novo
                
            df_final.to_excel(arquivo_excel, index=False)
            st.balloons()
            st.success(f"✅ Nota Fiscal {nf_limpa} registrada com sucesso às {agora}!")
        except Exception as e:
            st.error(f"⚠️ Erro ao salvar o registro: {e}")

if os.path.exists(arquivo_excel):
    st.divider()
    st.subheader("📊 Resumo Rápido das Entregas")
    df_visualizar = pd.read_excel(arquivo_excel, dtype={"Nota_Fiscal": str})
    st.dataframe(df_visualizar.tail(5), use_container_width=True)
    
    with open(arquivo_excel, "rb") as f:
        st.download_button(
            label="📥 Baixar Planilha Atualizada (base_entregas_morelate.xlsx)",
            data=f,
            file_name="base_entregas_morelate.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
"""

with open("app.py", "w", encoding="utf-8") as f:
    f.write(codigo_app)

print("✅ Arquivo app.py atualizado com sucesso!")
