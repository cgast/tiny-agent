#!/usr/bin/env python3
"""
Example client for tiny-agent HTTP API

This demonstrates how to interact with the agent-api.py server
in both auto-respond and interactive modes.
"""

import requests
import json
import sys
import uuid
from typing import Iterator

API_URL = "http://localhost:5000"


def parse_sse_event(line: str) -> dict:
    """Parse a Server-Sent Event line"""
    if line.startswith('data: '):
        return json.loads(line[6:])
    return None


def run_agent_auto(prompt: str) -> None:
    """
    Run agent in auto-respond mode (fire-and-forget).
    Agent will automatically respond with /done to any follow-up questions.
    """
    session_id = f"auto-{uuid.uuid4().hex[:8]}"

    print(f"🚀 Starting agent in auto-respond mode")
    print(f"   Session ID: {session_id}")
    print(f"   Prompt: {prompt}")
    print("-" * 60)

    response = requests.post(
        f"{API_URL}/prompt",
        json={
            "session_id": session_id,
            "prompt": prompt,
            "auto_respond": True
        },
        stream=True
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return

    # Process SSE stream
    for line in response.iter_lines():
        if not line:
            continue

        line = line.decode('utf-8')
        event = parse_sse_event(line)

        if not event:
            continue

        if event['type'] == 'output':
            # Print output directly
            print(event['content'], end='', flush=True)

        elif event['type'] == 'question':
            # In auto-respond mode, this shouldn't happen
            # but we'll display it anyway
            print(f"\n[Question: {event['content']}]")

        elif event['type'] == 'complete':
            print("\n" + "=" * 60)
            print(f"✅ Complete: {event['content']}")
            print("=" * 60)
            break

        elif event['type'] == 'error':
            print("\n" + "=" * 60)
            print(f"❌ Error: {event['content']}")
            print("=" * 60)
            break


def run_agent_interactive(prompt: str) -> None:
    """
    Run agent in interactive mode.
    User will be prompted to answer follow-up questions.
    """
    session_id = f"interactive-{uuid.uuid4().hex[:8]}"

    print(f"🚀 Starting agent in interactive mode")
    print(f"   Session ID: {session_id}")
    print(f"   Prompt: {prompt}")
    print("-" * 60)

    # Start the request in a way that allows us to handle questions
    response = requests.post(
        f"{API_URL}/prompt",
        json={
            "session_id": session_id,
            "prompt": prompt,
            "auto_respond": False
        },
        stream=True
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return

    # Process SSE stream
    for line in response.iter_lines():
        if not line:
            continue

        line = line.decode('utf-8')
        event = parse_sse_event(line)

        if not event:
            continue

        if event['type'] == 'output':
            # Print output directly
            print(event['content'], end='', flush=True)

        elif event['type'] == 'question':
            # Agent is asking a question - get user input
            print(f"\n{'=' * 60}")
            print(f"❓ Agent Question: {event['content']}")
            print(f"{'=' * 60}")

            # Get user response
            try:
                user_response = input("Your response: ").strip()
            except (EOFError, KeyboardInterrupt):
                user_response = "/quit"

            # Send response to agent
            resp = requests.post(
                f"{API_URL}/respond",
                json={
                    "session_id": session_id,
                    "response": user_response
                }
            )

            if resp.status_code != 200:
                print(f"❌ Failed to send response: {resp.json()}")
                break

            print(f"✓ Response sent: {user_response}")
            print("-" * 60)

        elif event['type'] == 'complete':
            print("\n" + "=" * 60)
            print(f"✅ Complete: {event['content']}")
            print("=" * 60)
            break

        elif event['type'] == 'error':
            print("\n" + "=" * 60)
            print(f"❌ Error: {event['content']}")
            print("=" * 60)
            break


def check_health() -> bool:
    """Check if the API server is running"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is healthy")
            print(f"   Active sessions: {data.get('active_sessions', 0)}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {API_URL}")
        print(f"   Make sure agent-api.py is running:")
        print(f"   python agent-api.py")
        return False
    except Exception as e:
        print(f"❌ Error checking health: {e}")
        return False


def main():
    """Main entry point"""
    print("=" * 60)
    print("Tiny-Agent API Client Example")
    print("=" * 60)
    print()

    # Check server health
    if not check_health():
        sys.exit(1)

    print()

    # Example prompts
    examples = [
        {
            "prompt": "List all Python files in the current directory",
            "mode": "auto"
        },
        {
            "prompt": "What is the size of the agent.py file?",
            "mode": "auto"
        },
        {
            "prompt": "Find the most recently modified file",
            "mode": "interactive"
        }
    ]

    if len(sys.argv) > 1:
        # User provided a prompt
        prompt = " ".join(sys.argv[1:])
        mode = "interactive"  # Default to interactive for user prompts

        if "--auto" in sys.argv:
            mode = "auto"
            # Remove --auto from prompt
            prompt = prompt.replace("--auto", "").strip()

        print(f"Running custom prompt in {mode} mode...")
        print()

        if mode == "auto":
            run_agent_auto(prompt)
        else:
            run_agent_interactive(prompt)

    else:
        # Run examples
        print("No prompt provided. Choose an example:")
        print()

        for i, example in enumerate(examples, 1):
            print(f"{i}. [{example['mode']:12}] {example['prompt']}")

        print(f"{len(examples) + 1}. [custom      ] Enter your own prompt")
        print()

        try:
            choice = input("Enter choice (1-4): ").strip()
            choice_num = int(choice)

            if 1 <= choice_num <= len(examples):
                example = examples[choice_num - 1]
                print()

                if example['mode'] == 'auto':
                    run_agent_auto(example['prompt'])
                else:
                    run_agent_interactive(example['prompt'])

            elif choice_num == len(examples) + 1:
                prompt = input("\nEnter your prompt: ").strip()
                mode_choice = input("Mode (auto/interactive) [interactive]: ").strip().lower()
                mode = "auto" if mode_choice == "auto" else "interactive"

                print()
                if mode == "auto":
                    run_agent_auto(prompt)
                else:
                    run_agent_interactive(prompt)

            else:
                print("Invalid choice")
                sys.exit(1)

        except (ValueError, KeyboardInterrupt):
            print("\nCancelled")
            sys.exit(0)


if __name__ == "__main__":
    main()
