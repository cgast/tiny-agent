FROM python:3.11-slim

# Install basic CLI tools that agent might use
RUN apt-get update && apt-get install -y \
    findutils \
    grep \
    coreutils \
    git \
    curl \
    wget \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 agent && \
    mkdir -p /home/agent/.agent && \
    mkdir -p /workspace && \
    chown -R agent:agent /home/agent /workspace

# Set working directory
WORKDIR /workspace

# Copy agent files
COPY --chown=agent:agent agent.py /home/agent/
COPY --chown=agent:agent commands.json /home/agent/.agent/

# Install Python dependencies
RUN pip install --no-cache-dir openai anthropic

# Switch to non-root user
USER agent

# Set environment
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/agent

# Make agent executable
RUN chmod +x /home/agent/agent.py

# Entry point
ENTRYPOINT ["python", "/home/agent/agent.py"]

# Default command (shows usage)
CMD ["--help"]
