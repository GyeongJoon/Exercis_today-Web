# 베이스 이미지로 Python 3.8 사용
FROM python:3.8-slim-buster

# 작업 디렉토리 설정
WORKDIR /app

# 종속성 파일을 작업 디렉토리로 복사
COPY requirements.txt requirements.txt

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y locales
RUN apt-get install -y fonts-nanum

# 로케일 설정
RUN locale-gen ko_KR.UTF-8
ENV LANGUAGE=ko_KR:ko
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 불필요한 파일 제거
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# 애플리케이션 파일과 정적 파일을 작업 디렉토리로 복사
COPY app.py app.py 
COPY chart.py chart.py
COPY gpt.py gpt.py
COPY templates /app/templates
COPY static /app/static

# 포트 설정
EXPOSE 5002

# 애플리케이션 실행
CMD ["python", "app.py"]
