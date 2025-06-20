import streamlit as st
import pandas as pd
from io import BytesIO
from openai import OpenAI

# ✅ GPT 클라이언트 초기화 (Secrets에 API 키 등록 필수)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 📂 엑셀 전체 텍스트 평탄화 함수
def flatten_excel(file):
    xl = pd.ExcelFile(BytesIO(file.read()))
    all_text = ''
    for sheet in xl.sheet_names:
        df = xl.parse(sheet, header=None)
        for row in df.itertuples(index=False):
            line = ' '.join([str(cell) for cell in row if pd.notnull(cell)])
            all_text += line + '\n'
    return all_text.strip()

# 🧠 GPT로 상품 정보 추출
def extract_info_with_gpt(text):
    prompt = f"""
다음은 골프여행 상품 설명입니다. 문장과 표를 분석해서 다음 JSON 구조로 추출해줘:

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

# 🖥️ Streamlit 인터페이스
st.set_page_config(page_title="골프 견적 추출기", layout="wide")
st.title("⛳ 골프 여행 상품 엑셀 → GPT 정보 추출")

uploaded = st.file_uploader("📂 엑셀 파일 업로드", type=["xls", "xlsx"])
if uploaded:
    text = flatten_excel(uploaded)
    st.text_area("📋 엑셀에서 추출된 전체 텍스트", text, height=250)

    if st.button("🧠 GPT로 정보 추출하기"):
        with st.spinner("GPT가 내용을 분석 중입니다..."):
            result = extract_info_with_gpt(text)

        st.subheader("📦 GPT가 추출한 결과")
        st.code(result, language="json")