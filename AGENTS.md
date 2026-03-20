# AGENTS.md

## Learned User Preferences

- When the user asks to add something to the punchlist, only perform punchlist updates; do not also try to fix or implement the issue.
- Before creating a commit or pushing, ask the user for approval.
- When presenting UI or design directions, offer multiple distinct options when practical rather than a single mockup.
- For interactive Playwright E2E work, follow write-spec-first, then code, then debug, then re-run tests until every test in scope passes.

## Learned Workspace Facts

- Rangers is a shared dashboard platform for ~6 friends — multi-user, widget-based architecture
- Dual-language project: JavaScript (frontend, tooling, widgets) + Python (scrapers, automation, data)
- Repo carries most configuration (CLAUDE.md, .cursor/rules, .claude-flow, skills); team members must install Claude CLI, RuFlo, get .env.local securely, and enable MCPs in Cursor to replicate the setup
- Use config/shared-facts.json and .cursor/rules as source of truth when reviewing or validating code and UI against project standards
