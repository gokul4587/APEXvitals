# 💠 APEXVITALS v2.0
**"Context-aware heuristic inference for high-fidelity system observability and remediation."**

[![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue?logo=python)](https://www.python.org/)
[![AI-Powered](https://img.shields.io/badge/Engine-Gemini%203%20Flash%20Preview-red?logo=google-gemini)](https://aistudio.google.com/)
[![ECE | SRMIST](https://img.shields.io/badge/Research-ECE%20%7C%20SRMIST-orange)](https://www.srmist.edu.in/)

---

## 🔬 Project Overview
**APEXVITALS v2.0** is an AI-integrated system observability dashboard designed for Windows environments, specifically optimized for high-performance hardware like the **HP Omen 16** with an **NVIDIA RTX 5060**. It moves beyond passive monitoring by using **Heuristic Inference** to correlate real-time hardware telemetry with active system power states to provide actionable diagnostic audits.

---

## 🏗 The POD Architecture
The system operates on a modular **POD (Point of Deployment)** framework, ensuring low-latency data flow and secure execution:

### 🧠 POD-C: Diagnostic Engine (Brain)
The core reasoning layer utilizes the **Gemini 3 Flash (Preview)** model to perform deep-trace analysis. v2.0 implements a **Dual-Output Logic** system, removing all colloquial analogies in favor of engineering-grade forensics:
* **[NEURAL_LOG]:** A high-fidelity technical breakdown for engineers. Focuses on **I/O wait states**, **VRAM fragmentation**, and **thermal ceiling** analysis using precise silicon-level metrics.
* **[HUMAN_READABLE]:** A direct, professional status report for the end-user. It identifies the root cause of performance degradation and provides a single, actionable remediation step.

### ⚡ POD-D: Action Engine (Execution)
A specialized remediation tool that allows for direct system intervention:
* **PID-based Remediation:** Targeted termination of resource-heavy or unresponsive processes via PID.
* **Safety Guardrails:** Logic-based filters prevent the accidental termination of system-critical processes (Kernel/OS level), ensuring system stability during remediation.

---

## 🚀 v2.0 Key Features
* **Power-Aware Diagnostics:** Integration of the `get_power_plan()` helper to ingest active Windows Power Schemes (Performance, Balanced, Power Saver) into the AI context for mode-specific optimization advice.
* **GPU Forensics:** Deep monitoring of **GPU Wattage (W)**, **VRAM Saturation**, and **Thermal Profiles** via the NVIDIA NVML integration.
* **Silicon-to-Context Correlation:** Cross-referencing CPU load cycles with GPU power draw to identify hardware-level bottlenecks.

---

## 🛠 Technical Stack
* **Language:** Python 3.13+
* **Framework:** Streamlit (Custom Cyberpunk Glassmorphism UI)
* **Telemetry:** Psutil (Hardware probing), Py3NVML (NVIDIA GPU metrics)
* **Intelligence:** Google GenAI v1 SDK (Gemini 3 Flash Preview)
* **OS Integration:** Windows `powercfg` API

---

## 📅 Roadmap (v3.0)
* **Attended Automation:** Implementation of a conversational Chatbot Agent for real-time system querying.
* **System Vitality Index (SVI):** A weighted health score (0-100) based on thermals, memory pressure, and thread count.
* **Predictive Forecasting:** Time-series trend analysis to forecast potential thermal throttling or RAM overflow before they occur.

---

## 👨‍🔬 Academic Context
Developed as a research project within the **Electronics and Communication Engineering (ECE)** department at **SRMIST**, focusing on the intersection of Hardware Telemetry and Generative AI for autonomous system management.

---

**Author:** [Your Name/GitHub]  
**Department:** Electronics and Communication Engineering (ECE)  
**Institution:** SRM Institute of Science and Technology (SRMIST)
