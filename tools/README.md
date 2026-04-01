# Tools Directory

This directory contains Python scripts that perform deterministic execution tasks.

## Design Principles

- **Single Responsibility**: Each tool does one thing well
- **Deterministic**: Same inputs always produce same outputs
- **Error Handling**: Clear error messages and graceful failures
- **Documentation**: Docstrings explaining purpose, inputs, and outputs
- **Environment Variables**: All credentials from `.env`

## Tool Template

```python
#!/usr/bin/env python3
"""
Tool Name: Brief description

Purpose: What this tool does
Inputs: What it expects
Outputs: What it produces
Usage: python tool_name.py [args]
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main execution function."""
    # Your code here
    pass

if __name__ == "__main__":
    main()
```

## Common Tool Categories

- **Data Collection**: Web scraping, API calls
- **Data Processing**: Transformations, analysis, cleaning
- **Data Export**: Writing to Google Sheets, Slides, databases
- **Utility**: File operations, format conversions

## Best Practices

- Use type hints for clarity
- Include error handling for API calls
- Log important operations
- Make tools reusable across workflows
- Test tools independently before integrating into workflows
