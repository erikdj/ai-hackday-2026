FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home hallway
COPY --chown=hallway:hallway hallway/ ./hallway/
USER hallway
CMD ["python", "-m", "hallway.agents.desk"]
