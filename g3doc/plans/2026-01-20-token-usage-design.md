# Gemini Token Usage Calculator Design

## Overview
A standalone Python tool to calculate and display token consumption and estimated costs from Gemini CLI session histories stored in `~/.gemini/tmp/`.

## Goals
- Aggregate token usage by day and model.
- Calculate costs based on configurable pricing data.
- provide a clean, terminal-friendly tabular output.
- No `google3` dependencies for portability.

## Components

### 1. Data Discovery
- Root path: `~/.gemini/tmp/`
- Search pattern: `*/chats/session-*.json`
- Each JSON file represents a session and contains an array of `messages`.

### 2. Aggregation Logic
- **Group by**: Date (YYYY-MM-DD from `startTime`) and `model`.
- **Metrics**: 
  - `sessions`: Count of session files.
  - `input`: Sum of `tokens.input`.
  - `cached`: Sum of `tokens.cached`.
  - `output`: Sum of `tokens.output` + `tokens.thoughts`.
  - `total`: Sum of all tokens.

### 3. Pricing Configuration
- Optional `pricing.json` in the script directory.
- Default rates (Flash):
  - Input: $0.10 / 1M tokens
  - Cached: $0.05 / 1M tokens
  - Output: $0.40 / 1M tokens

### 4. Output Format
Tabular breakdown in terminal.

| DATE | MODEL | SESSIONS | INPUT | CACHED | OUTPUT | TOTAL | COST |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-01-20 | gemini-3-flash-preview | 12 | 450,200 | 120,000 | 8,100 | 578,300 | $0.28 |

## Implementation Plan
1. Create `scripts/token-usage.py`.
2. Implement file discovery using `pathlib`.
3. Implement JSON parsing and data aggregation using `collections.defaultdict`.
4. Implement pricing logic.
5. Implement formatted table output (using f-strings or `tabulate` if lightweight).
