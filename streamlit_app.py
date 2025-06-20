import streamlit as st
import pandas as pd
from io import BytesIO
from openai import OpenAI

# ✅ API 키는 반드시 Streamlit Cloud > Secrets 에서 관리하세요
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 📂 엑셀 내용을 문자열로 평탄화
def flatten_excel(file):
    xl = pd.ExcelFile(BytesIO(file.read()))
    all_text = ''
    for sheet in xl.sheet_names:
        df = xl.parse(sheet, header=None)
        for row in df.itertuples(index=False):
            line = ' '.join([str(cell) for cell in row if pd.notnull(cell)])
            all_text += line + '\n'
    return all_text.strip()

# 🧠 GPT로 정보 추출 요청
def extract_info_with_gpt(text):
    prompt = f"""
다음은 골프여행 상품 설명입니다. 문장과 표에서 정보를 추론해 다음 JSON 구조로 정리해주세요:

{{
  "product_name": "",
  "departure_date": "",
  "region": "",
  "price": ,
  "includes": [],
  "excludes": []
}}

텍스트:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content

# 🖥️ Streamlit UI
st.title("⛳ 골프 여행 엑셀 → GPT 기반 정보 추출기")

uploaded = st.file_uploader("📂 엑셀 파일 업로드", type=["xls", "xlsx"])
if uploaded:
    text = flatten_excel(uploaded)
    st.text_area("📄 전체 텍스트 보기", text, height=250)

    if st.button("🧠 GPT로 정보 추출하기"):
        with st.spinner("GPT가 정보를 분석 중입니다..."):
            result = extract_info_with_gpt(text)

        st.subheader("📦 추출된 정보")
        st.code(result, language="json")