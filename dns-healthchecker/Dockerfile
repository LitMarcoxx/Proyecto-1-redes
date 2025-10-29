FROM debian:stable-slim

RUN apt-get update && apt-get install -y \
    gcc make libcurl4-openssl-dev libjansson-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN make

CMD ["./health-checker"]
