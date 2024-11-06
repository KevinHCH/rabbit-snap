# Define Python version as an argument
ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim

RUN apt-get update && \
  apt-get install -y gnupg curl && \
  curl -fsSL https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - && \
  echo "deb https://dl.bintray.com/rabbitmq/debian $(lsb_release -sc) main" | tee /etc/apt/sources.list.d/rabbitmq.list && \
  apt-get update && \
  apt-get install -y rabbitmq-server && \
  rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Berlin

# Show the currently running commands
SHELL ["sh", "-exc"]

# Set working directory
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt --no-cache-dir
RUN playwright install
COPY . /app
# See <https://hynek.me/articles/docker-signals/>.
STOPSIGNAL SIGINT
EXPOSE 8000

CMD ["sh", "-c", "service rabbitmq-server start && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

