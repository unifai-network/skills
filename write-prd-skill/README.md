# PRD Writer

**An AI-Powered Product Requirements Document Generator that turns vague ideas into engineering-ready specs.**

`prd-writer` is an agent skill that transforms a single sentence, a rough feature idea, or a product concept into a complete, structured Product Requirements Document (PRD). It covers both frontend requirements (with ASCII wireframes, interaction specs, component states, and copy) and backend requirements (with data field definitions, business rules, sorting logic, and edge cases).

---

## Core Features

### 1. Guided Requirements Clarification
When user input is incomplete, the skill asks structured questions to fill in the gaps — prioritized, concise, and never overwhelming. It provides reasonable assumptions for the user to confirm, so the conversation moves forward efficiently.

### 2. Full-Stack PRD Generation
Generates a comprehensive PRD covering:
- **Frontend**: ASCII wireframes for every key page state, detailed interaction specs (action -> response -> result), component states, and exact copy/labels.
- **Backend**: Data field definitions (type, source, calculation, update frequency), business rules in condition-action format, API design outlines, and edge case handling.

### 3. Iterative Refinement
After generating the initial draft, the skill proactively highlights potential gaps, suggests areas to refine, and walks through all `[TBD]` items with the user.

---

## Trigger Conditions

This skill activates when the user mentions any of the following (in Chinese or English):

- "PRD", "product requirements document", "feature spec"
- "write requirements", "organize requirements", "spec this out"
- "turn this idea into a document", "help me write up this feature"
- Or simply throws out a vague product idea and expects structured output

---

## Usage

### For AI Agents (Natural Language Prompts)

Just describe what you want:

> "I want to add a leaderboard feature — help me write a PRD."

> "Help me turn this idea into a product requirements document: users can bind their X account and display their avatar on the ranking page."

> "Write requirements for a portfolio dashboard."

The skill will start by clarifying key unknowns, then generate a full PRD in Markdown.

### Output Structure

```
# [Feature Name] Product Requirements Document

## 1. Overview
  - Background & Goals
  - Core User Scenarios

## 2. Frontend Requirements
  - 2.1 [Page / Module Name]
    - ASCII Wireframe
    - Interaction Specs
  - 2.2 [Page / Module Name]
    - ...

## 3. Backend Requirements
  - 3.1 Data Field Definitions
  - 3.2 Business Rules & Logic
  - 3.3 API Design Outline
  - 3.4 Edge Cases & Error Handling

## 4. Open Questions (if any)
```

---

## ASCII Wireframe Conventions

The skill uses a consistent set of symbols for wireframes:

| Symbol | Meaning |
|--------|---------|
| `+--+` `\|  \|` | Container / Card border |
| `[ Button ]` | Clickable button |
| `(○)` / `(●)` | Radio button (unselected / selected) |
| `[ ]` / `[✓]` | Checkbox (unselected / selected) |
| `▼` | Expandable dropdown |
| `>` | Clickable link / navigation |
| `...` | Truncated or omitted content |
| `<placeholder>` | Input field |

---

## Output Format

- Default output is **Markdown**.
- Language follows the user's input: Chinese input produces a Chinese PRD, English input produces an English PRD.
- Document length scales with complexity — a small UI tweak gets 1-2 pages, a multi-page feature with complex backend logic gets as much detail as needed.

---

## Directory Structure

```text
write-prd-skill/
├── SKILL.md    # Agent prompt and workflow directives
└── README.md   # This document
```

---

*Built for the UnifAI Network Skills Ecosystem.*
