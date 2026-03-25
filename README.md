# 💠 APEXVITALS v3.5 — Agentic Suite
**"High-performance agentic inference for real-time system observability, remediation, and predictive diagnostics."**

[![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue?logo=python)](https://www.python.org/)
[![AI-Powered](https://img.shields.io/badge/Engine-Gemini%203%20Flash%20Preview-red?logo=google-gemini)](https://aistudio.google.com/)
[![ECE | SRMIST](https://img.shields.io/badge/Research-ECE%20%7C%20SRMIST-orange)](https://www.srmist.edu.in/)

---

## 🔬 Project Overview
**APEXVITALS v3.5** is an AI-integrated system observability dashboard designed for Windows environments, specifically optimized for high-performance hardware like the **HP Omen 16** with an **NVIDIA RTX 5060**. It moves beyond passive monitoring by using **Heuristic Inference** to correlate real-time hardware telemetry with active system power states to provide actionable diagnostic audits.

**v3.5 introduces the Agentic Suite**: Fragment-isolated Neural Chat with streaming AI, an Impact HUD for battery/thermal/network projections, and advanced conditional advisories for hardware integrity and OS optimization.

---

## 🏗 The POD Architecture
The system operates on a modular **POD (Point of Deployment)** framework, ensuring low-latency data flow and secure execution:

### 🧠 POD-C: Diagnostic Engine (Brain)
The core reasoning layer utilizes the **Gemini 3 Flash (Preview)** model to perform deep-trace analysis with **streaming output** for real-time typewriter-style responses:
* **[NEURAL_LOG]:** A high-fidelity technical breakdown for engineers. Focuses on **I/O wait states**, **VRAM fragmentation**, and **thermal ceiling** analysis using precise silicon-level metrics.
* **[HUMAN_READABLE]:** A direct, professional status report for the end-user.
* **[OS_ADVISORY]:** Triggered when Windows NT Kernel overhead exceeds 15% — recommends Posix-compliant environments.
* **[HARDWARE_INTEGRITY]:** Triggered on thermal envelope breach (>80°C GPU or >90% sustained CPU) — warns about silicon degradation and electromigration.

### ⚡ POD-D: Action Engine (Execution)
A specialized remediation tool with **RAM reclaim tracking**:
* **PID-based Remediation:** Targeted termination of resource-heavy processes via PID.
* **RAM Reclaim Tracking:** Tracks cumulative MB saved from terminated processes in the Impact HUD.
* **Safety Guardrails:** Logic-based filters prevent termination of system-critical processes.

### 🌐 POD-N: Network POD (NEW in v3.5)
* **Live I/O Traffic:** Real-time network send/receive delta tracking via `psutil.net_io_counters()`.
* **Displayed in Impact HUD** as live MB throughput per refresh cycle.

---

## 🚀 v3.5 Key Features

### 🎯 Performance Optimization
* **`@st.fragment` Isolation:** Neural Chat is wrapped in a Streamlit fragment — chatting with Gemini only reruns the chat container, NOT the entire dashboard. Eliminates the "dimming/slow" issue.
* **Response Streaming:** Gemini responses stream in real-time with a typewriter cursor (`▌`), providing instant feedback.

### 📊 Impact HUD (4 Metric Cards)
* **🧹 RAM Reclaimed:** Cumulative MB freed from terminated PIDs (persists across session).
* **🌡️ Thermal Safety Margin:** `90°C - GPU Temp` — the throttling gap before thermal shutdown.
* **🌐 POD-N Net I/O:** Live network traffic delta (MB sent + received since last refresh).
* **🔋 Battery Projection:** Estimated minutes gained from CPU load reduction (`10% CPU saved ≈ 15 min`).

### 🧠 Enhanced Heuristic Brain
* **[OS_ADVISORY]:** Recommends Linux transition when Windows kernel overhead > 15% of CPU.
* **[HARDWARE_INTEGRITY]:** Warns about silicon degradation from sustained high temperatures.
* **Power-Aware Diagnostics:** Integration of Windows Power Schemes into AI context.
* **GPU Forensics:** Deep monitoring of GPU Wattage, VRAM Saturation, and Thermal Profiles.

---

## 🛠 Technical Stack
* **Language:** Python 3.13+
* **Framework:** Streamlit (Custom Indigo/Slate Dark Theme with Glassmorphism)
* **Telemetry:** Psutil (Hardware probing), Py3NVML (NVIDIA GPU metrics)
* **Intelligence:** Google GenAI v1 SDK (Gemini 3 Flash Preview, Streaming)
* **OS Integration:** Windows `powercfg` API
* **Performance:** Streamlit Fragments for isolated reruns

---

## 📅 Architecture Diagram
```
POD-A (Sensor) → POD-C (Brain) → POD-D (Action)
                       ↓                ↓
                  POD-N (Network)    Impact HUD
                       ↓
              [OS_ADVISORY] / [HARDWARE_INTEGRITY]
```

---

## 👨‍🔬 Academic Context
Developed as a research project within the **Electronics and Communication Engineering (ECE)** department at **SRMIST**, focusing on the intersection of Hardware Telemetry and Generative AI for autonomous system management.

---

**Author:** R.Anirwin
**Department:** Electronics and Communication Engineering (ECE)  
**Institution:** SRM Institute of Science and Technology (SRMIST)
