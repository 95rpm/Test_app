import streamlit as st
import pandas as pd
import json
from io import BytesIO
import openai  # 수정: openai 라이브러리를 정확히 사용

# ✅ OpenAI 클라이언트 초기화
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 📂 엑셀 파일에서 모든 텍스트 추출
def flatten_excel(file):
    try:
        xl = pd.ExcelFile(BytesIO(file.read()), engine="openpyxl")
        all_text = ''
        for sheet in xl.sheet_names:
            df = xl.parse(sheet, header=None)
            for row in df.itertuples(index=False):
                line = ' '.join([str(cell) for cell in row if pd.notnull(cell)])
                all_text += line + '\n'
        return all_text.strip()
    except Exception as e:
        st.error(f"❌ 파일 처리 중 오류 발생: {e}")
        return None

# 🧠 GPT로 실무형 정보 추출
def extract_info_with_gpt(text):
    prompt = f"""
    너는 여행사에서 사용하는 '골프여행 상품 견적 자동화 시스템'에 탑재된 GPT 분석기야.  
    업로드된 상품 설명 문서에서 **아래 JSON 구조**에 맞춰 필요한 정보를 정확하게 추출해줘.

    반드시 지켜야 할 규칙은 다음과 같아

    1. 모든 항목을 JSON 포맷으로 출력해. 텍스트나 설명 말고 JSON만 반환해.
    2. 항목이 없는 경우에도 null 또는 빈 배열 []로 명시적으로 채워.
    3. 숫자는 따옴표 없이 숫자형(int)으로 출력해.
    4. "price_by_date"는 날짜별 가격이 있다면 최대 5개까지 정리해주고, 없다면 빈 배열로.
    5. "flight_included"는 항공이 포함되었는지 문맥을 이해해서 true/false로 정확하게 판단해.
    6. 포함/불포함 항목은 문장이나 표로 표현된 내용까지 감지해서 배열로 정리해.

    출력 JSON 형식은 아래와 같아. 이 형식을 그대로 유지해줘:

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

    이제 아래 텍스트를 분석해서 위 JSON 형식으로 추출해줘:

    {text}
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content
    except openai.error.OpenAIError as e:
        st.error(f"❌ GPT 호출 오류: {e}")
        return None

#🖥️ Streamlit 웹앱 UI 구성
st.set_page_config(page_title="⛳ 골프상품 자동추출기", layout="wide")
st.title("⛳ 실무용 골프 여행 상품 자동 추출기")

uploaded = st.file_uploader("📂 엑셀 파일을 업로드하세요", type=["xls", "xlsx"])

if uploaded:
    text = flatten_excel(uploaded)
    if text:
        st.text_area("📋 엑셀에서 추출된 전체 텍스트", text, height=300)

        if st.button("🧠 GPT로 정보 추출"):
            with st.spinner("GPT가 내용을 분석 중입니다..."):
                result = extract_info_with_gpt(text)

            if result:
                st.subheader("📦 GPT 응답 JSON")
                st.code(result, language="json")

                try:
                    # JSON 파싱
                    if result.strip().startswith("{") and result.strip().endswith("}"):
                        parsed = json.loads(result)
                        st.success("✅ JSON 파싱 성공!")
                        st.subheader("📊 표로 보기")
                        st.json(parsed)
                    else:
                        st.error("❌ JSON 형식이 아닙니다.")
                except json.JSONDecodeError as e:
                    st.error(f"❌ JSON 파싱 실패: {e}")
                except Exception as e:
                    st.error(f"❌ 예상치 못한 오류 발생: {e}")