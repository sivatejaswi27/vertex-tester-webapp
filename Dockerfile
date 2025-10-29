FROM python:3.9-slim

WORKDIR /tester-app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Run Streamlit with Cloud Run compatible settings
CMD streamlit run app.py \
    --server.port=8080 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false