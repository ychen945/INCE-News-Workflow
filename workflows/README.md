# Workflows Directory

This directory contains markdown SOPs (Standard Operating Procedures) that define how tasks should be executed.

## Workflow Structure

Each workflow should include:

1. **Objective**: What this workflow accomplishes
2. **Required Inputs**: What information/data is needed to start
3. **Tools Required**: Which scripts from `tools/` are used
4. **Steps**: Ordered sequence of operations
5. **Expected Outputs**: What gets produced and where
6. **Edge Cases**: Known issues and how to handle them
7. **Lessons Learned**: Accumulated knowledge from past executions

## Example Workflow Template

```markdown
# [Workflow Name]

## Objective
Brief description of what this accomplishes.

## Required Inputs
- Input 1: description
- Input 2: description

## Tools Required
- `tools/script_name.py`

## Steps
1. Step one description
2. Step two description
3. ...

## Expected Outputs
- Output 1: Where it goes (e.g., Google Sheet URL)
- Output 2: Format and location

## Edge Cases
- **Issue**: How to handle
- **Issue**: How to handle

## Lessons Learned
- Date: What was learned and how workflow was improved
```

## Best Practices

- Keep workflows focused on a single objective
- Update workflows when you discover better approaches
- Document rate limits, timing quirks, and API constraints
- Reference tools by their exact filename
- Specify cloud service destinations for deliverables
