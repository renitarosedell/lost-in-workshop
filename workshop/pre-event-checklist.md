---
title: Pre-Event Facilitator Checklist
description: Complete these checks 10–15 minutes before attendees arrive.
---

# Pre-Event Facilitator Checklist

<Badge type="danger" text="Facilitators only" />

::: warning Complete before opening the room
All items should be ✅ before attendees arrive. This checklist takes ~15 minutes.
:::

---

## 1. Infrastructure

- [ ] Game server is running and reachable:
  ```bash
  curl https://<GAME_URL>/mcp
  ```
  Expected: HTTP 200 with JSON MCP capability manifest.

- [ ] A2A expert is running and reachable:
  ```bash
  curl -X POST https://<A2A_URL>/a2a \
    -H "Content-Type: application/json" \
    -d '{"message": "Best way from Moore Square to Glenwood South?"}'
  ```
  Expected: HTTP 200 with `{ "advice": "..." }`.

- [ ] Document bundles are accessible:
  ```bash
  curl -I https://<STORAGE_ACCOUNT>.blob.core.windows.net/bundles/raleigh/glenwood_getaway.zip
  ```
  Expected: HTTP 200 with `Content-Type: application/zip`.

- [ ] Admin dashboard loads: `https://<GAME_URL>/admin`
  Expected: "Lost in Raleigh - Admin" page with an empty players table.

---

## 2. State

- [ ] No leftover players from a previous test run. If there are:
  ```bash
  curl -X DELETE https://<GAME_URL>/api/players
  ```
  Or click **Reset ALL players** on the admin dashboard and confirm twice.

- [ ] Leaderboard shows 0 entries on the admin dashboard.

---

## 3. Attendee environment

- [ ] MCP_SERVER_URL has been posted to the workshop Slack/Teams channel.
- [ ] Azure Foundry setup guide link has been shared with attendees.
- [ ] `.env.example` is checked in and contains the correct MCP_SERVER_URL placeholder.

---

## 4. Azure AI Foundry

- [ ] Your own `gpt-4o-mini` deployment is responding:
  ```bash
  python create-agent/steps/step1_foundry_test.py
  ```
  Expected: `Connected to Azure OpenAI!`

- [ ] Confirm the deployment is in a region with sufficient quota (≥ 10K TPM × expected attendees).

---

## 5. End-to-end smoke test

- [ ] Run the full fallback agent against the live server:
  ```bash
  cd create-agent
  python agent.py
  ```
  Expected: All six phases complete, final score printed, entry appears on admin leaderboard.

- [ ] Delete the smoke-test player from the admin dashboard after the test.

---

## 6. Room and materials

- [ ] Projector / screen shows the admin dashboard (so attendees can watch the leaderboard).
- [ ] Workshop guide (`workshop/workshop.md`) is open in a browser or PDF viewer on the projector.
- [ ] Azure Foundry setup guide (`workshop/azure-foundry-setup.md`) is ready to share.
- [ ] Wi-Fi credentials are written on the whiteboard.
- [ ] Subscription codes (if using Azure passes) are printed and at each seat.

---

## 7. Contingency

::: warning Have a local fallback ready
- [ ] You have a local copy of the game server that can run offline:
  ```bash
  cd lost-in-raleigh
  python server.py
  ```
- [ ] You have printed copies of the `.env.example` with the fallback localhost URL in case of network issues.
:::

---

## ✅ All checks complete - you are ready!

Good luck, and remember: the leaderboard auto-refreshes every 5 seconds.
