# ---- Dockerfile ----
FROM python:3.12-slim

# install headless Chromium
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        chromium chromium-driver && \
    rm -rf /var/lib/apt/lists/*

# create app directory
WORKDIR /app

# copy code
COPY . /app

# install python deps
RUN pip install --no-cache-dir -r requirements.txt

# needed so Selenium can find Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV PATH="/usr/lib/chromium:/usr/bin:${PATH}"

CMD ["python", "Main.py"]
