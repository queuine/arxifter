FROM python:3.12-slim
RUN apt update \
    && apt install -y \
        procps \
        psmisc \
        g++ \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app/arxifter
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["/bin/bash"]
