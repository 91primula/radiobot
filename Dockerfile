FROM python:3.11-slim

# ffmpeg 설치 (음성 재생용)
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
run pip install -U yt-dlp


COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
