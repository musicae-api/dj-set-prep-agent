# DJ Set Prep Agent

An AI DJ set-prep assistant: Claude orders a crate of tracks into a set (warmup to peak,
harmonic Camelot transitions) by calling the [DJ Track Audio Analyzer](https://apify.com/musicae/dj-track-audio-analyzer)
Actor as a tool through the [Apify MCP server](https://docs.apify.com/integrations/mcp).

Companion repository for the article *Building an AI DJ set-prep assistant with Claude and the
Apify MCP server*.

## What's here

| File | Purpose |
|---|---|
| `set_prep.py` | Headless version: Anthropic Messages API + MCP connector, renders the set sheet in the terminal with rich |
| `requirements.txt` | Three dependencies (`anthropic`, `python-dotenv`, `rich`) |
| `.env.example` | The two keys you need |
| `sample-output/analysis-sample.json` | Real (trimmed) output of the Actor for one track |

## Interactive setup (Claude Desktop)

1. Settings → Connectors → add the Apify MCP server
2. Paste your Apify API token in its settings
3. Set "Enabled tools" to `get-actor-output,musicae/dj-track-audio-analyzer`

## Interactive setup (Claude Code)

```bash
claude mcp add --transport http apify "https://mcp.apify.com?tools=get-actor-output,musicae/dj-track-audio-analyzer" --header "Authorization: Bearer YOUR_APIFY_TOKEN"
```

## Headless script

```bash
pip install -r requirements.txt
cp .env.example .env # fill in both keys; the script reads .env on its own
python set_prep.py
```

Environment variables that are already set always win over `.env` values.

Edit the `TRACKS` list in `set_prep.py` with your own crate. Entries can be track URLs, track IDs,
ISRCs, or plain search strings ("Keinemusik Muyè"); the Actor resolves all four.

## Costs

- Actor: pay-per-event, **$4.99 per 1,000 analyzed tracks** (~half a cent per track), billed to the
  Apify account whose token authenticates the MCP connection. An 8-track crate ≈ $0.04.
- Model: normal Anthropic API token pricing, billed to your Anthropic account.

If you pass search strings instead of links, keep `searchKeywordLimit` at 1 (the prompt already
asks for this): the default of 10 would bill up to ten results per keyword.

## License

MIT
