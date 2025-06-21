import streamlit as st
import pandas as pd
import PyPDF2
import openpyxl
from PIL import Image
import io
import base64
import openai
from supabase import create_client, Client
import json
import os
from datetime import datetime
import uuid

# 페이지 설정

st.set_page_config(
page_title=“파일 정보 추출 시스템”,
page_icon=“📄”,
layout=“wide”
)

# 환경 변수 설정 (Streamlit secrets 사용)

try:
OPENAI_API_KEY = st.secrets[“OPENAI_API_KEY”]
SUPABASE_URL = st.secrets[“SUPABASE_URL”]
SUPABASE_KEY = st.secrets[“SUPABASE_KEY”]
except KeyError:
st.error(“환경 변수가 설정되지 않았습니다. Streamlit secrets를 확인해주세요.”)
st.stop()

# OpenAI 클라이언트 초기화

openai.api_key = OPENAI_API_KEY

# Supabase 클라이언트 초기화

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class FileProcessor:
“”“파일 처리 클래스”””

```
def __init__(self):
    self.supported_formats = {
        'pdf': self.extract_pdf_text,
        'xlsx': self.extract_excel_data,
        'xls': self.extract_excel_data,
        'jpg': self.extract_image_text,
        'jpeg': self.extract_image_text,
        'png': self.extract_image_text
    }

def extract_pdf_text(self, file):
    """PDF 텍스트 추출"""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"PDF 처리 중 오류 발생: {str(e)}")
        return None

def extract_excel_data(self, file):
    """Excel 데이터 추출"""
    try:
        df = pd.read_excel(file)
        # 데이터프레임을 텍스트로 변환
        text = df.to_string(index=False)
        return text
    except Exception as e:
        st.error(f"Excel 처리 중 오류 발생: {str(e)}")
        return None

def extract_image_text(self, file):
    """이미지에서 텍스트 추출 (GPT-4V 사용)"""
    try:
        # 이미지를 base64로 인코딩
        image = Image.open(file)
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        st.error(f"이미지 처리 중 오류 발생: {str(e)}")
        return None

def process_file(self, file):
    """파일 형식에 따라 적절한 처리 함수 호출"""
    file_extension = file.name.split('.')[-1].lower()
    
    if file_extension in self.supported_formats:
        return self.supported_formats[file_extension](file)
    else:
        st.error(f"지원하지 않는 파일 형식입니다: {file_extension}")
        return None
```

class GPTProcessor:
“”“GPT API를 이용한 정보 추출 클래스”””

```
def __init__(self):
    self.client = openai.OpenAI(api_key=OPENAI_API_KEY)

def extract_information(self, content, file_type, extraction_prompt):
    """GPT API를 이용해 정보 추출"""
    try:
        if file_type in ['jpg', 'jpeg', 'png']:
            # 이미지 분석
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": extraction_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": content
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
        else:
            # 텍스트 분석
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 문서에서 중요한 정보를 추출하는 전문가입니다. 요청된 정보를 JSON 형태로 구조화하여 반환해주세요."
                    },
                    {
                        "role": "user",
                        "content": f"{extraction_prompt}\n\n문서 내용:\n{content}"
                    }
                ],
                max_tokens=1000
            )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"GPT API 처리 중 오류 발생: {str(e)}")
        return None
```

class DatabaseManager:
“”“Supabase 데이터베이스 관리 클래스”””

```
def __init__(self):
    self.supabase = supabase

def save_extracted_data(self, file_name, file_type, extracted_data, original_content):
    """추출된 데이터를 데이터베이스에 저장"""
    try:
        data = {
            "id": str(uuid.uuid4()),
            "file_name": file_name,
            "file_type": file_type,
            "extracted_data": extracted_data,
            "original_content": original_content[:5000] if len(original_content) > 5000 else original_content,  # 내용 제한
            "created_at": datetime.now().isoformat(),
            "processed": True
        }
        
        result = self.supabase.table("extracted_files").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        st.error(f"데이터베이스 저장 중 오류 발생: {str(e)}")
        return None

def get_all_records(self):
    """모든 레코드 조회"""
    try:
        result = self.supabase.table("extracted_files").select("*").order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        st.error(f"데이터 조회 중 오류 발생: {str(e)}")
        return []
```

def main():
“”“메인 애플리케이션”””
st.title(“📄 파일 정보 추출 시스템”)
st.markdown(”—”)

```
# 사이드바 설정
st.sidebar.title("설정")

# 추출 프롬프트 설정
extraction_prompt = st.sidebar.text_area(
    "정보 추출 프롬프트",
    value="""다음 문서에서 중요한 정보를 추출해주세요:
```

- 제목 또는 주제
- 주요 키워드 (5개 이내)
- 핵심 내용 요약
- 날짜 정보 (있는 경우)
- 연락처 정보 (있는 경우)
- 금액 정보 (있는 경우)

결과를 JSON 형태로 반환해주세요.”””,
height=200
)

```
# 인스턴스 생성
file_processor = FileProcessor()
gpt_processor = GPTProcessor()
db_manager = DatabaseManager()

# 메인 컨텐츠
col1, col2 = st.columns([2, 1])

with col1:
    st.header("파일 업로드")
    
    uploaded_file = st.file_uploader(
        "파일을 선택하세요",
        type=['pdf', 'xlsx', 'xls', 'jpg', 'jpeg', 'png'],
        help="지원 형식: PDF, Excel, 이미지 파일"
    )
    
    if uploaded_file is not None:
        st.success(f"파일 업로드 완료: {uploaded_file.name}")
        
        # 파일 정보 표시
        file_details = {
            "파일명": uploaded_file.name,
            "파일 크기": f"{uploaded_file.size:,} bytes",
            "파일 형식": uploaded_file.type
        }
        st.json(file_details)
        
        # 처리 버튼
        if st.button("파일 처리 시작", type="primary"):
            with st.spinner("파일 처리 중..."):
                # 1. 파일 내용 추출
                content = file_processor.process_file(uploaded_file)
                
                if content:
                    st.success("파일 내용 추출 완료!")
                    
                    # 2. GPT API로 정보 추출
                    with st.spinner("GPT API로 정보 추출 중..."):
                        file_extension = uploaded_file.name.split('.')[-1].lower()
                        extracted_info = gpt_processor.extract_information(
                            content, file_extension, extraction_prompt
                        )
                        
                        if extracted_info:
                            st.success("정보 추출 완료!")
                            
                            # 3. 데이터베이스에 저장
                            with st.spinner("데이터베이스에 저장 중..."):
                                saved_record = db_manager.save_extracted_data(
                                    uploaded_file.name,
                                    file_extension,
                                    extracted_info,
                                    content if isinstance(content, str) else str(content)
                                )
                                
                                if saved_record:
                                    st.success("데이터베이스 저장 완료!")
                                    
                                    # 추출된 정보 표시
                                    st.subheader("추출된 정보")
                                    st.text_area("결과", extracted_info, height=300)
                                    
                                    # JSON 파싱 시도
                                    try:
                                        json_data = json.loads(extracted_info)
                                        st.json(json_data)
                                    except:
                                        st.info("JSON 형태로 파싱할 수 없습니다. 텍스트 형태로 표시됩니다.")

with col2:
    st.header("처리 기록")
    
    # 새로고침 버튼
    if st.button("기록 새로고침"):
        st.rerun()
    
    # 저장된 기록 조회
    records = db_manager.get_all_records()
    
    if records:
        for record in records[:10]:  # 최근 10개만 표시
            with st.expander(f"{record['file_name']} ({record['created_at'][:10]})"):
                st.write(f"**파일 형식:** {record['file_type']}")
                st.write(f"**처리 시간:** {record['created_at']}")
                
                if record['extracted_data']:
                    st.write("**추출된 정보:**")
                    st.text_area("", record['extracted_data'], height=100, key=f"record_{record['id']}")
    else:
        st.info("저장된 기록이 없습니다.")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>📄 파일 정보 추출 시스템 | Powered by OpenAI GPT & Supabase</p>
    </div>
    """, 
    unsafe_allow_html=True
)
```

if **name** == “**main**”:
main()