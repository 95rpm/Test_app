import streamlit as st
import pandas as pd
import openai
from io import BytesIO

# OpenAI API Key (꼭 st.secrets로 관리 추천)
openai.api_key = "YOUR_OPENAI_API_KEY"

st.title("⛳ 골프 상품 자동 추출기 (GPT 기반)")

# 엑셀 텍스트 전체 펼치기
def flatten_excel(file):
    xl = pd.ExcelFile(BytesIO(file.read()))
    all_text = ''
    for sheet in xl.sheet_names:
        df = xl.parse(sheet, header=None)
        for row in df.itertuples(index=False):
            line = ' '.join([str(cell) for cell in row if pd.notnull(cell)])
            all_text += line + '\n'
    return all_text.strip()

# GPT에게 요청
def extract_info_with_gpt(text):
    prompt = f"""
다음은 골프여행 상품 설명입니다. 이 안에서 핵심 정보를 JSON 형태로 추출해줘.
필요 시 부정/조건/기준을 이해해서 정확히 분류해줘.

필요한 항목:
- product_name (문장에서 추론)
- departure_date (가능하면 날짜 추출)
- region (국가/도시/지역)
- price (숫자만)
- includes (포함내역 리스트)
- excludes (불포함 리스트)

텍스트:
{text}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    reply = response.choices[0].message.content
    try:
        result = eval(reply)  # GPT 응답이 딕셔너리일 경우
        return result
    except:
        st.warning("⚠️ GPT 응답이 예상과 달라요. 내용 확인해주세요.")
        return reply

# UI
uploaded = st.file_uploader("📂 엑셀 파일 업로드", type=["xls", "xlsx"])
if uploaded:
    text = flatten_excel(uploaded)
    st.text_area("📋 전체 텍스트", text, height=200)

    if st.button("🧠 GPT로 정보 추출하기"):
        result = extract_info_with_gpt(text)
        st.subheader("📦 추출된 정보")
        st.json(result)