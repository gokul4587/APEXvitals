"""
APEXVITALS - AI-Driven System Health Narrator
A production-grade diagnostic tool for ECE portfolios
Architecture: POD-A (Sensor) → POD-B (Context) → POD-C (Brain) → POD-D (Action)
"""

import streamlit as st
import psutil
import json
from datetime import datetime
from google import genai
from google.genai import errors

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION & CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="APEXVITALS | System Diagnostic Engine",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Cyberpunk Theme
CYAN = "#00f2ff"
CYAN_DIM = "#00f2ff40"
BG_BLACK = "#060606"
GLASS_BG = "#0a0a0fcc"
TEXT_PRIMARY = "#e0e0e0"
TEXT_SECONDARY = "#888888"
STATUS_GREEN = "#00ff88"
STATUS_YELLOW = "#ffaa00"
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
    }}
    .stMetric {{
        background: linear-gradient(135deg, {GLASS_BG} 0%, #00000080 100%);
        border: 1px solid {CYAN_DIM};
        border-radius: 8px;
        padding: 16px;
    }}
    .stMetricLabel {{
        color: {CYAN} !important;
        font-size: 14px;
        font-weight: 600;
    }}
    .stMetricValue {{
        color: #ffffff !important;
        font-size: 28px;
        font-weight: 700;
    }}
    .glass-container {{
        background: linear-gradient(135deg, {GLASS_BG} 0%, #00000080 100%);
        border: 1px solid {CYAN_DIM};
        border-radius: 12px;
        padding: 24px;
        margin: 16px 0;
        backdrop-filter: blur(10px);
    }}
    .status-indicator {{
        font-size: 32px;
        font-weight: bold;
        padding: 8px 16px;
        border-radius: 6px;
        display: inline-block;
    }}
    .status-green {{ background-color: {STATUS_GREEN}20; color: {STATUS_GREEN}; border: 1px solid {STATUS_GREEN}; }}
    .status-yellow {{ background-color: {STATUS_YELLOW}20; color: {STATUS_YELLOW}; border: 1px solid {STATUS_YELLOW}; }}
    .status-red {{ background-color: {STATUS_RED}20; color: {STATUS_RED}; border: 1px solid {STATUS_RED}; }}
    .stDataFrame {{
        border: 1px solid {CYAN_DIM};
        border-radius: 8px;
    }}
    .stDataFrame th {{
        background-color: {CYAN_DIM};
        color: {CYAN};
        font-weight: 600;
    }}
    .stDataFrame td {{
        color: {TEXT_PRIMARY};
    }}
    .stButton>button {{
        background: transparent;
        color: {CYAN};
        border: 2px solid {CYAN};
        border-radius: 6px;
        padding: 12px 32px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        background: {CYAN};
        color: #000000;
        box-shadow: 0 0 20px {CYAN_DIM};
    }}
    .stTextInput>div>div>input, .stNumberInput>div>div>input {{
        background-color: #00000040;
        border: 1px solid {CYAN_DIM};
        color: {TEXT_PRIMARY};
    }}
    .stSidebar {{
        background-color: #020202;
        border-right: 1px solid {CYAN_DIM};
    }}
    .warning-box {{
        background-color: {STATUS_YELLOW}10;
        border-left: 4px solid {STATUS_YELLOW};
        padding: 16px;
        margin: 16px 0;
        border-radius: 4px;
    }}
    .ai-output {{
        font-family: 'Consolas', monospace;
        line-height: 1.8;
        color: {TEXT_PRIMARY};
    }}
    div[data-testid="stMetricValue"] {{
        font-family: 'Consolas', monospace;
    }}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# POD-A: SENSOR MODULE - Hardware Telemetry Acquisition
# ─────────────────────────────────────────────────────────────────────────────

def fetch_cpu_metrics():
    """Acquire CPU load percentage and frequency telemetry."""
    cpu_percent = psutil.cpu_percent(interval=0.5)
    freq = psutil.cpu_freq()
    current_ghz = freq.current / 1000 if freq else 0
    max_ghz = freq.max / 1000 if freq else 0
    return {
        "load_percent": cpu_percent,
        "frequency_ghz": round(current_ghz, 2),
        "max_frequency_ghz": round(max_ghz, 2),
        "cores_physical": psutil.cpu_count(logical=False),
        "cores_logical": psutil.cpu_count(logical=True)
    }


def fetch_memory_metrics():
    """Acquire physical RAM and swap memory telemetry."""
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "ram_total_gb": round(ram.total / (1024**3), 2),
        "ram_used_gb": round(ram.used / (1024**3), 2),
        "ram_available_gb": round(ram.available / (1024**3), 2),
        "ram_percent": ram.percent,
        "swap_total_gb": round(swap.total / (1024**3), 2),
        "swap_used_gb": round(swap.used / (1024**3), 2),
        "swap_percent": swap.percent
    }


def fetch_disk_metrics():
    """Acquire disk I/O statistics."""
    disk_io = psutil.disk_io_counters()
    disk_usage = psutil.disk_usage('C:')
    return {
        "disk_read_mb": round(disk_io.read_bytes / (1024**2), 2) if disk_io else 0,
        "disk_write_mb": round(disk_io.write_bytes / (1024**2), 2) if disk_io else 0,
        "disk_total_gb": round(disk_usage.total / (1024**3), 2),
        "disk_used_gb": round(disk_usage.used / (1024**3), 2),
        "disk_percent": disk_usage.percent
    }


def fetch_top_processes(n=5):
    """Acquire top N processes by CPU usage."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
        try:
            pinfo = proc.info
            mem_mb = pinfo['memory_info'].rss / (1024**2) if pinfo.get('memory_info') else 0
            processes.append({
                "pid": pinfo['pid'],
                "name": pinfo['name'] or "Unknown",
                "cpu_percent": round(pinfo.get('cpu_percent', 0), 1),
                "memory_mb": round(mem_mb, 1),
                "memory_percent": round(pinfo.get('memory_percent', 0), 1)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    return processes[:n]


def pod_a_sensor_probe():
    """
    POD-A: Primary Sensor Array
    Aggregates all hardware telemetry into raw data structures.
    """
    return {
        "cpu": fetch_cpu_metrics(),
        "memory": fetch_memory_metrics(),
        "disk": fetch_disk_metrics(),
        "top_processes": fetch_top_processes(5),
        "timestamp": datetime.now().isoformat(),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
    }


# ─────────────────────────────────────────────────────────────────────────────
# POD-B: CONTEXT MODULE - State Object Serialization
# ─────────────────────────────────────────────────────────────────────────────

def pod_b_contextualize(raw_data):
    """
    POD-B: Context Engine
    Transforms raw sensor data into LLM-consumable JSON state object.
    """
    vitals_snapshot = {
        "system_state": {
            "cpu_load": raw_data["cpu"]["load_percent"],
            "cpu_frequency_ghz": raw_data["cpu"]["frequency_ghz"],
            "cpu_max_frequency_ghz": raw_data["cpu"]["max_frequency_ghz"],
            "cpu_core_count": raw_data["cpu"]["cores_logical"],
            "ram_usage_percent": raw_data["memory"]["ram_percent"],
            "ram_used_gb": raw_data["memory"]["ram_used_gb"],
            "ram_total_gb": raw_data["memory"]["ram_total_gb"],
            "swap_usage_percent": raw_data["memory"]["swap_percent"],
            "disk_usage_percent": raw_data["disk"]["disk_percent"]
        },
        "process_anomalies": [
            {
                "pid": p["pid"],
                "name": p["name"],
                "cpu_load": p["cpu_percent"],
                "memory_mb": p["memory_mb"]
            }
            for p in raw_data["top_processes"]
            if p["cpu_percent"] > 10 or p["memory_mb"] > 500
        ],
        "diagnostic_flags": {
            "thermal_throttle_risk": raw_data["cpu"]["frequency_ghz"] < raw_data["cpu"]["max_frequency_ghz"] * 0.8,
            "memory_pressure": raw_data["memory"]["ram_percent"] > 80,
            "swap_active": raw_data["memory"]["swap_percent"] > 5,
            "high_cpu_process": any(p["cpu_percent"] > 50 for p in raw_data["top_processes"]),
            "context_switching_likely": raw_data["cpu"]["load_percent"] > 70 and len(raw_data["top_processes"]) > 3
        },
        "metadata": {
            "scan_timestamp": raw_data["timestamp"],
            "system_uptime": raw_data["boot_time"]
        }
    }
    return vitals_snapshot


# ─────────────────────────────────────────────────────────────────────────────
# POD-C: BRAIN MODULE - Gemini AI Analysis Engine
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a Senior Hardware Diagnostic Engineer AI specializing in ECE system analysis.
Your role is to analyze hardware telemetry and provide actionable engineering insights.

ANALYSIS FRAMEWORK:
1. Thermal Throttling: Compare current CPU frequency against max. If <80%, flag cooling issues.
2. Memory Pressure: RAM >80% indicates allocation problems or leaks.
3. Context Switching: High CPU load + multiple processes = excessive context switches.
4. Swap Activity: Active swap indicates memory starvation.
5. Process Anomalies: Identify runaway processes consuming disproportionate resources.

OUTPUT FORMAT (STRICT JSON):
{{
    "status": "GREEN" | "YELLOW" | "RED",
    "analysis": "<exactly 2 sentences of technical diagnosis>",
    "actionable_steps": ["<step 1>", "<step 2>", "<step 3>"],
    "diagnosis": {
        "thermal_status": "<normal/warning/critical>",
        "memory_status": "<normal/pressure/critical>",
        "cpu_status": "<normal/loaded/overloaded>"
    }
}}

Be concise, technical, and prescriptive. No fluff.
"""


def get_client(api_key):
    """Initialize modern GenAI client with sanitized key."""
    clean_key = api_key.strip().replace(' ', '')
    return genai.Client(api_key=clean_key)


def get_available_models(api_key):
    """Discover available models from the API."""
    try:
        client = get_client(api_key)
        models = []
        for m in client.models.list():
            models.append(m.name)
        return models
    except Exception as e:
        return [f"Error: {str(e)}"]


def validate_api_key(api_key):
    """
    Pre-flight API key validation.
    Returns (is_valid, error_message, available_models).
    """
    try:
        client = get_client(api_key)
        # Try gemini-1.5-flash
        try:
            test_response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents="health check"
            )
            if test_response:
                return True, None, "gemini-1.5-flash"
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                # Fallback to gemini-1.5-pro
                try:
                    test_response = client.models.generate_content(
                        model='gemini-1.5-pro',
                        contents="health check"
                    )
                    if test_response:
                        return True, None, "gemini-1.5-pro"
                except:
                    pass
            raise e # Reraise for main handler if not 404
            
        return False, "No suitable model found", None
    except Exception as e:
        error_str = str(e)
        if "400" in error_str or "API_KEY_INVALID" in error_str:
            return False, "INVALID_KEY", None
        elif "403" in error_str:
            return False, "API_DISABLED", None
        else:
            return False, f"CONNECTION_ERROR: {error_str}", None


def pod_c_brain_analyze(vitals_snapshot, api_key):
    """
    POD-C: Neural Analysis Engine
    Sends contextualized data to Gemini 1.5 Flash for expert diagnosis.
    """
    client = get_client(api_key)

    # Model discovery and fallback logic
    model_name = 'gemini-1.5-flash'
    model_error = None

    analysis_prompt = f"""{SYSTEM_PROMPT}

Analyze this hardware telemetry:
{json.dumps(vitals_snapshot, indent=2)}

Return JSON with: status (GREEN/YELLOW/RED), analysis (2 sentences), actionable_steps (3 items), diagnosis object."""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=analysis_prompt
        )
        response_text = response.text.strip()

        # Extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        try:
            result = json.loads(response_text)
            result['_model_used'] = model_name
            return result
        except json.JSONDecodeError:
            return {
                "status": "YELLOW",
                "analysis": "AI response parsing failed.",
                "actionable_steps": ["Check API connectivity", "Retry the scan", "Review raw telemetry"],
                "diagnosis": {"thermal_status": "unknown", "memory_status": "unknown", "cpu_status": "unknown"},
                "_model_used": model_name
            }
            
    except errors.ClientError as e:
        if e.code == 400:
            return {
                "status": "RED",
                "analysis": "DECRYPT_FAIL: API key decryption or validation failed.",
                "actionable_steps": [
                    "Check API key permissions in Google AI Studio",
                    "Ensure the key is active and not restricted",
                    "Verify billing/quota status"
                ],
                "diagnosis": {"thermal_status": "critical", "memory_status": "unknown", "cpu_status": "unknown"},
                "_error_detail": "API_KEY_INVALID_OR_DECRYPT_FAIL"
            }
        raise e
    except Exception as e:
        return {
            "status": "RED",
            "analysis": f"Neural Link Error: {str(e)}",
            "actionable_steps": ["Verify network integrity", "Check API dashboard", "Retry synchronization"],
            "diagnosis": {"thermal_status": "unknown", "memory_status": "unknown", "cpu_status": "unknown"},
            "_model_used": model_name
        }


# ─────────────────────────────────────────────────────────────────────────────
# POD-D: ACTION MODULE - Process Termination Agent
# ─────────────────────────────────────────────────────────────────────────────

def pod_d_terminate_process(pid):
    """
    POD-D: Action Agent
    Safely terminates a process by PID with error handling.
    """
    try:
        proc = psutil.Process(pid)
        proc_name = proc.name()

        # Safety check: prevent termination of critical system processes
        critical_processes = ['system', 'smss.exe', 'csrss.exe', 'wininit.exe',
                             'services.exe', 'lsass.exe', 'winlogon.exe']
        if proc_name.lower() in critical_processes:
            return {
                "success": False,
                "message": f"CRITICAL: Cannot terminate system process '{proc_name}'",
                "pid": pid
            }

        proc.terminate()
        proc.wait(timeout=3)
        return {
            "success": True,
            "message": f"Process '{proc_name}' (PID: {pid}) terminated successfully",
            "pid": pid,
            "process_name": proc_name
        }

    except psutil.NoSuchProcess:
        return {"success": False, "message": f"Process {pid} does not exist", "pid": pid}
    except psutil.AccessDenied:
        return {"success": False, "message": f"Access denied for PID {pid}. Run as administrator.", "pid": pid}
    except psutil.TimeoutExpired:
        return {"success": False, "message": f"Process {pid} did not terminate gracefully", "pid": pid}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}", "pid": pid}


# ─────────────────────────────────────────────────────────────────────────────
# UI LAYER: Streamlit Dashboard
# ─────────────────────────────────────────────────────────────────────────────

def render_header():
    """Render the APEXVITALS header with cyberpunk styling."""
    st.markdown("""
    <div style="text-align: center; padding: 20px 0; border-bottom: 1px solid #00f2ff40;">
        <h1 style="margin: 0; font-size: 48px; letter-spacing: 8px;">APEXVITALS</h1>
        <p style="color: #00f2ff; margin: 8px 0; font-size: 14px; letter-spacing: 3px;">
            AI-DRIVEN SYSTEM HEALTH NARRATOR
        </p>
        <p style="color: #666; font-size: 12px;">TELEMETRY → REASONING → ACTION</p>
    </div>
    """, unsafe_allow_html=True)


def render_permission_gate():
    """Render the security authorization screen."""
    st.markdown("""
    <div class="glass-container" style="text-align: center; padding: 48px;">
        <h2 style="color: #00f2ff;">🔒 SECURE AUTHORIZATION REQUIRED</h2>
        <p style="color: #aaa; line-height: 1.8;">
            APEXVITALS will probe hardware sensors and execute system-level diagnostics.<br>
            This requires elevated process access and AI-assisted analysis.
        </p>
        <div class="warning-box" style="display: inline-block; text-align: left; margin-top: 24px;">
            <strong>⚠ SYSTEM ACCESS SCOPE:</strong><br>
            • CPU frequency and load telemetry<br>
            • Memory allocation mapping<br>
            • Process enumeration and termination<br>
            • Disk I/O statistics
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔷 INITIALIZE APEX SCAN", key="init_scan_btn", type="primary", use_container_width=True):
            st.session_state.scan_initialized = True
            st.rerun()


def render_vitals_dashboard(raw_data, vitals_snapshot):
    """Render the main vitals dashboard with metrics."""

    # CPU Metrics Row
    st.markdown("### ⚡ CPU TELEMETRY")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="CPU LOAD",
            value=f"{raw_data['cpu']['load_percent']}%",
            delta=f"{raw_data['cpu']['load_percent'] - 50:+.1f}%" if raw_data['cpu']['load_percent'] > 50 else None
        )

    with col2:
        st.metric(
            label="FREQUENCY",
            value=f"{raw_data['cpu']['frequency_ghz']} GHz",
            help=f"Max: {raw_data['cpu']['max_frequency_ghz']} GHz"
        )

    with col3:
        st.metric(
            label="PHYSICAL CORES",
            value=raw_data['cpu']['cores_physical'],
            delta=f"+{raw_data['cpu']['cores_logical'] - raw_data['cpu']['cores_physical']} logical"
        )

    with col4:
        throttle_status = "⚠ THROTTLED" if vitals_snapshot["diagnostic_flags"]["thermal_throttle_risk"] else "✓ NORMAL"
        st.metric(
            label="THERMAL STATUS",
            value=throttle_status.split()[0],
            delta=throttle_status.split()[1] if len(throttle_status.split()) > 1 else None
        )

    # Memory Metrics Row
    st.markdown("### 🧠 MEMORY SUBSYSTEM")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="RAM USAGE",
            value=f"{raw_data['memory']['ram_percent']}%",
            delta=f"{raw_data['memory']['ram_used_gb']}/{raw_data['memory']['ram_total_gb']} GB"
        )

    with col2:
        pressure_status = "⚠ PRESSURE" if vitals_snapshot["diagnostic_flags"]["memory_pressure"] else "✓ STABLE"
        st.metric(
            label="MEMORY STATUS",
            value=pressure_status.split()[0]
        )

    with col3:
        st.metric(
            label="SWAP USAGE",
            value=f"{raw_data['memory']['swap_percent']}%",
            delta=f"{raw_data['memory']['swap_used_gb']} GB used"
        )

    with col4:
        st.metric(
            label="DISK USAGE",
            value=f"{raw_data['disk']['disk_percent']}%",
            delta=f"{raw_data['disk']['disk_used_gb']}/{raw_data['disk']['disk_total_gb']} GB"
        )

    # Top Processes Table
    st.markdown("### 📊 TOP PROCESSES BY CPU")
    st.dataframe(
        raw_data["top_processes"],
        use_container_width=True,
        hide_index=True,
        column_config={
            "pid": st.column_config.NumberColumn("PID", format="%d"),
            "name": st.column_config.TextColumn("PROCESS"),
            "cpu_percent": st.column_config.NumberColumn("CPU %", format="%.1f"),
            "memory_mb": st.column_config.NumberColumn("MEMORY (MB)", format="%.1f"),
            "memory_percent": st.column_config.NumberColumn("MEM %", format="%.1f")
        }
    )


def render_ai_report(ai_report):
    """Render the AI diagnostic report in a glassmorphism container."""
    status_colors = {
        "GREEN": STATUS_GREEN,
        "YELLOW": STATUS_YELLOW,
        "RED": STATUS_RED
    }
    status_emojis = {
        "GREEN": "🟢",
        "YELLOW": "🟡",
        "RED": "🔴"
    }

    status = ai_report.get("status", "YELLOW").upper()
    status_color = status_colors.get(status, STATUS_YELLOW)
    status_emoji = status_emojis.get(status, "🟡")

    st.markdown(f"""
    <div class="glass-container" style="border-color: {status_color};">
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 20px;">
            <span class="status-indicator status-{status.lower()}" style="font-size: 24px;">
                {status_emoji} SYSTEM STATUS: {status}
            </span>
        </div>

        <h3 style="color: {CYAN}; margin-bottom: 12px;">🔬 AI DIAGNOSTIC ANALYSIS</h3>
        <p class="ai-output" style="font-size: 16px; color: #fff;">
            {ai_report.get("analysis", "Analysis unavailable.")}
        </p>

        <h3 style="color: {CYAN}; margin: 24px 0 12px 0;">⚙️ DIAGNOSTIC DETAILS</h3>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
            <div style="background: #00000040; padding: 12px; border-radius: 6px; border-left: 3px solid {status_color};">
                <span style="color: #888; font-size: 12px;">THERMAL</span><br>
                <span style="color: #fff; font-weight: 600;">{ai_report.get("diagnosis", {}).get("thermal_status", "N/A").upper()}</span>
            </div>
            <div style="background: #00000040; padding: 12px; border-radius: 6px; border-left: 3px solid {status_color};">
                <span style="color: #888; font-size: 12px;">MEMORY</span><br>
                <span style="color: #fff; font-weight: 600;">{ai_report.get("diagnosis", {}).get("memory_status", "N/A").upper()}</span>
            </div>
            <div style="background: #00000040; padding: 12px; border-radius: 6px; border-left: 3px solid {status_color};">
                <span style="color: #888; font-size: 12px;">CPU</span><br>
                <span style="color: #fff; font-weight: 600;">{ai_report.get("diagnosis", {}).get("cpu_status", "N/A").upper()}</span>
            </div>
        </div>

        <h3 style="color: {CYAN}; margin: 24px 0 12px 0;">📋 ACTIONABLE ENGINEERING STEPS</h3>
        <ol style="color: {TEXT_PRIMARY}; line-height: 2;">
            {''.join(f'<li style="padding: 8px 0; border-bottom: 1px solid #333;">{step}</li>' for step in ai_report.get("actionable_steps", []))}
        </ol>
    </div>
    """, unsafe_allow_html=True)


def render_action_agent():
    """Render the process termination interface."""
    st.markdown("""
    <div class="glass-container" style="border-color: #ff336640;">
        <h2 style="color: #ff3366;">⚠ PROCESS TERMINATION AGENT</h2>
        <p style="color: #888; margin-bottom: 20px;">
            Enter a Process ID (PID) to terminate. Exercise caution - this action is irreversible.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        pid_input = st.number_input(
            "TARGET PID",
            min_value=1,
            max_value=99999,
            step=1,
            key="pid_input",
            placeholder="Enter PID from table above"
        )

    with col2:
        terminate_btn = st.button(
            "💀 TERMINATE PROCESS",
            key="terminate_btn",
            use_container_width=True
        )

    return pid_input, terminate_btn


def render_sidebar():
    """Render the sidebar with API key input and verification."""
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px 0;">
            <h2 style="color: {CYAN}; font-size: 20px;">⚙ CONFIGURATION</h2>
        </div>
        """, unsafe_allow_html=True)

        api_key = st.text_input(
            "GEMINI API KEY",
            type="password",
            placeholder="Enter your API key",
            help="Get your API key from Google AI Studio",
            key="api_key_input"
        )

        # Debug: Show key fingerprint (first 4 + last 4 chars)
        if api_key and len(api_key) >= 8:
            key_preview = f"{api_key[:4]}...{api_key[-4:]}"
            st.caption(f"Key: `{key_preview}`")

        # Key verification section
        st.markdown("---")
        st.markdown("### 🔑 KEY STATUS")

        if api_key:
            if st.button("🔍 VERIFY KEY", key="verify_key_btn", type="primary", use_container_width=True):
                with st.spinner("Checking API..."):
                    is_valid, error, model_used = validate_api_key(api_key)
                    st.session_state.key_validated = True
                    st.session_state.key_error = error
                    st.session_state.key_valid = is_valid
                    st.session_state.model_used = model_used
                    st.rerun()

            # Status display after verification
            if st.session_state.get("key_validated"):
                if st.session_state.get("key_error") == "INVALID_KEY":
                    st.error("❌ INVALID KEY")
                    st.caption("Check at aistudio.google.com")
                elif st.session_state.get("key_error"):
                    st.error(f"❌ {st.session_state.key_error}")
                elif st.session_state.get("key_valid"):
                    st.success(f"🟢 VALID ({st.session_state.model_used})")

            # Show available models for debugging
            if st.session_state.get("key_validated") and st.session_state.get("key_error"):
                st.markdown("---")
                st.markdown("**Available Models:**")
                try:
                    client = get_client(api_key)
                    models = [m.name for m in client.models.list()]
                    for m in models:
                        st.caption(m)
                except Exception as e:
                    st.caption(f"Could not list models: {e}")
        else:
            st.caption("Enter API key above")

        st.markdown("---")
        st.markdown("""
        ### ABOUT APEXVITALS

        **Architecture:**
        - POD-A: Hardware Sensor
        - POD-B: Context Engine
        - POD-C: AI Brain (Gemini)
        - POD-D: Action Agent

        **Version:** 1.1.0 (V1 SDK)

        **For:** ECE Portfolio
        """)

        return api_key


# ─────────────────────────────────────────────────────────────────────────────
# MAIN APPLICATION FLOW
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """Main application entry point."""

    # Initialize session state
    if "scan_initialized" not in st.session_state:
        st.session_state.scan_initialized = False
    if "raw_data" not in st.session_state:
        st.session_state.raw_data = None
    if "vitals_snapshot" not in st.session_state:
        st.session_state.vitals_snapshot = None
    if "ai_report" not in st.session_state:
        st.session_state.ai_report = None
    if "key_validated" not in st.session_state:
        st.session_state.key_validated = False
    if "key_error" not in st.session_state:
        st.session_state.key_error = None
    if "key_valid" not in st.session_state:
        st.session_state.key_valid = False

    # Render UI components
    render_header()
    api_key = render_sidebar()

    # Permission Gate - Phase 1
    if not st.session_state.scan_initialized:
        render_permission_gate()
        return

    # POD-A: Sensor Probe
    with st.status("🔍 POD-A: ACQUIRING HARDWARE TELEMETRY...", expanded=True) as status:
        st.write("Reading CPU registers...")
        st.write("Mapping memory allocation...")
        st.write("Enumerating processes...")
        st.session_state.raw_data = pod_a_sensor_probe()
        st.write("✓ Sensor data acquired")
        status.update(label="✅ POD-A COMPLETE", state="complete")

    # POD-B: Contextualization
    with st.status("🧠 POD-B: BUILDING CONTEXT OBJECT...", expanded=False) as status:
        st.session_state.vitals_snapshot = pod_b_contextualize(st.session_state.raw_data)
        st.write(f"State object serialized: {len(json.dumps(st.session_state.vitals_snapshot))} bytes")
        status.update(label="✅ POD-B COMPLETE", state="complete")

    # Display Vitals Dashboard
    render_vitals_dashboard(st.session_state.raw_data, st.session_state.vitals_snapshot)

    # POD-C: AI Analysis
    st.markdown("### 🤖 POD-C: NEURAL ANALYSIS")

    if not api_key:
        st.warning("⚠ Enter your Gemini API key in the sidebar to enable AI analysis.")
    else:
        if st.button("🧠 RUN AI DIAGNOSTIC", key="run_ai", use_container_width=False):
            with st.status("🔮 POD-C: ANALYZING WITH GEMINI 1.5 FLASH...", expanded=True) as status:
                try:
                    st.write("Connecting to Gemini API...")
                    st.write("Sending telemetry snapshot...")
                    st.write("Awaiting expert diagnosis...")
                    st.session_state.ai_report = pod_c_brain_analyze(
                        st.session_state.vitals_snapshot,
                        api_key
                    )
                    status.update(label="✅ POD-C COMPLETE - ANALYSIS READY", state="complete")
                except Exception as e:
                    st.error(f"AI Analysis failed: {str(e)}")
                    status.update(label="❌ POD-C FAILED", state="error")

    # Display AI Report
    if st.session_state.ai_report:
        render_ai_report(st.session_state.ai_report)

    # POD-D: Action Agent
    st.markdown("---")
    pid_input, terminate_btn = render_action_agent()

    if terminate_btn and pid_input:
        with st.spinner(f"Terminating process {pid_input}..."):
            result = pod_d_terminate_process(pid_input)

            if result["success"]:
                st.success(f"✅ {result['message']}")
                # Refresh process list
                st.session_state.raw_data = pod_a_sensor_probe()
                st.session_state.vitals_snapshot = pod_b_contextualize(st.session_state.raw_data)
                st.rerun()
            else:
                st.error(f"⚠ {result['message']}")

    # Footer
    st.markdown(f"""
    <div style="text-align: center; padding: 40px 0; color: #444; font-size: 12px;">
        APEXVITALS v1.1.0 | ECE PORTFOLIO PROJECT | POWERED BY GEMINI 1.5 FLASH (V1 SDK)
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
