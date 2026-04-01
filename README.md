# AI News Update - WAT Framework

This project uses the **WAT framework** (Workflows, Agents, Tools) to separate AI reasoning from deterministic execution, ensuring reliability and maintainability.

## Architecture Overview

- **Workflows** (`workflows/`): Markdown SOPs that define what to do and how
- **Agents**: AI coordination layer (Claude) that reads workflows and orchestrates tools
- **Tools** (`tools/`): Python scripts that handle deterministic execution

See [CLAUDE.md](CLAUDE.md) for detailed framework documentation.

## Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 3. Google OAuth Setup (if using Google APIs)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable required APIs (Sheets, Slides, etc.)
3. Create OAuth 2.0 credentials
4. Download `credentials.json` to the project root
5. Run your first tool that uses Google APIs - it will generate `token.json`

## Directory Structure

```
.tmp/           # Temporary files (scraped data, intermediate exports)
tools/          # Python scripts for execution
workflows/      # Markdown SOPs
.env            # API keys (gitignored)
credentials.json # Google OAuth (gitignored)
token.json      # Google OAuth token (gitignored)
```

## Usage Pattern

1. Define or update a workflow in `workflows/`
2. Create or use existing tools in `tools/`
3. Let the agent orchestrate execution based on the workflow
4. Deliverables go to cloud services (Google Sheets, Slides, etc.)

## Core Principles

- Local files are for processing only
- Deliverables live in cloud services
- Everything in `.tmp/` is disposable and can be regenerated
- Tools are deterministic; agents handle coordination
- Workflows evolve through a continuous improvement loop
