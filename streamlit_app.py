import streamlit as st
import pandas as pd
import json
from io import BytesIO
from openai import OpenAI

# ✅ OpenAI 클라이언트 초기화
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 📂 엑셀 파일에서 모든 텍스트 추출
def flatten_excel(file):
    xl = pd.ExcelFile(BytesIO(file.read()))
    all_text = ''
    for sheet in xl.sheet_names:
        df = xl.parse(sheet, header=None)
        for row in df.itertuples(index=False):
            line = ' '.join([str(cell) for cell in row if pd.notnull(cell)])
            all_text += line + '\n'
    return all_text.strip()

# 🧠 GPT로 실무형 정보 추출
def extract_info_with_gpt(text):
    prompt = f"""
아래는 골프 여행 상품 엑셀에서 추출한 텍스트입니다.
표와 문장을 분석하여 다음 JSON 형식으로 필요한 정보를 추출해 주세요.

- JSON 항목은 실무에서 견적서 자동 생성을 위해 모두 필요합니다.
- 텍스트에 없으면 null 또는 빈 배열로 출력하세요.

```json
{{
  "product_name": "",
  "region": "",
  "departure_date": "",
  "duration": "",
  "rounds_per_day": "",
  "total_rounds": "",
  "price": null,
  "price_by_date": [
    {{
      "date": "2025-07-01",
      "price": 1390000
    }},
    {{
      "date": "2025-07-08",
      "price": 1490000
    }}
  ],
  "flight_included": false,
  "includes": [],
  "excludes": [],
  "hotel": "",
  "golf_courses": [],
  "transport": "",
  "extra_charges": {{
    "single_charge": null,
    "caddie_fee": null,
    "cart_fee": null
  }}
}}

아래 텍스트에서 이 정보를 추출하세요:

{text}
“””
response = client.chat.completions.create(
model=“gpt-4”,
messages=[{“role”: “user”, “content”: prompt}],
temperature=0
)
return response.choices[0].message.content

🖥️ Streamlit 웹앱 UI 구성

st.set_page_config(page_title=“⛳ 골프상품 자동추출기”, layout=“wide”)
st.title(“⛳ 실무용 골프 여행 상품 자동 추출기”)

uploaded = st.file_uploader(“📂 엑셀 파일을 업로드하세요”, type=[“xls”, “xlsx”])

if uploaded:
text = flatten_excel(uploaded)
st.text_area(“📋 엑셀에서 추출된 전체 텍스트”, text, height=300)

if st.button("🧠 GPT로 정보 추출"):
    with st.spinner("GPT가 내용을 분석 중입니다..."):
        result = extract_info_with_gpt(text)

    st.subheader("📦 GPT 응답 JSON")
    st.code(result, language="json")

    try:
        parsed = json.loads(result)
        st.success("✅ JSON 파싱 성공!")
        st.subheader("📊 표로 보기")
        st.json(parsed)
    except Exception as e:
        st.error(f"❌ JSON 파싱 실패: {e}")
        