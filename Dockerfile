# 베이스 이미지로 Python 3.8 사용
FROM python:3.8-slim-buster

# 작업 디렉토리 설정
WORKDIR /app

# 종속성 파일을 작업 디렉토리로 복사
COPY requirements.txt requirements.txt

# 종속성 설치
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y locales
RUN locale-gen ko_KR.UTF-8
ENV LANG ko_KR.UTF-8
ENV LANGUAGE ko_KR:ko
ENV LC_ALL ko_KR.UTF-8

# 애플리케이션 파일과 정적 파일을 작업 디렉토리로 복사
COPY app.py app.py 
COPY chart.py chart.py
COPY gpt.py gpt.py
COPY templates /app/templates
COPY static /app/static

# 환경 변수 설정
ENV OPENAI_API_KEY="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"

# 애플리케이션 실행
CMD ["python", "app.py"]