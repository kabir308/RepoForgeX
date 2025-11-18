FROM python:3.14-slim

# Install system deps (git, gcc optional)
RUN apt-get update \
  && apt-get install -y --no-install-recommends git ca-certificates openssh-client \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project
COPY . /app

# Create non-root user
RUN useradd --create-home --home-dir /home/repoforge -u 1000 repoforge \
  && chown -R repoforge:repoforge /app

# Install python deps
RUN pip install --no-cache-dir -r requirements.txt

USER repoforge
ENV PATH="/home/repoforge/.local/bin:${PATH}"
EXPOSE 5000

CMD ["python", "-m", "repoforgex.web"]
