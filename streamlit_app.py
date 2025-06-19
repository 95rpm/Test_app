# streamlit_app.py
import streamlit as st
import pandas as pd

st.title("⛳ 골프 여행 상품 정규화 도구")

uploaded_file = st.file_uploader("📁 엑셀 파일 업로드", type=["xls", "xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [c.strip().replace('\n', ' ') for c in df.columns]
    st.success("정규화 완료 ✅")
    st.dataframe(df.head(30))
