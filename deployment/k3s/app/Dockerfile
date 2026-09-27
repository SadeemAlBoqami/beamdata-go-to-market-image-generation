FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv
RUN python -m pip install --no-cache-dir "gradio==6.28.0" requests Pillow "openpyxl==3.1.5"
COPY . /srv/app

EXPOSE 7860
CMD ["python", "-m", "app.app"]
