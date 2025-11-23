#!/usr/bin/env python3
"""
HTTP API wrapper for tiny-agent using agent_core.py

This version uses the refactored agent_core.py, resulting in much cleaner code
with better separation of concerns.
"""

import json
import threading
import queue
import time
import logging
from pathlib import Path
from typing import Optional, Dict
from flask import Flask, request, Response, jsonify

from agent_core import AgentConfig, AgentCallbacks, agent_loop

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Session management
session_queues: Dict[str, Dict[str, queue.Queue]] = {}
session_threads: Dict[str, threading.Thread] = {}
sessions_lock = threading.Lock()

SESSION_TIMEOUT = 300  # 5 minutes


def create_session(session_id: str) -> None:
    """Create a new session with input/output queues"""
    with sessions_lock:
        if session_id in session_queues:
            logger.warning(f"Session {session_id} already exists, cleaning up")
            cleanup_session(session_id)

        session_queues[session_id] = {
            "input": queue.Queue(),
            "output": queue.Queue(),
            "created_at": time.time(),
        }
        logger.info(f"Created session {session_id}")


def cleanup_session(session_id: str) -> None:
    """Clean up session resources (call with sessions_lock held)"""
    if session_id in session_queues:
        del session_queues[session_id]
    if session_id in session_threads:
        del session_threads[session_id]
    logger.info(f"Cleaned up session {session_id}")


def get_session_queues(session_id: str) -> Optional[Dict[str, queue.Queue]]:
    """Get queues for a session"""
    with sessions_lock:
        return session_queues.get(session_id)


def create_api_callbacks(session_id: str, auto_respond: bool = False) -> AgentCallbacks:
    """Create callbacks that communicate via queues for API"""
    queues = get_session_queues(session_id)
    if not queues:
        raise RuntimeError(f"Session {session_id} not found")

    output_queue = queues["output"]
    input_queue = queues["input"]

    def send_output(content: str, event_type: str = "output"):
        """Helper to send output to queue"""
        output_queue.put({"type": event_type, "content": content})

    def on_iteration(current: int, max_iterations: int):
        """Send iteration info"""
        send_output(f"--- Iteration {current}/{max_iterations} ---\n")

    def on_thinking(content: str):
        """Send agent thinking"""
        send_output(f"💭 Agent: {content}\n")

    def on_tool_call(name: str, args: dict):
        """Send tool execution info"""
        send_output(f"🔧 Executing: {name}({args})\n")

    def on_tool_result(result: str):
        """Send tool result (truncated for display)"""
        display = result[:200] + "..." if len(result) > 200 else result
        send_output(f"📋 Result: {display}\n")

    def on_need_input(question: str) -> str:
        """Request input from user via API"""
        if auto_respond:
            return "/done"

        # Send question event
        output_queue.put({"type": "question", "content": question})

        # Wait for response
        try:
            response = input_queue.get(timeout=SESSION_TIMEOUT)
            return response
        except queue.Empty:
            logger.error(f"Session {session_id}: Timeout waiting for user input")
            raise TimeoutError("Timed out waiting for user input")

    def on_error(error: str):
        """Send error"""
        send_output(f"❌ Error: {error}\n", "error")

    return AgentCallbacks(
        on_iteration=on_iteration,
        on_thinking=on_thinking,
        on_tool_call=on_tool_call,
        on_tool_result=on_tool_result,
        on_need_input=on_need_input,
        on_error=on_error,
    )


def run_agent_thread(session_id: str, prompt: str, auto_respond: bool = False) -> None:
    """Run agent in background thread"""
    logger.info(f"Starting agent thread for session {session_id}")

    queues = get_session_queues(session_id)
    if not queues:
        logger.error(f"No queues found for session {session_id}")
        return

    output_queue = queues["output"]

    try:
        # Send initial goal
        output_queue.put({"type": "output", "content": f"🎯 Goal: {prompt}\n"})

        # Find agent directory
        current_dir = Path.cwd()
        if (current_dir / "commands.json").exists():
            agent_dir = current_dir
        elif (Path.home() / ".agent").exists():
            agent_dir = Path.home() / ".agent"
        else:
            raise RuntimeError("commands.json not found in current directory or ~/.agent")

        # Load config
        config = AgentConfig.from_env()

        # Create callbacks
        callbacks = create_api_callbacks(session_id, auto_respond)

        # Run agent
        result = agent_loop(prompt, agent_dir, config, callbacks)

        # Send completion
        output_queue.put({"type": "complete", "content": result})

        logger.info(f"Session {session_id}: Agent completed successfully")

    except Exception as e:
        logger.error(f"Session {session_id}: Agent execution failed: {e}", exc_info=True)
        output_queue.put({"type": "error", "content": f"Error: {str(e)}"})


def generate_sse_stream(session_id: str):
    """Generate Server-Sent Events stream for a session"""
    logger.info(f"Starting SSE stream for session {session_id}")

    queues = get_session_queues(session_id)
    if not queues:
        yield f"data: {json.dumps({'type': 'error', 'content': 'Session not found'})}\n\n"
        return

    output_queue = queues["output"]

    while True:
        try:
            event = output_queue.get(timeout=1.0)
            yield f"data: {json.dumps(event)}\n\n"

            if event["type"] in ("complete", "error"):
                break

        except queue.Empty:
            # Check if thread is alive
            with sessions_lock:
                thread = session_threads.get(session_id)
                if thread and not thread.is_alive():
                    yield f"data: {json.dumps({'type': 'error', 'content': 'Agent thread died'})}\n\n"
                    break

            # Keepalive
            yield ": keepalive\n\n"

        except Exception as e:
            logger.error(f"Session {session_id}: Error in SSE stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            break

    # Cleanup
    with sessions_lock:
        cleanup_session(session_id)


@app.route("/prompt", methods=["POST"])
def handle_prompt():
    """Start a new agent execution"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        session_id = data.get("session_id")
        prompt = data.get("prompt")
        auto_respond = data.get("auto_respond", False)

        if not session_id:
            return jsonify({"error": "session_id is required"}), 400
        if not prompt:
            return jsonify({"error": "prompt is required"}), 400

        logger.info(f"Received prompt for session {session_id}")

        # Create session
        create_session(session_id)

        # Start thread
        thread = threading.Thread(
            target=run_agent_thread, args=(session_id, prompt, auto_respond), daemon=True
        )

        with sessions_lock:
            session_threads[session_id] = thread

        thread.start()

        # Return SSE stream
        return Response(
            generate_sse_stream(session_id),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    except Exception as e:
        logger.error(f"Error handling prompt: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/respond", methods=["POST"])
def handle_response():
    """Send user's response to agent"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        session_id = data.get("session_id")
        response_text = data.get("response")

        if not session_id:
            return jsonify({"error": "session_id is required"}), 400
        if response_text is None:
            return jsonify({"error": "response is required"}), 400

        logger.info(f"Received response for session {session_id}")

        queues = get_session_queues(session_id)
        if not queues:
            return jsonify({"error": "Session not found or expired"}), 404

        queues["input"].put(response_text)
        return jsonify({"status": "ok"})

    except Exception as e:
        logger.error(f"Error handling response: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check"""
    with sessions_lock:
        active_sessions = len(session_queues)
    return jsonify({"status": "healthy", "active_sessions": active_sessions})


@app.route("/sessions", methods=["GET"])
def list_sessions():
    """List active sessions"""
    with sessions_lock:
        sessions = list(session_queues.keys())
    return jsonify({"sessions": sessions})


def cleanup_old_sessions():
    """Background task to clean up expired sessions"""
    while True:
        time.sleep(60)

        with sessions_lock:
            now = time.time()
            expired = [
                sid
                for sid, data in session_queues.items()
                if now - data.get("created_at", now) > SESSION_TIMEOUT
            ]

            for sid in expired:
                logger.info(f"Cleaning up expired session {sid}")
                cleanup_session(sid)


if __name__ == "__main__":
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_old_sessions, daemon=True)
    cleanup_thread.start()

    logger.info("Starting Flask server on http://0.0.0.0:5000")
    logger.info("Endpoints:")
    logger.info("  POST /prompt - Start agent execution")
    logger.info("  POST /respond - Send response to agent")
    logger.info("  GET /health - Health check")
    logger.info("  GET /sessions - List active sessions")

    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
