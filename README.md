# ⚡ APEXVITALS: Agentic System Intelligence
**"Bridging the Telemetry-Reasoning Gap with Silicon-to-Sentiment Analysis"**

[![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue?logo=python)](https://www.python.org/)
[![AI-Powered](https://img.shields.io/badge/AI-Gemini%203%20Flash-red?logo=google-gemini)](https://aistudio.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🔬 Project Overview
**APEXVITALS** is a high-performance system diagnostic engine that transforms raw hardware telemetry into actionable engineering narratives. Unlike traditional monitors that only display numbers, APEXVITALS utilizes **In-Context Reasoning** to diagnose system bottlenecks like thermal throttling, memory pressure, and context switching in real-time.

### 🏗 The POD Architecture
The system is built on a modular **POD (Point of Deployment)** architecture, ensuring a clean separation of concerns:
* **POD-A (Sensor):** Low-level kernel probing via `psutil`.
* **POD-B (Context):** Serialization of raw data into a structured JSON "State Object."
* **POD-C (Brain):** Edge-to-Cloud inference using the **Google GenAI v1 SDK**.
* **POD-D (Action):** An agentic execution layer for real-time process termination.

---

## 🛠 Features
* **Cyberpunk Interface:** A high-contrast, professional UI built with Streamlit and custom CSS.
* **Real-time Hardware Probing:** Live monitoring of CPU Frequency, RAM Saturation, and Disk I/O.
* **AI Diagnostics:** Narrative reports identifying *why* the system is behaving a certain way.
* **Process Action Agent:** Integrated "Kill Switch" to terminate resource-heavy PIDs directly from the dashboard.
* **Safety Handshake:** Built-in Permission Gate to ensure secure hardware access.

---

## 🚦 Prerequisites & Setup

### 1. API Configuration
You must enable the **Generative Language API** in your Google Cloud Project.
* Visit: [Google Cloud API Library](https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com)
* Click **ENABLE**.
* Generate your API Key at [Google AI Studio](https://aistudio.google.com/).

### 2. Local Installation
```bash
# Clone the repository
git clone [https://github.com/gokul4587/APEXvitals.git](https://github.com/gokul4587/APEXvitals.git)
cd APEXvitals

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run apexvitals.py