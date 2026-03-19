"""
APEXVITALS - AI-Driven System Health Narrator
Production-grade diagnostic tool for ECE portfolios
Architecture: POD-A (Sensor) → POD-B (Context) → POD-C (Brain) → POD-D (Action)
Enhanced Module: POD-G (GPU Telemetry)
"""

import streamlit as st
import psutil
import json
import pandas as pd
import os
import subprocess
from datetime import datetime
from google import genai
from google.genai import errors
from dotenv import load_dotenv

# Optional GPU imports with graceful fallbacks
try:
    import py3nvml.py3nvml as nvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

# Load environment variables from .env
load_dotenv()

def get_power_plan():
    """Detects the active Windows power plan."""
    try:
        if os.name == 'nt':
            result = subprocess.check_output("powercfg /getactivescheme", shell=True).decode()
            if "High performance" in result: return "Performance Mode"
            if "Balanced" in result: return "Balanced Mode"
            if "Power saver" in result: return "Power Saver Mode"
            return "Custom Plan"
        return "OS Default"
    except:
        return "Unknown"

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION & THEME
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="APEXVITALS | AI System Diagnostic",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Cyberpunk Theme Constants
CYAN = "#00f2ff"
CYAN_DIM = "#00f2ff30"
BG_BLACK = "#060606"
GLASS_BG = "rgba(10, 10, 15, 0.8)"
TEXT_PRIMARY = "#e0e0e0"
TEXT_SECONDARY = "#888888"
STATUS_GREEN = "#00ff88"
STATUS_RED = "#ff3366"
GPU_ACCENT = "#00ff88"

CUSTOM_CSS = f"""
<style>
    .stApp {{
        background-color: {BG_BLACK};
        color: {TEXT_PRIMARY};
    }}
    .stApp h1, .stApp h2, .stApp h3 {{
        color: {CYAN};
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 0 10px {CYAN_DIM};
    }}
    .metric-card {{
        background: {GLASS_BG};
        border: 1px solid {CYAN_DIM};
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
    }}
    .metric-value {{
        font-size: 36px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 5px;
    }}
    .metric-label {{
        font-size: 14px;
        color: {CYAN};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .glass-panel {{
        background: {GLASS_BG};
        border: 1px solid {CYAN_DIM};
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 20px;
        backdrop-filter: blur(12px);
    }}
    .stButton>button {{
        background: transparent;
        color: {CYAN};
        border: 1px solid {CYAN};
        border-radius: 4px;
        width: 100%;
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        background: {CYAN_DIM};
        box-shadow: 0 0 15px {CYAN_DIM};
        border-color: {CYAN};
    }}
    .stTextInput>div>div>input {{
        background: #111 !important;
        color: {CYAN} !important;
        border: 1px solid {CYAN_DIM} !important;
    }}
    .gpu-metric {{
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid {GPU_ACCENT};
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# POD-A: SENSOR (Telemetry Logic)
# ─────────────────────────────────────────────────────────────────────────────

def get_system_telemetry():
    """Captures real-time hardware telemetry."""
    cpu_usage = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()

    # Get Top 5 high-impact processes
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Sort and take top 5
    top_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:5]

    return {
        "cpu_usage": cpu_usage,
        "ram_usage": memory.percent,
        "ram_available_gb": round(memory.available / (1024**3), 2),
        "top_processes": top_processes,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

# ─────────────────────────────────────────────────────────────────────────────
# POD-G: GPU TELEMETRY (NVIDIA NVML)
# ─────────────────────────────────────────────────────────────────────────────

def get_gpu_telemetry():
    """Captures NVIDIA GPU telemetry using py3nvml."""
    if not NVML_AVAILABLE:
        return {"error": "py3nvml not installed"}

    try:
        nvml.nvmlInit()
        device_count = nvml.nvmlDeviceGetCount()

        if device_count == 0:
            nvml.nvmlShutdown()
            return {"error": "No NVIDIA GPU detected"}

        handle = nvml.nvmlDeviceGetHandleByIndex(0)
        gpu_name = nvml.nvmlDeviceGetName(handle)
        temp_info = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
        memory_info = nvml.nvmlDeviceGetMemoryInfo(handle)
        vram_used_gb = round(memory_info.used / (1024**3), 2)
        vram_total_gb = round(memory_info.total / (1024**3), 2)
        vram_percent = round((memory_info.used / memory_info.total) * 100, 1)
        power_draw_mw = nvml.nvmlDeviceGetPowerUsage(handle) / 1000.0

        nvml.nvmlShutdown()

        return {
            "gpu_name": gpu_name.decode() if isinstance(gpu_name, bytes) else gpu_name,
            "temperature": temp_info,
            "vram_used_gb": vram_used_gb,
            "vram_total_gb": vram_total_gb,
            "vram_percent": vram_percent,
            "power_draw_w": round(power_draw_mw, 1),
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
    except Exception as e:
        return {"error": f"GPU Telemetry Offline: {str(e)}"}

# ─────────────────────────────────────────────────────────────────────────────
# POD-B: CONTEXT (Data Preparation)
# ─────────────────────────────────────────────────────────────────────────────

def prepare_brain_context(telemetry, gpu_data):
    """Formats telemetry and GPU stats into a structured context for the AI."""
    context = {
        "HARDWARE": telemetry,
        "GPU": gpu_data
    }
    return json.dumps(context, indent=2)

# ─────────────────────────────────────────────────────────────────────────────
# POD-C: BRAIN (AI Reasoning)
# ─────────────────────────────────────────────────────────────────────────────

def get_ai_diagnosis(api_key, context_json):
    """AI reasoning via Gemini API - POD-C Lead Diagnostic Engine."""
    sanitized_key = api_key.strip()
    if not sanitized_key:
        return {
            "neural_log": "ERROR: Handshake Aborted. API Key Missing.",
            "human_readable": "Please provide a Gemini API Key to initialize the brain module."
        }

    try:
        client = genai.Client(api_key=sanitized_key)
        power_mode = get_power_plan()
        
        prompt = f"""
        You are POD-C, the lead diagnostic engine for APEXVITALS. 
        Context: HP Omen 16 (RTX 5060). 
        Current Mode: {power_mode}

        --- INPUT DATA ---
        {context_json}

        --- TASK ---
        Provide a factual, two-part system audit. AVOID metaphors, analogies, or 'cheesy' language.

        [NEURAL_LOG]
        - High-fidelity technical breakdown for engineers.
        - Reference specific metrics (Wattage, VRAM, Clock speeds).
        - Identify bottlenecks (e.g., CPU-bound, Thermal ceiling, I/O wait).

        [HUMAN_READABLE]
        - Simple, professional English for a standard user.
        - Direct status report: Tell the user exactly why the system is behaving this way.
        - Provide one clear, actionable fix (e.g., 'Lower shadow settings' or 'Change to Performance Mode').

        STRICT: No 'Chef', 'High-end sports car', or 'Athlete' metaphors. Be direct.
        Total response must be under 180 words.
        """

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )
        
        response_text = response.text
        neural_log = ""
        human_readable = ""

        if "[NEURAL_LOG]" in response_text:
            parts = response_text.split("[NEURAL_LOG]")[1].split("[HUMAN_READABLE]")
            neural_log = parts[0].strip()
            if len(parts) > 1:
                human_readable = parts[1].strip()
        
        if not neural_log or not human_readable:
            neural_log = "Error parsing neural response."
            human_readable = response_text

        return {"neural_log": neural_log, "human_readable": human_readable}

    except Exception as e:
        return {
            "neural_log": f"ERROR [System]: {str(e)}",
            "human_readable": "Neural handshake failed. Check your API key or connection."
        }

# ─────────────────────────────────────────────────────────────────────────────
# POD-D: ACTION (Execution Engine)
# ─────────────────────────────────────────────────────────────────────────────

def kill_process(pid):
    """Attempts to terminate a specific system process."""
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.terminate()
        return f"✅ SUCCESS: Process '{name}' (PID: {pid}) terminated."
    except Exception as e:
        return f"❌ FAILED: Unable to kill PID {pid}. {str(e)}"

# ─────────────────────────────────────────────────────────────────────────────
# UI HELPPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def render_gpu_panel(gpu_data):
    """Renders the GPU telemetry panel with cyberpunk styling."""
    if gpu_data and "error" not in gpu_data:
        st.markdown(f"""
        <div class="gpu-metric">
            <div style="color: {GPU_ACCENT}; font-weight: bold; margin-bottom: 10px;">
                🎮 {gpu_data['gpu_name']}
            </div>
            <div style="display: flex; justify-content: space-around; text-align: center;">
                <div>
                    <div style="font-size: 24px; color: #fff;">{gpu_data['temperature']}°C</div>
                    <div style="font-size: 12px; color: {CYAN};">TEMPERATURE</div>
                </div>
                <div>
                    <div style="font-size: 24px; color: #fff;">{gpu_data['vram_used_gb']}/{gpu_data['vram_total_gb']} GB</div>
                    <div style="font-size: 12px; color: {CYAN};">VRAM USAGE</div>
                </div>
                <div>
                    <div style="font-size: 24px; color: #fff;">{gpu_data['power_draw_w']} W</div>
                    <div style="font-size: 12px; color: {CYAN};">POWER DRAW</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning(gpu_data.get("error", "NVIDIA Telemetry Offline"))

# ─────────────────────────────────────────────────────────────────────────────
# MAIN UI APPLICATION
# ─────────────────────────────────────────────────────────────────────────────

def main():
    st.title("💠 APEXVITALS // DIAGNOSTIC")
    st.markdown("---")

    # SIDEBAR: Control Center
    with st.sidebar:
        st.header("⚙️ SYSTEM CONTROL")
        env_key = os.getenv("GEMINI_API_KEY")
        if env_key and "PASTE_YOUR_NEW_KEY_HERE" not in env_key:
            api_key = env_key
            st.success("API Key active from environment.")
        else:
            api_key = st.text_input("GEMINI_API_KEY", type="password", placeholder="Enter AIza...")

        st.info("POD System Architecture v3.0 | APEXVITALS-OS")
        if st.button("RESET ENGINE"):
            st.rerun()

    # TELEMETRY RETRIEVAL
    telemetry = get_system_telemetry()
    gpu_data = get_gpu_telemetry()

    # TOP ROW: System Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{telemetry["cpu_usage"]}%</div><div class="metric-label">CPU LOAD</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{telemetry["ram_usage"]}%</div><div class="metric-label">RAM LOAD</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{telemetry["ram_available_gb"]} GB</div><div class="metric-label">RAM FREE</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # MIDDLE ROW: GPU Panel & Process List
    mid_col1, mid_col2 = st.columns([1, 1])
    with mid_col1:
        st.subheader("🎮 GPU TELEMETRY")
        render_gpu_panel(gpu_data)
    with mid_col2:
        st.subheader("📡 TOP PROCESSES")
        df = pd.DataFrame(telemetry['top_processes'])
        df.columns = ['PID', 'NAME', 'CPU %', 'RAM %']
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # BOTTOM SECTION: Brain Diagnostic
    st.subheader("🧠 POD-C: BRAIN DIAGNOSTIC")
    if st.button("RUN AI NARRATOR", use_container_width=True):
        if api_key:
            with st.status("Performing Neural Correlation...", expanded=True) as status:
                context = prepare_brain_context(telemetry, gpu_data)
                diagnosis = get_ai_diagnosis(api_key, context)
                status.update(label="Handshake Complete", state="complete", expanded=True)

                d_col1, d_col2 = st.columns(2)
                with d_col1:
                    st.markdown(f"""
                    <div class="glass-panel" style="border-color: {CYAN};">
                        <div style="color: {CYAN}; font-weight: bold; margin-bottom: 10px;">⚡ [NEURAL_LOG]</div>
                        <div style="font-family: monospace; font-size: 13px;">{diagnosis['neural_log']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with d_col2:
                    st.markdown(f"""
                    <div class="glass-panel" style="border-color: {STATUS_GREEN};">
                        <div style="color: {STATUS_GREEN}; font-weight: bold; margin-bottom: 10px;">👤 [HUMAN_READABLE]</div>
                        <div>{diagnosis['human_readable']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("API KEY REQUIRED FOR BRAIN MODULE.")

    st.markdown("---")

    # ACTION ENGINE
    st.subheader("⚡ POD-D: ACTION ENGINE")
    with st.expander("MANUAL OVERRIDE: TERMINATE PROCESS"):
        kill_pid = st.number_input("Enter Process ID (PID)", min_value=0, step=1)
        if st.button("EXECUTE KILL COMMAND"):
            if kill_pid > 0:
                result = kill_process(kill_pid)
                st.success(result) if "SUCCESS" in result else st.error(result)

    # Footer
    st.markdown(f"""
    <div style="text-align: right; color: {TEXT_SECONDARY}; font-size: 10px; margin-top: 50px;">
        OS_TIMESTAMP: {telemetry['timestamp']} | CORE_ENGINE: GEMINI-2.0-FLASH | POD_ARCH: v3.0
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
