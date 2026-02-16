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
COPY --chown=agent:agent agent_core.py /home/agent/
COPY --chown=agent:agent agent_cli.py /home/agent/
COPY --chown=agent:agent agent_api.py /home/agent/
COPY --chown=agent:agent agent.py /home/agent/
COPY --chown=agent:agent commands.json /home/agent/.agent/

# Install Python dependencies (including Flask for agent_api.py)
RUN pip install --no-cache-dir openai anthropic flask

# Switch to non-root user
USER agent

# Set environment
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/agent

# Make agent files executable
RUN chmod +x /home/agent/*.py

# Expose Flask API port
EXPOSE 5000

# Entry point - run agent-api.py for web use
ENTRYPOINT ["python", "/home/agent/agent_api.py"]

# Default command (none needed for API server)
CMD []
