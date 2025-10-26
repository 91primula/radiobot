# 베이스 이미지
FROM python:3.11-slim

# ffmpeg 설치
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# 작업 디렉토리
WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

# 환경 변수 로드
ENV PYTHONUNBUFFERED=1

# 봇 실행
CMD ["python", "bot.py"]
