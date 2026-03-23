# CLAUDE.md — ApexVitals v3.0

> **Project Intelligence File** | POD Architecture Reference | SRMIST ECE Project
> This file provides architectural context, development standards, and operational commands for AI-assisted development of ApexVitals.

---

## 1. Project Identity

| Field | Value |
|---|---|
| **Project Name** | ApexVitals v3.0 |
| **Type** | Windows System Observability Dashboard |
| **Institution** | SRMIST — ECE Department |
| **Entry Point** | `apexvitals.py` |
| **UI Paradigm** | Cyberpunk / Glassmorphism (Streamlit) |
| **AI Engine** | Google Gemini 2.0 Flash |

### Core Stack

```
Python          → Application runtime
Streamlit       → UI framework (Cyberpunk/Glassmorphism theme)
psutil          → Cross-platform hardware telemetry
py3nvml         → NVIDIA GPU sensor access (temperature, VRAM, utilization)
google-genai    → Gemini 2.0 Flash SDK
python-dotenv   → Environment variable management
pywin32         → Windows API access
```

---

## 2. POD Architecture

ApexVitals uses a three-layer POD architecture:

```
┌─────────────────────────────────────────────────────────┐
│                     APEXVITALS RUNTIME                    │
│                                                         │
│   ┌──────────┐     ┌──────────┐     ┌──────────────┐   │
│   │  POD-A   │────▶│  POD-C   │────▶│    POD-D     │   │
│   │ Scanner  │     │  Brain   │     │   Action     │   │
│   └──────────┘     └──────────┘     └──────────────┘   │
│   Telemetry        AI Diagnosis     Agentic Execution   │
└─────────────────────────────────────────────────────────┘
```

---

### POD-A — Scanner (Hardware Telemetry)

**Responsibility:** Collect real-time hardware metrics.

**Key Function:** `get_system_telemetry()` returns:
- CPU usage, RAM usage, top processes
- GPU temperature, VRAM, power draw (via py3nvml)
- Disk usage, disk I/O counters
- Network I/O (sent/recv bytes)
- Windows power plan

---

### POD-C — Brain (AI Diagnostic Layer)

**Responsibility:** Interpret telemetry and generate structured diagnostic output.

**Functions:**
- `get_ai_diagnosis()` — Full diagnostic mode with dual-output format
- `get_chat_response()` — Conversational chatbot mode

**Dual-Output Format:**
```
[NEURAL_LOG]
Technical diagnostic data, confidence scores, anomaly flags
[/NEURAL_LOG]

[HUMAN_READABLE]
Plain-language summary with actionable advice
[/HUMAN_READABLE]
```

**Kill Request Protocol:** AI can suggest `[KILL_REQUEST: <PID>]` for runaway processes.

---

### POD-D — Action (Agentic Execution Layer)

**Responsibility:** Execute system operations with safety guardrails.

**The Bouncer:** `kill_process(pid)` enforces:
- Protected PIDs: {0, 4} (System Idle, System)
- Protected processes: explorer.exe, svchost.exe, lsass.exe, csrss.exe, etc.
- SYSTEM-owned process rejection
- Returns `(success: bool, message: str)`

---

## 3. Core Features

### System Vitality Index (SVI)

Calculated by `calculate_vitality_index(cpu, ram, gpu_temp)`:

```python
score = 100.0
if cpu > 85:      score -= (cpu - 85) * 1.5
if ram > 90:      score -= (ram - 90) * 2.5
if gpu_temp > 82: score -= (gpu_temp - 82) * 1.2
return max(0.0, round(score, 1))
```

**Status Bands:**
| Score | Status | Color |
|-------|--------|-------|
| 80-100 | OPTIMAL | #00ff9d |
| 55-79 | NOMINAL | #ffd60a |
| 30-54 | STRESSED | #ff6b35 |
| 0-29 | CRITICAL | #ff2d55 (pulsing animation) |

### Live Mode

- Toggle in sidebar enables auto-refresh
- `time.sleep(refresh_interval)` + `st.rerun()` at end of main()
- AI calls remain manual (rate-limit safe)

### Neural Chat

- Toggle enables conversational mode
- Multi-turn context with session history
- System telemetry prepended to each query

### Telemetry History

- Rolling 60-entry history in `st.session_state.history`
- Three `st.line_chart()` visualizations: CPU, RAM, GPU temp over time

### Diagnostic Export

- JSON export with full snapshot + AI diagnosis
- Filename: `apexvitals_report_YYYYMMDD_HHMMSS.json`

---

## 4. Development Commands

### Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GEMINI_API_KEY=your_key_here" > .env
```

### Run Commands

```bash
# Start the dashboard
streamlit run apexvitals.py

# Start with custom port
streamlit run apexvitals.py --server.port 8502

# Headless mode (no auto browser)
streamlit run apexvitals.py --server.headless true
```

---

## 5. Windows-Specific Integrations

### Power Plan Detection

```python
subprocess.check_output("powercfg /getactivescheme", shell=True)
```

### GPU Monitoring (NVIDIA only)

Requires py3nvml. Gracefully degrades if:
- No NVIDIA GPU present
- Drivers not installed
- NVML not available

### Process Safety

The Bouncer prevents accidental termination of:
- System processes (PID 0, 4)
- Windows shell processes
- Services (svchost, services.exe, etc.)
- SYSTEM-owned processes

---

## 6. Session State Keys

Initialize at app start:

```python
st.session_state.history          # List of telemetry snapshots (max 60)
st.session_state.chat_history     # List of {role, content} dicts
st.session_state.last_diagnosis   # Last AI diagnosis result
st.session_state.pending_kills      # List of PIDs from [KILL_REQUEST] tags
st.session_state.last_ai_call     # Timestamp for rate limiting
st.session_state.auto_refresh     # Bool toggle
st.session_state.refresh_interval # Int seconds
```

---

## 7. AI Collaboration Guidelines

- **POD boundaries are sacred.** Keep scanner, brain, and action logic separate.
- **The Bouncer is non-negotiable.** Never make protected process lists configurable.
- **Snapshot-on-Demand is deliberate.** Don't auto-trigger Gemini calls.
- **Use v3 color constants.** Reference the NEON_* and BG_* variables, don't hardcode.
- **Handle psutil exceptions.** All process iterations must catch NoSuchProcess and AccessDenied.
- **Model name:** Use `"gemini-2.0-flash"` (not gemini-3-flash-preview).

---

## 8. File Structure

```
apexvitals/
├── apexvitals.py          # Main application (single-file architecture)
├── .env                   # API key (never commit)
├── requirements.txt       # Dependencies
├── CLAUDE.md              # This file
└── README.md              # User documentation
```

---

*ApexVitals v3.0 — SRMIST ECE Project | CLAUDE.md last updated: 2026*
