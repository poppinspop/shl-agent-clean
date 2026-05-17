FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-root user with UID 1000, a standard on HF Spaces
RUN useradd -m -u 1000 user
USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy and install requirements first (for better caching)
COPY --chown=user ./requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of your application code
COPY --chown=user . .

EXPOSE 7860

# The key is to make your app listen on port 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]