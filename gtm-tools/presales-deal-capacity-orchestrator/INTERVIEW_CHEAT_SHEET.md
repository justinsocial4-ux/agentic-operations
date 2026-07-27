# Presales Orchestrator — Interview Cheat Sheet

**Glance at this during the call. Don't read it. Skim the line you need, jump back to the interview.**

---

## The one-line pitch
> "A local prototype that answers one question — where should the presales team spend its next hour? The AI proposes, a manager decides, and nothing writes back to Salesforce or ClickUp."

## The 3 shields (memorize these — your safety answers)
- **"Does this really work with our Salesforce/Gong?"** → "Yes, read-only — but it's labeled **'not live-validated'** until someone authorizes a sandbox and runs a checked live test."
- **"Can the AI just assign people?"** → "No. The optimizer recommends. A manager accepts or overrides. Nothing is booked."
- **"Does it read our calls to judge reps?"** → "Transcripts can prove a *deal's* readiness, like the buyer confirming a requirement. They can **never** pick or score a consultant — that's a hard rule, tested in code."

## The 7 walkthrough steps (what to say at each)
1. **Intro / How the engine decides** → "Recommendation-only prototype, nothing booked or written back." (point at the badges: RECOMMENDATION_ONLY, NOT_LIVE_VALIDATED)
2. **Is the deal ready?** → "Readiness facts need an exact citation before they count. Transcripts can prove a fact, but the engine never uses call text to judge a person."
3. **How urgent and valuable is it?** → "Urgency + readiness + commercial value = one priority score in basis points. Nothing hand-wavy — you see exactly why one deal's above another."
4. **Who is allowed to help?** → "Engine can't go shopping. It only sees people a manager has approved. Fit comes from skills + capacity + availability — never from call text."
5. **Which consultant, and why?** (THE SHOWPIECE) → "Optimizer proves OPTIMAL for the whole portfolio, not greedy per-deal. Shows all hard constraints passed + why this consultant over the alternative. Tie broken by stable ID, never call text."
6. **What does this do to capacity?** → "Capacity heatmap + the EMEA +25% scenario. Labeled 'user-selected assumption, not a forecast.'"
7. **You decide** → "Engine STOPS here. Manager accepts / overrides / rejects / defers. Export is inert — no CRM write, no task, no webhook, no assignment."

## How to run it if he wants to see it
- URL: `http://127.0.0.1:8783` (local, on your laptop)
- Click **"Run fictional demo"** → the walkthrough opens automatically
- Use **Next** to step through; **Skip to full results** for the compact view
- Dark mode: hamburger menu (top-right) → Settings → Theme → Dark

## If he digs in
- Stack: Python, Streamlit dashboard, Google OR-Tools (the optimizer), SQLite local state
- Connectors: Salesforce, ClickUp, Fathom, Gong (read-only); HubSpot is interface-only by design
- 341 automated tests pass; all boundaries enforce in code, not just on paper

## Don't say
- "It's live" / "it works with our systems" (say "read-only, not yet live-validated")
- "Production-ready" (it's `NOT_ASSESSED`)
- "The AI picks the consultant" (it doesn't — code + optimizer do, from approved inputs only)
