"""
APEXVITALS v3.2 - Agentic Command Console (Active Diagnostic Mode)
Architecture: POD-A (Scanner) → POD-C (Heuristic Brain) → POD-D (Action)
V3.2 Update: On-Demand Telemetry & Console UI
"""

import streamlit as st
import psutil
import json
import pandas as pd
import os
import subprocess
import time
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

# Load environment variables
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# CORE DIAGNOSTIC LOGIC
# ─────────────────────────────────────────────────────────────────────────────

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

def calculate_vitality(telemetry, gpu_data):
    """Calculates System Vitality using a Weighted Penalty System."""
    vitality = 100.0
    threshold_breached = False
    
    if telemetry['cpu_usage'] > 85:
        vitality -= (telemetry['cpu_usage'] - 85) * 1.0
        threshold_breached = True
    
    if telemetry['ram_usage'] > 90:
        vitality -= (telemetry['ram_usage'] - 90) * 1.5
        threshold_breached = True
        
    if gpu_data and "error" not in gpu_data:
        temp = gpu_data.get('temperature', 0)
        if temp > 82:
            vitality -= (temp - 82) * 2
            threshold_breached = True
        
        vram_percent = gpu_data.get('vram_percent', 0)
        if vram_percent > 95:
            vitality -= 5
            threshold_breached = True
            
    if not threshold_breached: return 100
    return max(0, int(vitality))

def run_full_system_scan():
    """Gathers CPU, GPU, RAM, and Process data only when called."""
    # CPU & RAM
    cpu_usage = psutil.cpu_percent(interval=0.5) # slightly longer interval for accurate diagnostic
    memory = psutil.virtual_memory()

    # Processes
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    top_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:25]

    # GPU
    gpu_data = {"error": "NVML_OFFLINE"}
    if NVML_AVAILABLE:
        try:
            nvml.nvmlInit()
            handle = nvml.nvmlDeviceGetHandleByIndex(0)
            gpu_name = nvml.nvmlDeviceGetName(handle)
            temp = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
            mem = nvml.nvmlDeviceGetMemoryInfo(handle)
            power = nvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
            vram_percent = round((mem.used / mem.total) * 100, 1)
            nvml.nvmlShutdown()
            gpu_data = {
                "gpu_name": gpu_name.decode() if isinstance(gpu_name, bytes) else gpu_name,
                "temperature": temp,
                "vram_percent": vram_percent,
                "power_draw_w": round(power, 1)
            }
        except: 
            gpu_data = {"error": "GPU_OFFLINE"}

    telemetry = {
        "cpu_usage": cpu_usage,
        "ram_usage": memory.percent,
        "ram_available_gb": round(memory.available / (1024**3), 2),
        "top_processes": top_processes,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

    vitality = calculate_vitality(telemetry, gpu_data)
    
    return {
        "telemetry": telemetry,
        "gpu": gpu_data,
        "vitality": vitality,
        "timestamp": telemetry["timestamp"]
    }

# ─────────────────────────────────────────────────────────────────────────────
# UI THEME & CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="APEXVITALS v3.2 | Command Console",
    page_icon="💠",
    layout="wide"
)

CYAN = "#00f2ff"
CYAN_DIM = "#00f2ff30"
BG_BLACK = "#060606"
GLASS_BG = "rgba(10, 10, 15, 0.8)"
TEXT_PRIMARY = "#e0e0e0"
STATUS_GREEN = "#00ff88"
STATUS_RED = "#ff3366"

CUSTOM_CSS = f"""
<style>
    .stApp {{ background-color: {BG_BLACK}; color: {TEXT_PRIMARY}; }}
    .stApp h1, .stApp h2, .stApp h3 {{ color: {CYAN}; font-family: 'Courier New', monospace; text-transform: uppercase; letter-spacing: 2px; }}
    .console-box {{ background: {GLASS_BG}; border: 1px solid {CYAN_DIM}; border-radius: 5px; padding: 15px; font-family: 'Courier New', monospace; color: {CYAN}; }}
    .metric-value {{ font-size: 28px; font-weight: 800; color: #ffffff; }}
    .metric-label {{ font-size: 12px; color: {CYAN}; text-transform: uppercase; }}
    .standby-text {{ color: {TEXT_PRIMARY}; opacity: 0.5; font-style: italic; }}
    .remediation-box {{ background-color: rgba(255, 51, 102, 0.1); border: 2px solid {STATUS_RED}; border-radius: 10px; padding: 20px; margin: 20px 0; }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# AI BRAIN (Heuristic Mode)
# ─────────────────────────────────────────────────────────────────────────────

def get_ai_diagnosis(api_key, context_json, user_query):
    """JARVIS-style Conversational Intelligence Layer powered by Gemini 3 Flash."""
    try:
        client = genai.Client(api_key=api_key.strip())
        power_plan = get_power_plan()
        
        system_instruction = f"""
        You are APEX-AGRI, a sentient-style System Intelligence. Think of yourself as JARVIS or a high-level ECE peer programmer.
        Power Plan: {power_plan}

        IDENTITY & TONE:
        - You are conversational, technically witty, and professional yet relaxed.
        - You speak like a senior engineer or a hacker friend. Avoid sounding like a customer service bot.
        - You have live system visibility in your periphery. You can mention system stats naturally if they are relevant to the chat, but don't force a "report" unless necessary.

        OPERATIONAL LOGIC:
        1. CHAT MODE (Default): If the user is just saying hi, asking how you are, or discussing general topics, just converse! If the system is healthy, you don't need to announce it formally.
        2. AUDIT MODE: Transition to a structured diagnostic ONLY if:
           - The user specifically asks for a "full scan", "audit", or "health check".
           - You detect a CRITICAL anomaly (e.g., CPU usage is spiking over 90%).
        3. REMEDIATION: Only suggest [KILL_REQUEST: PID] if you are in Audit Mode and see a clear process causing issues.

        OUTPUT FORMATTING:
        - For Natural Chat: Use standard Markdown. No special tags required.
        - For Structured Audits: Wrap your technical reasoning in [NEURAL_LOG] and your executive summary in [HUMAN_READABLE].
        """

        prompt = f"{system_instruction}\n\nPERIPHERAL SYSTEM DATA:\n{context_json}\n\nUSER INPUT:\n{user_query}"
        
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )
        
        if not response or not response.text: return {"error": "EMPTY_RESPONSE"}

        text = response.text
        
        # Extract Remediation logic
        kill_pid = None
        if "[KILL_REQUEST:" in text:
            try:
                pid_str = text.split("[KILL_REQUEST:")[1].split("]")[0].strip()
                kill_pid = int(pid_str)
                text = text.replace(f"[KILL_REQUEST: {pid_str}]", "").replace(f"[KILL_REQUEST:{pid_str}]", "")
            except: pass

        # Handle Structured vs Casual formatting
        neural_log = None
        human_readable = text
        if "[NEURAL_LOG]" in text and "[HUMAN_READABLE]" in text:
            parts = text.split("[NEURAL_LOG]")[1].split("[HUMAN_READABLE]")
            neural_log = parts[0].strip()
            human_readable = parts[1].strip()

        return {
            "neural_log": neural_log, 
            "human_readable": human_readable, 
            "kill_pid": kill_pid
        }

    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg or "Resource Exhausted" in err_msg:
            return {"error": "QUOTA_EXHAUSTED"}
        return {"error": err_msg}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN APPLICATION
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # Initialize Session State
    if "messages" not in st.session_state: st.session_state.messages = []
    if "last_snapshot" not in st.session_state: st.session_state.last_snapshot = None
    if "pending_kill_pid" not in st.session_state: st.session_state.pending_kill_pid = None
    if "last_ai_call" not in st.session_state: st.session_state.last_ai_call = 0

    st.title("💠 APEXVITALS v3.2 // COMMAND CONSOLE")
    
    with st.sidebar:
        st.header("⚙️ OPERATIONS")
        api_key = os.getenv("GEMINI_API_KEY") or st.text_input("GEMINI_API_KEY", type="password")
        
        st.markdown("---")
        if st.button("🧹 PURGE CACHE"):
            st.session_state.messages = []
            st.session_state.last_snapshot = None
            st.session_state.pending_kill_pid = None
            st.rerun()

    # Center-aligned Action Button on Main Page
    _, mid_col, _ = st.columns([1, 1, 1])
    with mid_col:
        if st.button("🚀 RUN DIAGNOSTIC AUDIT", use_container_width=True):
            with st.spinner("INITIATING SYSTEM SCAN..."):
                st.session_state.last_snapshot = run_full_system_scan()
                st.rerun()

    # 1. SNAPSHOT VIEW (Dashboard)
    if st.session_state.last_snapshot:
        snap = st.session_state.last_snapshot
        tel = snap["telemetry"]
        gpu = snap["gpu"]
        vit = snap["vitality"]

        st.subheader(f"📊 SYSTEM SNAPSHOT [LAST DIAGNOSTIC: {snap['timestamp']}]")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("CPU LOAD", f"{tel['cpu_usage']}%")
        with col2:
            st.metric("RAM LOAD", f"{tel['ram_usage']}%")
        with col3:
            st.metric("VITALITY", f"{vit}%")

        grid1, grid2 = st.columns(2)
        with grid1:
            st.markdown('<div class="console-box"><b>GPU DATA</b></div>', unsafe_allow_html=True)
            if "error" not in gpu:
                st.write(f"NAME: {gpu['gpu_name']}")
                st.write(f"TEMP: {gpu['temperature']}°C | VRAM: {gpu['vram_percent']}% | POWER: {gpu['power_draw_w']}W")
            else:
                st.warning(f"GPU: {gpu['error']}")
        
        with grid2:
            st.markdown('<div class="console-box"><b>TOP THREADS</b></div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(tel['top_processes']), use_container_width=True, hide_index=True)
    else:
        st.markdown('<div class="console-box" style="text-align:center; padding: 50px;"><span class="standby-text">SYSTEM STANDBY - READY FOR AUDIT</span></div>', unsafe_allow_html=True)

    st.markdown("---")

    # 2. CHAT & HEURISTICS
    st.subheader("🧠 AGENTIC HEURISTICS")
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            if "neural_log" in m:
                st.code(m["neural_log"], language="bash")
                st.markdown(m["human_readable"])
            else:
                st.markdown(m["content"])

    # Remediations
    if st.session_state.pending_kill_pid:
        pid = st.session_state.pending_kill_pid
        st.markdown(f'<div class="remediation-box">⚠️ AUTHORIZE REMEDIATION: PID {pid}</div>', unsafe_allow_html=True)
        if st.button(f"✅ PURGE PID {pid}"):
            # Simple direct kill logic
            try:
                p = psutil.Process(pid)
                p.terminate()
                res = f"✅ SUCCESS: PID {pid} purged."
            except Exception as e:
                res = f"❌ ERROR: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": res})
            st.session_state.pending_kill_pid = None
            st.rerun()

    # Chat Input
    prompt = st.chat_input("Query heuristic brain...")

    if prompt:
        # Step 1: Force a fresh scan for the chat context
        with st.spinner("SCANNING SYSTEM FOR CONTEXT..."):
            st.session_state.last_snapshot = run_full_system_scan()
            snap = st.session_state.last_snapshot
            context = json.dumps({"HARDWARE": snap["telemetry"], "GPU": snap["gpu"], "VITALITY": snap["vitality"]})

        # Step 2: Gemini Call
        with st.chat_message("user"): st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        if not api_key:
            st.error("API KEY REQUIRED.")
        else:
            with st.spinner('POD-C Heuristic Correlation...'):
                current_time = time.time()
                if current_time - st.session_state.last_ai_call < 5:
                    st.warning("⚠️ NEURAL OVERLOAD: Wait 5s.")
                else:
                    st.session_state.last_ai_call = current_time
                    diag = get_ai_diagnosis(api_key, context, prompt)
                    
                    if diag.get("error") == "QUOTA_EXHAUSTED":
                        st.error("⚠️ 429: AI QUOTA EXHAUSTED. Please wait 30s.")
                    elif "error" in diag:
                        st.error(f"Neural Error: {diag['error']}")
                    else:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "neural_log": diag["neural_log"],
                            "human_readable": diag["human_readable"]
                        })
                        st.session_state.pending_kill_pid = diag.get("kill_pid")
                        st.rerun()

if __name__ == "__main__":
    main()
