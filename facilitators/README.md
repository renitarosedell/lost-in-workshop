# Facilitators

> **Attendees: you don't need anything in this folder.**
> Everything required to complete the workshop is in [`create-agent/`](../create-agent/) and [`workshop/`](../workshop/).

This folder contains the server-side infrastructure and tooling used by the people **running** the workshop:

| Folder / File | Purpose |
| --- | --- |
| `lost-in-raleigh/` | MCP game server + FastAPI admin UI (quest management, leaderboard) |
| `a2a-expert/` | A2A transport expert agent consulted by attendees in Step 5 |
| `bundles/` | Pre-built ZIP document bundles served to agents during the quest |
| `instructions/` | MCP server system prompt that defines the game behaviour |
| `scripts/` | PowerShell deployment automation (`deploy.ps1`) |
| `lost-in-raleigh-app.yaml` | Azure Container App export for the game server |

For full setup and deployment instructions, see the [Instructor Guide](https://roelantd.github.io/lost-in-workshop/workshop/instructor-guide) and [Deployment Guide](https://roelantd.github.io/lost-in-workshop/workshop/deployment-guide) on the workshop site.
