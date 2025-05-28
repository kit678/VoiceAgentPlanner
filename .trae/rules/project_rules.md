# Trae IDE Rules - Transferred from .cursorrules

## Memory Bank & Workflow

### Maintain Memory Bank
Treat memory-bank/ as the canonical knowledge store.
Keep these files fresh and commit them with related code:

*   PRD.md – Product requirements with project overview and functional requirements FR1-FR12
*   architecture.md – Technical design, technology stack, and ADR decisions
*   TASK.md – Backlog ▸ In-Progress ▸ Done checklist with emoji status legend
*   activeContext.md – Today's focus (overwrite each session start)
*   progress.md – "YYYY-MM-DD – ✅ summary" per completed task
*   MANUAL_ACTIONS.md – Steps requiring manual intervention

### Memory Bank Hygiene
Prevent redundancy and staleness:

*   Delete files when content is fully covered elsewhere
*   Archive outdated planning docs that don't reflect current implementation
*   Validate that all referenced files exist before committing
*   If creating new memory bank files, justify why existing files can't be extended

### Unit-test policy (all languages)
Every new function/class gets success, edge and failure tests under /tests mirroring source path.

### Progress.md format rule
Each entry in memory-bank/progress.md MUST follow:
YYYY-MM-DD – ✅ <past-tense summary of completed work>
Example:
2025-05-12 – ✅ Resolved electron-store startup crash and hotkey binding

### On-demand tech-rule sync
If the user types "sync tech rules" or "generate stack rules",
perform the Auto-sync tech rules procedure immediately.

### Auto-sync tech rules
Triggered when:
- User explicitly requests "sync tech rules" or "generate stack rules"
- After completing a task that modified package manifests (package.json, requirements.txt, etc.)
- When adding/removing major dependencies or frameworks

Procedure:
1.  Scan package manifests and file tree for languages/frameworks in use
2.  For each *newly detected* framework, library, or language:
    *   Append a concise stack-specific rule *below* '# --- tech-addon ---'
3.  For each rule already under '# --- tech-addon ---':
    *   If the referenced library or framework is **no longer present**, delete the rule
4.  When a library is **replaced** (e.g., Switch from Express to Fastify):
    *   Remove the obsolete rule for Express
    *   Append a new rule for Fastify
5.  Show the diff for approval and commit via the GitHub MCP with a Conventional-Commit message

## Memory Bank File Update Directives

### When PRD.md update is triggered:
*   Update project overview section to reflect current scope and architecture
*   Add/update functional requirements with FR-XXX format and clear acceptance criteria
*   Append new questions under "## Unanswered Questions" section, never overwrite existing content
*   Ensure alignment between project overview and detailed requirements
*   Maintain structured sections with numbered requirements

### When architecture.md update is triggered:
*   Update technology stack section with exact versions from package manifests
*   Add new ADR entries with format: "YYYY-MM-DD – Decision Title – Brief description"
*   Include structured ADR sections: Decision, Rationale, and impact
*   Update system diagrams to reflect current implementation
*   Document new services, APIs, or major architectural changes
*   Ensure diagrams match actual codebase structure

### When TASK.md update is triggered:
*   Move tasks between sections using emoji status indicators (🔴🟠🟢 for priority, ✅🟡❌ for status)
*   Add new tasks with clear, actionable descriptions and acceptance criteria
*   Include dependencies and blocking relationships
*   Archive completed tasks older than 14 days to maintain readability
*   Maintain clear priority categorization and status legend

### When MANUAL_ACTIONS.md update is triggered:
*   Add new entries with format: "YYYY-MM-DD - [CATEGORY] Description - Status: Pending"
*   Categories: API_SETUP, ENV_CONFIG, EXTERNAL_SERVICE, PERMISSIONS, OTHER
*   Mark completed actions as "Status: Completed - [completion date]"
*   Include specific instructions and required credentials/access
*   Archive completed actions older than 30 days

### When activeContext.md update is triggered:
*   Overwrite entire content with current session focus
*   Include: current task, immediate goals, and context switches
*   Keep under 100 words, bullet-point format preferred
*   Reference relevant TASK.md items and recent progress

### When progress.md update is triggered:
*   Add new entry with format: "YYYY-MM-DD – ✅ <past-tense summary>"
*   Include specific accomplishments, not just task completion
*   Reference relevant code changes, features, or fixes
*   Maintain reverse chronological order (newest first)

### When TASK.md update is triggered:
*   Move tasks between sections: Backlog ▸ In-Progress ▸ Done
*   Add new tasks with clear, actionable descriptions
*   Include acceptance criteria and dependencies
*   Archive Done tasks older than 14 days to maintain readability

## Tech Addons

### Electron.js Best Practices
When working with Electron.js:

*   Utilize IPC (Inter-Process Communication) for communication between main and renderer processes
*   Be mindful of process-specific APIs (e.g., `BrowserWindow` in main, DOM manipulation in renderer)
*   Ensure context isolation and enable `contextBridge` for secure preload scripts
*   Follow security best practices outlined in the Electron documentation

### JavaScript Development Standards
When writing JavaScript:

*   Use modern ECMAScript features where appropriate (ES6+)
*   Prefer `const` and `let` over `var`
*   Employ asynchronous patterns (Promises, async/await) for non-blocking operations
*   Follow a consistent coding style (e.g., Airbnb, StandardJS, or project-defined)

# --- tech-addon ---

### Conda Environment Management
When executing terminal commands for this project:

*   Always activate the conda environment "voiceapp" before running any commands
*   Use format: `conda activate voiceapp && [your_command]` for single commands
*   For multi-step operations, activate once at the beginning of the session
*   This ensures all Python dependencies and project-specific libraries are available