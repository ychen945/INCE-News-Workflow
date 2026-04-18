FROM python:3.11-slim

# Install Chromium for Selenium (more reliable than Google Chrome in Docker)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create runtime directories
RUN mkdir -p .tmp output

# Tell Selenium to use Chromium instead of Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Railway sets PORT dynamically; default to 5001 for local runs
ENV PORT=5001

EXPOSE 5001

CMD gunicorn --bind 0.0.0.0:$PORT --timeout 600 --threads 4 webapp.app:app
