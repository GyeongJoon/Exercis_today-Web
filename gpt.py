import openai
import os

# 환경 변수로 API 키 설정
os.environ["OPENAI_API_KEY"] = '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'

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

def ask_chatgpt(prompt):
    response = openai.ChatCompletion.create( # 질문 보내기
        model="gpt-3.5-turbo",  # 최신 모델 이름
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150  # 원하는 응답의 최대 토큰 수 설정
    )
    return response.choices[0].message["content"]

# 예제 질문
question = "오늘 날짜는?"

# ChatGPT API를 사용하여 질문에 답변 받기
answer = ask_chatgpt(question)
print(f"질문: {question}")
print(f"답변: {answer}")
