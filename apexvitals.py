"""
APEXVITALS - AI-Driven System Health Narrator
A production-grade diagnostic tool for ECE portfolios
Architecture: POD-A (Sensor) → POD-B (Context) → POD-C (Brain) → POD-D (Action)
"""

import streamlit as st
import psutil
import json
import pandas as pd
import os
from datetime import datetime
from google import genai
from google.genai import errors
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

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
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_stdio=True)

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
# POD-B: CONTEXT (Data Preparation)
# ─────────────────────────────────────────────────────────────────────────────

def prepare_brain_context(telemetry):
    """Formats raw sensor data into a JSON prompt context for POD-C."""
    context_string = f"""
    SYSTEM_SNAPSHOT:
    - CPU LOAD: {telemetry['cpu_usage']}%
    - RAM LOAD: {telemetry['ram_usage']}%
    - RAM AVAILABLE: {telemetry['ram_available_gb']} GB
    
    TOP_PROCESS_LIST:
    {json.dumps(telemetry['top_processes'], indent=2)}
    
    TIMESTAMP: {telemetry['timestamp']}
    """
    return context_string

# ─────────────────────────────────────────────────────────────────────────────
# POD-C: BRAIN (AI Reasoning)
# ─────────────────────────────────────────────────────────────────────────────

def get_ai_diagnosis(api_key, context):
    """AI reasoning via Gemini 1.5 Flash."""
    # Pre-flight Sanitizer
    sanitized_key = api_key.strip()
    
    if not sanitized_key:
        return "ERROR: API Key Missing. Please provide a valid Gemini API Key in the sidebar."

    try:
        client = genai.Client(api_key=sanitized_key)
        
        prompt = f"""
        Act as a Cyberpunk System Architect. Analyze this telemetry context:
        {context}
        
        Provide a concise 3-sentence diagnostic:
        1. Current health status (CRITICAL, STABLE, or OPTIMAL).
        2. Identify the primary resource bottleneck.
        3. Suggest a specific optimization action.
        
        Keep it professional, technical, and thematic.
        """
        
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text
    
    except errors.ClientError as e:
        if "404" in str(e):
            return "ERROR [404]: Generative AI Service not enabled for this project/region."
        elif "400" in str(e):
            return "ERROR [400]: Invalid API Key format. System Handshake Failed."
        else:
            return f"ERROR [Client]: {str(e)}"
    except Exception as e:
        return f"ERROR [System]: {str(e)}"

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
# MAIN UI APPLICATION
# ─────────────────────────────────────────────────────────────────────────────

def main():
    st.title("💠 APEXVITALS // DIAGNOSTIC")
    st.markdown("---")

    # SIDEBAR: Control Center
    with st.sidebar:
        st.header("⚙️ SYSTEM CONTROL")
        
        # Check environment variable first
        env_key = os.getenv("GEMINI_API_KEY")
        if env_key and "PASTE_YOUR_NEW_KEY_HERE" not in env_key:
            api_key = env_key
            st.success("API Key loaded from environment.")
        else:
            api_key = st.text_input("GEMINI_API_KEY", type="password", placeholder="Enter AIza...")
            
        st.info("POD System Architecture v1.0.4 | APEXVITALS-OS")
        
        if st.button("RESET ENGINE"):
            st.rerun()

    # POD-A: TELEMETRY (Top Row)
    telemetry = get_system_telemetry()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{telemetry['cpu_usage']}%</div>
            <div class="metric-label">CPU UTILIZATION</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{telemetry['ram_usage']}%</div>
            <div class="metric-label">MEMORY LOAD</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{telemetry['ram_available_gb']} GB</div>
            <div class="metric-label">AVAILABLE BUFFER</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # PROCESS LIST & BRAIN ANALYSIS (Middle Section)
    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.subheader("📡 POD-A: SENSOR DATA")
        df = pd.DataFrame(telemetry['top_processes'])
        df.columns = ['PID', 'NAME', 'CPU %', 'RAM %']
        st.dataframe(df, use_container_width=True, hide_index=True)

    with right_col:
        st.subheader("🧠 POD-C: BRAIN DIAGNOSTIC")
        if st.button("RUN AI NARRATOR", use_container_width=True):
            if api_key:
                with st.status("Initializing POD-C Handshake...", expanded=True) as status:
                    st.write("Fetching context from POD-B...")
                    context = prepare_brain_context(telemetry)
                    st.write("Synthesizing reasoning via Gemini Flash...")
                    diagnosis = get_ai_diagnosis(api_key, context)
                    status.update(label="Diagnostic Complete", state="complete", expanded=True)
                    st.markdown(f"**AI FEEDBACK:**\n\n{diagnosis}")
            else:
                st.warning("PLEASE PROVIDE AN API KEY IN THE CONTROL PANEL.")
        else:
            st.markdown("""
            <div class="glass-panel" style="color: #666; text-align: center;">
                Awaiting neural uplink... click "RUN AI NARRATOR" to begin analysis.
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # POD-D: ACTION ENGINE (Bottom Section)
    st.subheader("⚡ POD-D: ACTION ENGINE")
    with st.expander("MANUAL OVERRIDE: TERMINATE PROCESS"):
        kill_pid = st.number_input("Enter Process ID (PID)", min_value=0, step=1)
        if st.button("EXECUTE KILL COMMAND", type="secondary"):
            if kill_pid > 0:
                result = kill_process(kill_pid)
                if "SUCCESS" in result:
                    st.success(result)
                else:
                    st.error(result)
            else:
                st.warning("ENTER A VALID PID.")

    # Footer
    st.markdown(f"""
    <div style="text-align: right; color: {TEXT_SECONDARY}; font-size: 10px; margin-top: 50px;">
        OS_TIMESTAMP: {telemetry['timestamp']} | CORE_ENGINE: GEMINI-1.5-FLASH-V1
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
