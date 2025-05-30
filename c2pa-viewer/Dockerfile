FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Installeer de standaard python3 (3.12 op Noble), pip, venv, en andere benodigdheden
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    tar \
    file \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Download en installeer c2patool
ARG C2PA_VERSION=0.18.0
ARG C2PA_TOOL_TAG=c2patool-v${C2PA_VERSION}
ARG C2PA_TOOL_BASE_URL=https://github.com/contentauth/c2pa-rs/releases/download
ARG C2PA_TOOL_ARCHIVE=c2patool-v${C2PA_VERSION}-x86_64-unknown-linux-gnu.tar.gz

RUN set -ex; \
    echo "Cachebuster voor c2patool installatie: $(date +%s%N)"; \
    TEMP_DIR=$(mktemp -d); \
    DOWNLOAD_URL="${C2PA_TOOL_BASE_URL}/${C2PA_TOOL_TAG}/${C2PA_TOOL_ARCHIVE}"; \
    OUTPUT_FILE="${TEMP_DIR}/${C2PA_TOOL_ARCHIVE}"; \
    curl -L --fail --retry 3 --retry-delay 5 -A "..." -o "${OUTPUT_FILE}" "${DOWNLOAD_URL}"; \
    tar -xzf "${OUTPUT_FILE}" -C "${TEMP_DIR}/"; \
    C2PATOOL_BINARY_PATH=$(find ${TEMP_DIR} -name c2patool -type f -executable -print -quit); \
    mv "${C2PATOOL_BINARY_PATH}" /usr/local/bin/c2patool; \
    chown root:root /usr/local/bin/c2patool; \
    chmod 755 /usr/local/bin/c2patool; \
    rm -rf ${TEMP_DIR}; \
    echo "--- Diagnostische informatie voor /usr/local/bin/c2patool (versie ${C2PA_VERSION}, gnu build on Ubuntu Noble) ---"; \
    ls -l /usr/local/bin/c2patool; \
    file /usr/local/bin/c2patool; \
    echo "GLIBC version provided by the system:"; \
    ldd --version | head -n1 || true; \
    echo "Python version provided by the system:"; \
    python3 --version || true; \
    echo "Checking c2patool dependencies:"; \
    ldd /usr/local/bin/c2patool || echo "ldd check failed"; \
    echo "Attempting to run c2patool --version:"; \
    /usr/local/bin/c2patool --version || echo "c2patool version check failed"; \
    echo "--- Einde diagnostische informatie ---"

COPY ./app/requirements.txt .
# GEWIJZIGD: Gebruik --break-system-packages om de pip fout te omzeilen
# Dit is acceptabel in een Docker container waar we volledige controle hebben.
RUN python3 -m pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY ./app /app
# Forceer dat de app code *na* de c2patool installatie wordt gekopieerd
# en mogelijk de Flask executable die in PATH staat.
# Dit is een long shot om een vreemd cache-effect te voorkomen.
RUN echo "Cachebuster voor app copy: $(date +%s%N)"

RUN mkdir -p /app/uploads && chmod -R 755 /app/uploads
EXPOSE 5000
ENV FLASK_RUN_HOST=0.0.0.0
# Verzeker dat Python de system site-packages gebruikt waar Flask nu is geïnstalleerd
ENV PYTHONPATH=/usr/local/lib/python3.12/dist-packages:/usr/lib/python3/dist-packages

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]