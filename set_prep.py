"""AI DJ set-prep assistant, headless version.

Claude analyzes a crate of tracks by calling the DJ Track Audio Analyzer Actor through the hosted Apify MCP server, then orders them into a set.
Both the model and the tools run server-side: this script only states the task and renders the answer as a set sheet (tables, emoji, colors) via rich.

Setup: copy .env.example to .env and fill in both keys (or export them):
  ANTHROPIC_API_KEY  - your Anthropic API key (model tokens billed here)
  APIFY_TOKEN        - your Apify API token   (Actor runs billed here)
"""

import os
import sys
import pathlib

import anthropic
import dotenv
import rich.console
import rich.markdown

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to a legacy code page; emoji would print as garbage

console = rich.console.Console()

MODEL = "claude-sonnet-5"
MCP_URL = "https://mcp.apify.com?tools=get-actor-output,musicae/dj-track-audio-analyzer"

# Your crate. Entries can be track URLs, track IDs, ISRCs, or search strings.
TRACKS = [
    "https://open.spotify.com/track/1BJJbSX6muJVF2AK7uH1x4",  # Adam Port & Stryv - Move
    "https://open.spotify.com/track/60sVtP64olfBZlWqKc1nmm",  # Adam Port - Do You Still Think of Me?
    "https://open.spotify.com/track/5cOJ2APoxJfaGjEC7CYc0K",  # Black Coffee - Drive
    "https://open.spotify.com/track/3xTRqSvGEEOFpXrvqGUpvw",  # Black Coffee - Superman
    "https://open.spotify.com/track/5WgW9bG91h4zRUnBr97d6c",  # Keinemusik - Muyè
    "https://open.spotify.com/track/200DiJQhDi69nkGXOrrJgn",  # Keinemusik - The Rapture Pt.III
    "https://open.spotify.com/track/0RMSRyWm9JUqR2fd6HpaGO",  # Rampa - Everything (Mark Fanciulli Remix)
    "https://open.spotify.com/track/3QcqkrUkhGqYnG1Z1XMhPN",  # Themba - Who Is Themba?
]

PROMPT = f"""
You are helping a DJ prepare a set.
Analyze these tracks with the DJ track analyzer tool, then order them into a set: warmup to peak, harmonic (Camelot) transitions where possible.
If you search by keyword, set searchKeywordLimit to 1.

Format the answer in markdown, structured like a set sheet:
- "## 📊 The data": one table of the numbers you used (track, BPM, Camelot, energy, peak, vocal risk, loudness)
- "## 🎚️ The set": one table with position, track, BPM, Camelot, energy, and the transition into the next track marked ✅ harmonic or 🔴 EQ/cut, with the key move
- "## 🔧 The tricky transitions": a short bold-titled paragraph per 🔴 explaining exactly how to play it, using the analysis fields (phrases, loudness, instrumentalness, vocal risk) as evidence
- "## ⚠️ Watch out": the few warnings that matter most (gain staging, vocal clashes, tempo jumps)
No preamble, no conclusion; every line should be something a DJ can use in the booth.

Tracks:
{chr(10).join(TRACKS)}
"""


def stream_turn(client, apify_token, messages):
    """Send one request, render Claude's markdown answer as a set sheet, return the final message."""

    with console.status("Analyzing the crate..."):
        with client.beta.messages.stream(
            model=MODEL,
            max_tokens=16000,
            messages=messages,
            betas=["mcp-client-2025-11-20"],  # the MCP connector is an API beta; without this flag, mcp_servers is rejected
            tools=[{"type": "mcp_toolset", "mcp_server_name": "apify"}],
            mcp_servers=[{"type": "url", "url": MCP_URL, "name": "apify", "authorization_token": apify_token}],
        ) as stream:
            for _ in stream.text_stream:
                pass  # wait for the full answer; repainting partial markdown live leaves blank scroll regions in classic consoles
            response = stream.get_final_message()
    answer = "".join(block.text for block in response.content if block.type == "text")
    console.print(rich.markdown.Markdown(answer))
    return response


def plan_set(client, apify_token):
    """Run the conversation until Claude has delivered the full set plan."""

    messages = [{"role": "user", "content": PROMPT}]
    while True:
        response = stream_turn(client, apify_token, messages)
        if response.stop_reason != "pause_turn":
            return
        # The server paused a long tool loop; send the turn back to resume it.
        messages = [{"role": "user", "content": PROMPT}, {"role": "assistant", "content": response.content}]


def main() -> int:
    dotenv.load_dotenv(pathlib.Path(__file__).with_name(".env"))  # real env vars win over .env values
    apify_token = os.environ.get("APIFY_TOKEN")
    if not apify_token:
        print("APIFY_TOKEN is not set. Copy .env.example to .env and fill it in, or set the variable in your environment.", file=sys.stderr)
        return 1
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    plan_set(client, apify_token)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except anthropic.AuthenticationError:
        print("\nInvalid or missing ANTHROPIC_API_KEY.", file=sys.stderr)
        sys.exit(1)
    except anthropic.RateLimitError as e:
        retry_after = e.response.headers.get("retry-after")
        hint = f"Retry after {retry_after}s." if retry_after else "Retry shortly."
        print(f"\nRate limited by the Anthropic API. {hint}", file=sys.stderr)
        sys.exit(1)
    except anthropic.APIStatusError as e:
        print(f"\nAPI error {e.status_code}: {e.message}", file=sys.stderr)
        sys.exit(1)
    except anthropic.APIConnectionError:
        print("\nNetwork error reaching the Anthropic API.", file=sys.stderr)
        sys.exit(1)
