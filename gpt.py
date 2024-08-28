import os
from openai import OpenAI

# 환경 변수에서 API 키를 가져옵니다.
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

client = OpenAI(api_key=api_key)

def ask_chatgpt(prompt):
    # ChatCompletion API 호출
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # 사용할 모델을 지정
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000
    )
    # 응답 메시지를 가져와 반환합니다.
    return response.choices[0].message.content