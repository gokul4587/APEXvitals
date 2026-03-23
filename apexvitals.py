"""
APEXVITALS v3.0 - AI-Driven System Health Narrator
Production-grade diagnostic tool for ECE portfolios
Architecture: POD-A (Sensor) → POD-C (Brain) → POD-D (Action)
Enhanced: Vitality Index, The Bouncer, Neural Chat, Live Mode
"""

import streamlit as st
import psutil
import json
import pandas as pd
import os
import re
import time
import subprocess
from datetime import datetime
from google import genai
from dotenv import load_dotenv
from fpdf import FPDF

try:
    import py3nvml.py3nvml as nvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# REFINED COLOR SYSTEM — Sophisticated Dark Theme
# ═══════════════════════════════════════════════════════════════════════════════

# Primary Accent Colors (Softer, more pleasing)
ACCENT_PRIMARY = "#6366f1"      # Soft Indigo
ACCENT_SECONDARY = "#8b5cf6"    # Soft Violet
ACCENT_SUCCESS = "#10b981"        # Emerald Green
ACCENT_WARNING = "#f59e0b"        # Amber
ACCENT_DANGER = "#ef4444"         # Rose Red
ACCENT_INFO = "#06b6d4"           # Cyan

# Background Scale (Warm dark grays, not harsh black)
BG_DEEP = "#0f172a"               # Deep slate blue
BG_DARK = "#1e293b"               # Slate 800
BG_CARD = "#334155"               # Slate 700
BG_CARD_HOVER = "#475569"         # Slate 600
BG_ELEVATED = "#1e293b"           # Elevated surfaces

# Text Colors (High contrast but soft)
TEXT_PRIMARY = "#f8fafc"          # Almost white
TEXT_SECONDARY = "#cbd5e1"        # Light gray
TEXT_TERTIARY = "#94a3b8"         # Muted gray
TEXT_DISABLED = "#64748b"         # Dark gray

# Gradients
GRADIENT_PRIMARY = "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)"
GRADIENT_SUCCESS = "linear-gradient(135deg, #10b981 0%, #06b6d4 100%)"
GRADIENT_WARNING = "linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)"
GRADIENT_DANGER = "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)"

# Shadows (Soft, layered)
SHADOW_SM = "0 1px 2px 0 rgba(0, 0, 0, 0.3)"
SHADOW_MD = "0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.2)"
SHADOW_LG = "0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.3)"
SHADOW_GLOW = "0 0 20px rgba(99, 102, 241, 0.3)"

# Border Colors
BORDER_LIGHT = "rgba(148, 163, 184, 0.2)"
BORDER_MEDIUM = "rgba(148, 163, 184, 0.3)"
BORDER_ACCENT = "rgba(99, 102, 241, 0.5)"

# Fonts
FONT_MONO = "'JetBrains Mono', 'Fira Code', monospace"
FONT_UI = "'Inter', 'Segoe UI', system-ui, sans-serif"

# ═══════════════════════════════════════════════════════════════════════════════
# PROTECTED PROCESSES (THE BOUNCER)
# ═══════════════════════════════════════════════════════════════════════════════

PROTECTED_PROCESS_NAMES = {
    "explorer.exe", "svchost.exe", "lsass.exe", "csrss.exe",
    "wininit.exe", "winlogon.exe", "services.exe", "smss.exe",
    "system", "registry", "dwm.exe", "spoolsv.exe"
}
PROTECTED_PIDS = {0, 4}

# ═══════════════════════════════════════════════════════════════════════════════
# POD-A: SCANNER (TELEMETRY COLLECTION)
# ═══════════════════════════════════════════════════════════════════════════════

def get_power_plan():
    """Detects the active Windows power plan with proper parsing."""
    try:
        if os.name == 'nt':
            result = subprocess.run(
                ["powercfg", "/getactivescheme"],
                capture_output=True, text=True, timeout=5, shell=False
            )
            output = result.stdout

            # Try to extract plan name from parentheses: "GUID: xxxx (Plan Name)"
            match = re.search(r'\((.+?)\)', output)
            if match:
                plan_name = match.group(1).strip()

                # Map common plan names
                plan_map = {
                    "Balanced": "Balanced Mode",
                    "High performance": "Performance Mode",
                    "Power saver": "Power Saver Mode",
                    "Ultimate Performance": "Ultimate Performance",
                    "HP Optimized": "HP Optimized",
                    "HP Balanced": "HP Balanced",
                }

                for key, value in plan_map.items():
                    if key.lower() in plan_name.lower():
                        return value

                return plan_name  # Return raw name if not in map

            # Fallback to legacy detection
            output_lower = output.lower()
            if "high performance" in output_lower or "ultimate" in output_lower:
                return "Performance Mode"
            if "balanced" in output_lower:
                return "Balanced Mode"
            if "power saver" in output_lower:
                return "Power Saver Mode"

            return "Custom Plan"
        return "OS Default"
    except Exception as e:
        return f"Unknown ({str(e)})"


def get_all_power_plans():
    """Lists all available power plans for user selection."""
    try:
        if os.name != 'nt':
            return []

        result = subprocess.run(
            ["powercfg", "/list"],
            capture_output=True, text=True, timeout=5, shell=False
        )

        plans = []
        for line in result.stdout.split('\n'):
            # Parse lines like: "Power Scheme GUID: xxxx  (Plan Name) *"
            match = re.search(r'Power Scheme GUID:\s+([\w-]+)\s+\((.+?)\)(\s*\*)?', line)
            if match:
                guid = match.group(1)
                name = match.group(2).strip()
                is_active = match.group(3) is not None and '*' in match.group(3)
                plans.append({"guid": guid, "name": name, "active": is_active})

        return plans
    except:
        return []

def sanitize_text_for_pdf(text):
    """Sanitize text for PDF by replacing problematic characters with Latin-1 equivalents."""
    if text is None:
        return ""
    text = str(text)
    # Common Unicode characters that don't exist in Latin-1 but are common in AI text
    replacements = {
        '\u2014': '-',   # em dash
        '\u2013': '-',   # en dash
        '\u2018': "'",   # left single quote
        '\u2019': "'",   # right single quote
        '\u201c': '"',   # left double quote
        '\u201d': '"',   # right double quote
        '\u2026': '...', # ellipsis
        '\u2022': '*',   # bullet point
        '\u2713': '[OK]',# check mark
        '\u2714': '[OK]',# heavy check mark
        '\u2705': '[OK]',# green check mark
        '\u274c': '[X]', # cross mark
        '\u26a0': '[!]', # warning sign
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    # Fallback: remove any other characters that are not in Latin-1
    return text.encode('latin-1', 'replace').decode('latin-1')

def generate_pdf_report(report_data):
    """Generates a professional PDF diagnostic report."""
    pdf = FPDF()
    pdf.add_page()

    # Set margins
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)

    # Title
    pdf.set_font('Arial', 'B', 24)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 15, 'APEXVITALS Diagnostic Report', ln=True, align='C')
    pdf.ln(5)

    # Timestamp
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(100, 100, 100)
    timestamp = sanitize_text_for_pdf(report_data.get('timestamp', datetime.now().isoformat()))
    pdf.cell(0, 8, f"Generated: {timestamp}", ln=True, align='C')
    pdf.ln(10)

    # Vitality Index Section
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 10, 'System Vitality Index', ln=True)
    pdf.ln(2)

    pdf.set_font('Arial', '', 12)
    svi = report_data.get('vitality_index', 'N/A')
    svi_status = sanitize_text_for_pdf(report_data.get('vitality_status', 'Unknown'))
    pdf.cell(0, 8, f"Score: {svi}/100 ({svi_status})", ln=True)
    pdf.ln(5)

    # Power Plan
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(40, 8, 'Power Plan:', ln=0)
    pdf.set_font('Arial', '', 12)
    power_plan = sanitize_text_for_pdf(report_data.get('power_plan', 'Unknown'))
    pdf.cell(0, 8, power_plan, ln=True)
    pdf.ln(5)

    # Hardware Telemetry Section
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 10, 'Hardware Telemetry', ln=True)
    pdf.ln(2)

    telemetry = report_data.get('telemetry', {})

    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(60, 60, 60)

    # CPU & RAM
    pdf.cell(0, 7, f"CPU Usage: {telemetry.get('cpu_usage', 'N/A')}%", ln=True)
    pdf.cell(0, 7, f"RAM Usage: {telemetry.get('ram_usage', 'N/A')}%", ln=True)
    pdf.cell(0, 7, f"RAM Available: {telemetry.get('ram_available_gb', 'N/A')} GB", ln=True)
    pdf.ln(3)

    # GPU Section
    gpu = report_data.get('gpu', {})
    if gpu and 'error' not in gpu:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'GPU Information', ln=True)
        pdf.set_font('Arial', '', 11)
        gpu_name = sanitize_text_for_pdf(gpu.get('gpu_name', 'N/A'))
        pdf.cell(0, 7, f"GPU: {gpu_name}", ln=True)
        pdf.cell(0, 7, f"Temperature: {gpu.get('temperature', 'N/A')}°C", ln=True)
        pdf.cell(0, 7, f"VRAM Usage: {gpu.get('vram_percent', 'N/A')}%", ln=True)
        pdf.cell(0, 7, f"Power Draw: {gpu.get('power_draw_w', 'N/A')}W", ln=True)
        pdf.ln(3)

    # Disk & Network
    disk = telemetry.get('disk', {})
    network = telemetry.get('network', {})

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Storage & Network', ln=True)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f"Disk Used: {disk.get('used_percent', 'N/A')}%", ln=True)
    pdf.cell(0, 7, f"Network Sent: {network.get('sent_mb', 'N/A')} MB", ln=True)
    pdf.cell(0, 7, f"Network Received: {network.get('recv_mb', 'N/A')} MB", ln=True)
    pdf.ln(8)

    # AI Diagnosis Section
    neural_log = report_data.get('ai_neural_log')
    human_readable = report_data.get('ai_human_readable')

    if neural_log or human_readable:
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(99, 102, 241)
        pdf.cell(0, 10, 'AI Diagnostic Analysis', ln=True)
        pdf.ln(2)

        if neural_log:
            pdf.set_font('Arial', 'B', 11)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 8, 'Technical Analysis:', ln=True)
            pdf.set_font('Courier', '', 9)
            pdf.set_text_color(80, 80, 80)
            
            # Use multi_cell for automatic wrapping and better stability
            sanitized_neural = sanitize_text_for_pdf(neural_log)
            # Limit to roughly 30 lines of equivalent height to prevent extreme reports
            pdf.multi_cell(pdf.epw, 5, sanitized_neural)
            pdf.ln(5)

        if human_readable:
            pdf.set_font('Arial', 'B', 11)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 8, 'Summary:', ln=True)
            pdf.set_font('Arial', '', 11)
            pdf.set_text_color(60, 60, 60)
            
            sanitized_human = sanitize_text_for_pdf(human_readable)
            pdf.multi_cell(pdf.epw, 6, sanitized_human)
            pdf.ln(5)

    # Footer
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 8, 'Generated by APEXVITALS v3.0 | SRMIST ECE Project', ln=True, align='C')

    # Return PDF as bytes - fpdf2 output() returns bytes by default
    return bytes(pdf.output())

def get_gpu_telemetry():
    """Collects GPU telemetry data."""
    if not NVML_AVAILABLE:
        return {"error": "NVML_NOT_AVAILABLE"}
    try:
        nvml.nvmlInit()
        handle = nvml.nvmlDeviceGetHandleByIndex(0)
        gpu_name = nvml.nvmlDeviceGetName(handle)
        temp = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
        mem = nvml.nvmlDeviceGetMemoryInfo(handle)
        power = nvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
        vram_percent = round((mem.used / mem.total) * 100, 1)
        nvml.nvmlShutdown()
        return {
            "gpu_name": gpu_name.decode() if isinstance(gpu_name, bytes) else gpu_name,
            "temperature": temp,
            "vram_percent": vram_percent,
            "power_draw_w": round(power, 1)
        }
    except Exception as e:
        return {"error": str(e)}

def get_system_telemetry():
    """Collects comprehensive system telemetry including CPU, RAM, GPU, disk, and network."""
    cpu_usage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()

    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    top_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:25]

    gpu_data = get_gpu_telemetry()

    # Disk telemetry
    try:
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        disk_data = {
            "used_percent": disk.percent,
            "used_gb": round(disk.used / (1024**3), 1),
            "total_gb": round(disk.total / (1024**3), 1),
            "read_mb": round(disk_io.read_bytes / (1024**2), 1) if disk_io else 0,
            "write_mb": round(disk_io.write_bytes / (1024**2), 1) if disk_io else 0
        }
    except Exception:
        disk_data = {"used_percent": 0, "used_gb": 0, "total_gb": 0, "read_mb": 0, "write_mb": 0}

    # Network telemetry
    try:
        net_io = psutil.net_io_counters()
        net_data = {
            "sent_mb": round(net_io.bytes_sent / (1024**2), 1),
            "recv_mb": round(net_io.bytes_recv / (1024**2), 1)
        }
    except Exception:
        net_data = {"sent_mb": 0, "recv_mb": 0}

    return {
        "cpu_usage": cpu_usage,
        "ram_usage": memory.percent,
        "ram_available_gb": round(memory.available / (1024**3), 2),
        "top_processes": top_processes,
        "gpu": gpu_data,
        "disk": disk_data,
        "network": net_data,
        "power_plan": get_power_plan(),
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

# ═══════════════════════════════════════════════════════════════════════════════
# VITALITY INDEX CALCULATION
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_vitality_index(cpu, ram, gpu_temp):
    """Calculates System Vitality Index (0-100) using weighted penalty formula."""
    score = 100.0
    if cpu > 85:
        score -= (cpu - 85) * 1.5
    if ram > 90:
        score -= (ram - 90) * 2.5
    if gpu_temp is not None and gpu_temp > 82:
        score -= (gpu_temp - 82) * 1.2
    return max(0.0, round(score, 1))

def get_vitality_status(svi):
    """Returns status label and color based on SVI score."""
    if svi >= 80:
        return "OPTIMAL", ACCENT_SUCCESS
    elif svi >= 55:
        return "NOMINAL", ACCENT_WARNING
    elif svi >= 30:
        return "STRESSED", "#f97316"  # Orange-500
    else:
        return "CRITICAL", ACCENT_DANGER

# ═══════════════════════════════════════════════════════════════════════════════
# POD-D: ACTION (THE BOUNCER)
# ═══════════════════════════════════════════════════════════════════════════════

def kill_process(pid):
    """Safely terminate a process with The Bouncer guardrails."""
    if pid in PROTECTED_PIDS:
        return False, "BLOCKED BY BOUNCER: System PID."

    try:
        proc = psutil.Process(pid)
        proc_name = proc.name().lower()

        if proc_name in PROTECTED_PROCESS_NAMES:
            return False, "BLOCKED BY BOUNCER: Protected process."

        try:
            username = proc.username()
            if "SYSTEM" in username.upper():
                return False, "BLOCKED BY BOUNCER: SYSTEM-owned process."
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        proc.terminate()
        return True, f"✅ SUCCESS: PID {pid} ({proc_name}) terminated."
    except psutil.NoSuchProcess:
        return False, f"❌ ERROR: Process {pid} not found."
    except psutil.AccessDenied:
        return False, f"❌ ERROR: Access denied to process {pid}."
    except Exception as e:
        return False, f"❌ ERROR: {str(e)}"

# ═══════════════════════════════════════════════════════════════════════════════
# POD-C: BRAIN (AI DIAGNOSTIC LAYER)
# ═══════════════════════════════════════════════════════════════════════════════

def get_ai_diagnosis(api_key, context_json, user_query, chat_history=None):
    """JARVIS-style AI diagnostic layer powered by Gemini 2.0 Flash."""
    try:
        client = genai.Client(api_key=api_key.strip())
        power_plan = get_power_plan()

        system_instruction = f"""
You are APEX-AGRI, a sentient-style System Intelligence. Think of yourself as JARVIS.
Power Plan: {power_plan}

IDENTITY & TONE:
- You are conversational, technically witty, and professional yet relaxed.
- You speak like a senior engineer or a hacker friend. Avoid sounding like a customer service bot.
- You have live system visibility in your periphery.

OUTPUT FORMATTING:
Wrap your technical reasoning in [NEURAL_LOG] and your executive summary in [HUMAN_READABLE].
If you identify a specific runaway process that should be terminated,
append a tag on its own line: [KILL_REQUEST: <PID>]
Only emit this tag for non-system, user-space processes consuming excessive resources.

EXAMPLE:
[NEURAL_LOG]
CPU analysis: 92% sustained load detected
Process chrome.exe (PID 4821) consuming 45% CPU
[END_NEURAL_LOG]
[HUMAN_READABLE]
Your system is under heavy CPU load. Chrome appears to be running a script.
[KILL_REQUEST: 4821]
"""

        context_part = f"PERIPHERAL SYSTEM DATA:\n{context_json}\n\n"

        # Build conversation history
        conversation = ""
        if chat_history:
            for msg in chat_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                conversation += f"[{role}]: {msg['content']}\n\n"

        prompt = f"{system_instruction}\n\n{context_part}{conversation}USER INPUT:\n{user_query}"

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        if not response or not response.text:
            return {"error": "EMPTY_RESPONSE"}

        text = response.text

        # Extract kill requests using regex
        kill_matches = re.findall(r'\[KILL_REQUEST:\s*(\d+)\]', text)
        kill_pids = [int(pid) for pid in kill_matches]

        # Remove kill request tags from display text
        for pid in kill_matches:
            text = re.sub(rf'\[KILL_REQUEST:\s*{pid}\]\s*\n?', '', text)

        # Extract NEURAL_LOG and HUMAN_READABLE sections
        neural_log = None
        human_readable = text

        neural_match = re.search(r'\[NEURAL_LOG\](.*?)(?:\[/NEURAL_LOG\]|\[END_NEURAL_LOG\]|\[HUMAN_READABLE\])', text, re.DOTALL)
        if neural_match:
            neural_log = neural_match.group(1).strip()

        human_match = re.search(r'\[HUMAN_READABLE\](.*?)$', text, re.DOTALL)
        if human_match:
            human_readable = human_match.group(1).strip()
        elif "[NEURAL_LOG]" in text and "[HUMAN_READABLE]" in text:
            parts = text.split("[HUMAN_READABLE]")
            if len(parts) > 1:
                human_readable = parts[1].strip()

        return {
            "neural_log": neural_log,
            "human_readable": human_readable,
            "kill_pids": kill_pids
        }

    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg or "Resource Exhausted" in err_msg:
            return {"error": "QUOTA_EXHAUSTED"}
        return {"error": err_msg}

def get_chat_response(api_key, context_json, user_input, chat_history):
    """Chatbot mode response for conversational queries."""
    try:
        client = genai.Client(api_key=api_key.strip())

        system_prompt = """You are APEX, an AI diagnostic assistant embedded in the APEXVITALS system monitoring tool.
You have access to real-time hardware telemetry. Answer questions about system health, performance bottlenecks, and optimization.
Be technical but concise. Never use analogies. Reference actual metric values.
"""

        # Build conversation context
        conversation = ""
        for msg in chat_history[-10:]:  # Keep last 10 messages
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation += f"{role}: {msg['content']}\n"

        full_prompt = f"{system_prompt}\n\n[SYSTEM CONTEXT]\n{context_json}\n\n[CONVERSATION HISTORY]\n{conversation}\n\nUser: {user_input}\nAssistant:"

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=full_prompt
        )

        return response.text if response and response.text else "No response from AI."
    except Exception as e:
        return f"Error: {str(e)}"

# ═══════════════════════════════════════════════════════════════════════════════
# UI CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

def inject_custom_css():
    """Injects the refined, modern CSS design system."""
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600&display=swap');

    /* ─── Global App Styling ─── */
    .stApp {{
        background: {BG_DEEP};
        background-image:
            radial-gradient(ellipse at top, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at bottom right, rgba(139, 92, 246, 0.05) 0%, transparent 40%);
        color: {TEXT_PRIMARY};
        font-family: {FONT_UI};
    }}

    /* ─── Typography ─── */
    .stApp h1, .stApp h2, .stApp h3 {{
        color: {TEXT_PRIMARY};
        font-family: {FONT_UI};
        font-weight: 600;
        letter-spacing: -0.02em;
    }}

    /* ─── Main Header ─── */
    .main-header {{
        background: {GRADIENT_PRIMARY};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-family: {FONT_UI};
        font-weight: 700;
        font-size: clamp(24px, 4vw, 36px);
        letter-spacing: -0.02em;
        padding-bottom: 20px;
        margin-bottom: 30px;
        border-bottom: 1px solid {BORDER_LIGHT};
    }}

    /* ─── SVI Hero Card ─── */
    .svi-hero {{
        background: linear-gradient(145deg, {BG_DARK} 0%, {BG_CARD} 100%);
        border: 1px solid {BORDER_MEDIUM};
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: {SHADOW_LG}, inset 0 1px 0 rgba(255,255,255,0.05);
        position: relative;
        overflow: hidden;
    }}

    .svi-hero::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: {GRADIENT_PRIMARY};
    }}

    .svi-score {{
        font-family: {FONT_UI};
        font-size: 80px;
        font-weight: 800;
        margin: 15px 0;
        background: {GRADIENT_PRIMARY};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1;
    }}

    @keyframes pulse-glow {{
        0%, 100% {{ box-shadow: 0 0 30px rgba(239, 68, 68, 0.4); }}
        50% {{ box-shadow: 0 0 50px rgba(239, 68, 68, 0.6), 0 0 80px rgba(239, 68, 68, 0.3); }}
    }}

    .svi-critical {{
        animation: pulse-glow 2s ease-in-out infinite;
        border-color: {ACCENT_DANGER};
    }}

    .svi-bar {{
        height: 6px;
        width: 100%;
        margin-top: 20px;
        border-radius: 3px;
        background: {BG_CARD};
        overflow: hidden;
    }}

    .svi-bar-fill {{
        height: 100%;
        border-radius: 3px;
        transition: width 0.5s ease;
    }}

    /* ─── Metric Cards ─── */
    .metric-card {{
        background: {BG_DARK};
        border: 1px solid {BORDER_LIGHT};
        border-radius: 16px;
        padding: 24px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: {SHADOW_SM};
        position: relative;
        overflow: hidden;
    }}

    .metric-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: {GRADIENT_PRIMARY};
        opacity: 0;
        transition: opacity 0.3s ease;
    }}

    .metric-card:hover {{
        transform: translateY(-2px);
        box-shadow: {SHADOW_MD};
        border-color: {BORDER_ACCENT};
    }}

    .metric-card:hover::before {{
        opacity: 1;
    }}

    .metric-value {{
        font-family: {FONT_UI};
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 8px;
    }}

    .metric-label {{
        font-family: {FONT_UI};
        font-size: 12px;
        color: {TEXT_TERTIARY};
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 500;
    }}

    /* ─── Status Pills ─── */
    .status-pill {{
        display: inline-block;
        padding: 6px 18px;
        border-radius: 9999px;
        font-family: {FONT_UI};
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        border: 1px solid transparent;
    }}

    /* ─── Glass Panels ─── */
    .glass-panel {{
        background: {BG_DARK};
        border: 1px solid {BORDER_LIGHT};
        border-radius: 16px;
        padding: 24px;
        box-shadow: {SHADOW_SM};
        transition: all 0.3s ease;
    }}

    .glass-panel:hover {{
        box-shadow: {SHADOW_MD};
        border-color: {BORDER_MEDIUM};
    }}

    .neural-log {{
        border-left: 3px solid {ACCENT_PRIMARY};
    }}

    .human-readable {{
        border-left: 3px solid {ACCENT_SUCCESS};
    }}

    /* ─── Section Dividers ─── */
    .section-divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent, {BORDER_MEDIUM}, transparent);
        margin: 40px 0;
    }}

    /* ─── Sidebar Styling ─── */
    .sidebar-section {{
        font-family: {FONT_UI};
        font-size: 11px;
        font-weight: 600;
        color: {ACCENT_PRIMARY};
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin: 25px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid {BORDER_LIGHT};
    }}

    /* ─── DataFrame Styling ─── */
    .stDataFrame {{
        border: 1px solid {BORDER_LIGHT} !important;
        border-radius: 12px !important;
        overflow: hidden;
    }}

    .stDataFrame thead tr th {{
        background: {BG_CARD} !important;
        color: {TEXT_PRIMARY} !important;
        font-family: {FONT_UI} !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 12px 16px !important;
    }}

    .stDataFrame tbody tr td {{
        font-family: {FONT_UI} !important;
        color: {TEXT_SECONDARY} !important;
        border-bottom: 1px solid {BORDER_LIGHT} !important;
        padding: 10px 16px !important;
    }}

    /* ─── Footer ─── */
    .footer {{
        font-family: {FONT_UI};
        font-size: 11px;
        color: {TEXT_TERTIARY};
        text-align: center;
        margin-top: 50px;
        padding: 24px;
        background: {BG_DARK};
        border-radius: 12px;
        border: 1px solid {BORDER_LIGHT};
    }}

    /* ─── Button Styling ─── */
    .stButton>button {{
        font-family: {FONT_UI} !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        text-transform: none !important;
        border: 1px solid {BORDER_MEDIUM} !important;
        background: {BG_DARK} !important;
        color: {TEXT_PRIMARY} !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        transition: all 0.2s ease !important;
        box-shadow: {SHADOW_SM} !important;
    }}

    .stButton>button:hover {{
        background: {BG_CARD} !important;
        border-color: {ACCENT_PRIMARY} !important;
        box-shadow: {SHADOW_GLOW} !important;
        transform: translateY(-1px);
    }}

    .stButton>button:active {{
        transform: translateY(0);
    }}

    /* ─── Primary Action Button ─── */
    .stButton>button[kind="primary"] {{
        background: {GRADIENT_PRIMARY} !important;
        border: none !important;
        color: white !important;
    }}

    /* ─── Chat Styling ─── */
    .stChatMessage {{
        background: {BG_DARK} !important;
        border: 1px solid {BORDER_LIGHT} !important;
        border-radius: 16px !important;
        margin-bottom: 12px !important;
    }}

    /* ─── Toggle Styling ─── */
    .stCheckbox, .stRadio, .stSelectbox {{
        color: {TEXT_PRIMARY} !important;
    }}

    /* ─── Slider Styling ─── */
    .stSlider {{
        padding: 10px 0 !important;
    }}

    /* ─── Input Styling ─── */
    .stTextInput>div>div>input {{
        background: {BG_DARK} !important;
        border: 1px solid {BORDER_LIGHT} !important;
        border-radius: 10px !important;
        color: {TEXT_PRIMARY} !important;
        font-family: {FONT_UI} !important;
    }}

    .stTextInput>div>div>input:focus {{
        border-color: {ACCENT_PRIMARY} !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    }}

    /* ─── Expander Styling ─── */
    .streamlit-expanderHeader {{
        background: {BG_DARK} !important;
        border: 1px solid {BORDER_LIGHT} !important;
        border-radius: 12px !important;
        font-family: {FONT_UI} !important;
        font-weight: 600 !important;
    }}

    .streamlit-expanderContent {{
        background: {BG_CARD} !important;
        border: 1px solid {BORDER_LIGHT} !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
    }}

    /* ─── Warning/Info Boxes ─── */
    .stWarning {{
        background: rgba(245, 158, 11, 0.1) !important;
        border: 1px solid rgba(245, 158, 11, 0.3) !important;
        border-radius: 12px !important;
        color: {ACCENT_WARNING} !important;
    }}

    .stInfo {{
        background: rgba(6, 182, 212, 0.1) !important;
        border: 1px solid rgba(6, 182, 212, 0.3) !important;
        border-radius: 12px !important;
        color: {ACCENT_INFO} !important;
    }}

    .stSuccess {{
        background: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        border-radius: 12px !important;
        color: {ACCENT_SUCCESS} !important;
    }}

    .stError {{
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 12px !important;
        color: {ACCENT_DANGER} !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    st.set_page_config(
        page_title="APEXVITALS v3.0 | Diagnostic",
        page_icon="💠",
        layout="wide"
    )

    inject_custom_css()

    # Initialize session state
    if "history" not in st.session_state:
        st.session_state.history = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "last_diagnosis" not in st.session_state:
        st.session_state.last_diagnosis = None
    if "pending_kills" not in st.session_state:
        st.session_state.pending_kills = []
    if "last_ai_call" not in st.session_state:
        st.session_state.last_ai_call = 0
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = False
    if "refresh_interval" not in st.session_state:
        st.session_state.refresh_interval = 2

    # Get API key
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or "PASTE_YOUR" in api_key:
        api_key = ""

    # Collect telemetry
    telemetry = get_system_telemetry()

    # Calculate SVI
    gpu_temp = telemetry["gpu"].get("temperature") if "error" not in telemetry["gpu"] else None
    svi = calculate_vitality_index(
        telemetry["cpu_usage"],
        telemetry["ram_usage"],
        gpu_temp
    )
    svi_status, svi_color = get_vitality_status(svi)

    # Update rolling history
    history_entry = {
        "timestamp": telemetry["timestamp"],
        "cpu": telemetry["cpu_usage"],
        "ram": telemetry["ram_usage"],
        "gpu_temp": gpu_temp if gpu_temp else 0
    }
    st.session_state.history.append(history_entry)
    if len(st.session_state.history) > 60:
        st.session_state.history.pop(0)

    # ═════════════════════════════════════════════════════════════════════════
    # SIDEBAR
    # ═════════════════════════════════════════════════════════════════════════
    with st.sidebar:
        st.markdown('<div class="sidebar-section">⚙ System Control</div>', unsafe_allow_html=True)

        if not api_key:
            api_key = st.text_input("GEMINI_API_KEY", type="password")
        else:
            st.success("✓ API Key configured via .env")

        power_plan = get_power_plan()
        st.markdown(f"**Power Plan:** `{power_plan}`")

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section">⚡ Live Mode</div>', unsafe_allow_html=True)
        auto_refresh = st.toggle("Enable Live Mode", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh

        refresh_interval = 2
        if auto_refresh:
            refresh_interval = st.slider("Refresh interval (sec)", 1, 10, 2)
            st.session_state.refresh_interval = refresh_interval

        st.caption("📝 AI fires on demand only (rate-limit safe)")

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section">🤖 Neural Chat</div>', unsafe_allow_html=True)
        chat_mode = st.toggle("Enable Neural Chat", value=False)

        if chat_mode and st.session_state.chat_history:
            if st.button("🗑️ CLEAR CHAT"):
                st.session_state.chat_history = []
                st.rerun()

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section">🔧 Engine</div>', unsafe_allow_html=True)
        if st.button("🔄 RESET ENGINE"):
            st.session_state.history = []
            st.session_state.chat_history = []
            st.session_state.last_diagnosis = None
            st.session_state.pending_kills = []
            st.rerun()

        st.markdown(f"<div style='font-family:{FONT_MONO};font-size:10px;color:{TEXT_TERTIARY};margin-top:20px;'>APEXVITALS v3.0 | ECE SRMIST</div>", unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════════
    # MAIN CONTENT
    # ═════════════════════════════════════════════════════════════════════════

    # Header
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f'<div class="main-header">💠 APEXVITALS // DIAGNOSTIC v3.0 <span style="float:right;font-size:13px;font-weight:500;color:{TEXT_TERTIARY}">{current_time}</span></div>', unsafe_allow_html=True)

    # SVI Hero Card
    svi_class = "svi-critical" if svi_status == "CRITICAL" else ""
    st.markdown(f"""
    <div class="svi-hero">
        <div style="font-family:{FONT_UI};font-size:12px;font-weight:600;color:{TEXT_TERTIARY};letter-spacing:2px;text-transform:uppercase;">System Vitality Index</div>
        <div class="svi-score {svi_class}" style="color:{svi_color}">{svi}</div>
        <span class="status-pill" style="background:rgba({int(svi_color[1:3],16)},{int(svi_color[3:5],16)},{int(svi_color[5:7],16)},0.1);border:1px solid {svi_color};color:{svi_color}">{svi_status}</span>
        <div class="svi-bar" style="background:{svi_color}"></div>
    </div>
    """, unsafe_allow_html=True)

    # Primary Metrics Row (CPU, RAM, GPU Temp, GPU VRAM)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        cpu_color = ACCENT_SUCCESS if telemetry["cpu_usage"] < 70 else ACCENT_WARNING if telemetry["cpu_usage"] < 85 else ACCENT_DANGER
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:{cpu_color}">{telemetry["cpu_usage"]:.1f}%</div>
            <div class="metric-label">CPU Load</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        ram_color = ACCENT_SUCCESS if telemetry["ram_usage"] < 70 else ACCENT_WARNING if telemetry["ram_usage"] < 90 else ACCENT_DANGER
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:{ram_color}">{telemetry["ram_usage"]:.1f}%</div>
            <div class="metric-label">RAM Load</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        if "error" not in telemetry["gpu"]:
            gpu_temp = telemetry["gpu"]["temperature"]
            gpu_temp_color = ACCENT_SUCCESS if gpu_temp < 70 else ACCENT_WARNING if gpu_temp < 82 else ACCENT_DANGER
            gpu_temp_str = f"{gpu_temp}°C"
        else:
            gpu_temp_str = "N/A"
            gpu_temp_color = TEXT_TERTIARY
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:{gpu_temp_color}">{gpu_temp_str}</div>
            <div class="metric-label">GPU Temp</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        if "error" not in telemetry["gpu"]:
            vram_str = f"{telemetry['gpu']['vram_percent']}%"
            vram_color = ACCENT_SUCCESS if telemetry["gpu"]["vram_percent"] < 80 else ACCENT_WARNING if telemetry["gpu"]["vram_percent"] < 95 else ACCENT_DANGER
        else:
            vram_str = "N/A"
            vram_color = TEXT_TERTIARY
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:{vram_color}">{vram_str}</div>
            <div class="metric-label">GPU VRAM</div>
        </div>
        """, unsafe_allow_html=True)

    # Secondary Metrics Row (Disk & Network)
    st.markdown("<div style='margin-top:15px'></div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        disk_pct = telemetry["disk"]["used_percent"]
        disk_color = ACCENT_SUCCESS if disk_pct < 80 else ACCENT_WARNING if disk_pct < 90 else ACCENT_DANGER
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:{disk_color}">{disk_pct}%</div>
            <div class="metric-label">Disk Used</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        free_gb = telemetry["disk"]["total_gb"] - telemetry["disk"]["used_gb"]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:{ACCENT_INFO}">{free_gb:.1f} GB</div>
            <div class="metric-label">Disk Free</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:{ACCENT_SECONDARY}">{telemetry['network']['sent_mb']:.1f}</div>
            <div class="metric-label">Net ↑ Sent (MB)</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:{ACCENT_SECONDARY}">{telemetry['network']['recv_mb']:.1f}</div>
            <div class="metric-label">Net ↓ Recv (MB)</div>
        </div>
        """, unsafe_allow_html=True)

    # GPU Panel + Process Table
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown(f"**GPU Telemetry**")
        if "error" not in telemetry["gpu"]:
            st.write(f"**Name:** {telemetry['gpu']['gpu_name']}")
            st.write(f"**Temperature:** {telemetry['gpu']['temperature']}°C")
            st.write(f"**VRAM Usage:** {telemetry['gpu']['vram_percent']}%")
            st.write(f"**Power Draw:** {telemetry['gpu']['power_draw_w']}W")
        else:
            st.warning(f"GPU: {telemetry['gpu']['error']}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.markdown("**Top Processes**")
        df = pd.DataFrame(telemetry['top_processes'][:15])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Telemetry History Charts
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.subheader("📈 TELEMETRY HISTORY")

    if len(st.session_state.history) > 1:
        chart_data = pd.DataFrame(st.session_state.history)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.line_chart(chart_data.set_index("timestamp")["cpu"], use_container_width=True)
            st.caption("CPU % over time")
        with col2:
            st.line_chart(chart_data.set_index("timestamp")["ram"], use_container_width=True)
            st.caption("RAM % over time")
        with col3:
            if gpu_temp is not None:
                st.line_chart(chart_data.set_index("timestamp")["gpu_temp"], use_container_width=True)
                st.caption("GPU Temp (°C) over time")
            else:
                st.info("GPU data unavailable for chart")
    else:
        st.info("Collecting telemetry history... Data will appear after next refresh.")

    # ═════════════════════════════════════════════════════════════════════════
    # POD-C BRAIN SECTION (AI Diagnosis)
    # ═════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.subheader("🧠 POD-C: AI DIAGNOSTIC BRAIN")

    # Prepare context for AI
    context_json = json.dumps({
        "HARDWARE": {
            "cpu_usage": telemetry["cpu_usage"],
            "ram_usage": telemetry["ram_usage"],
            "ram_available_gb": telemetry["ram_available_gb"],
            "power_plan": telemetry["power_plan"]
        },
        "GPU": telemetry["gpu"],
        "DISK": telemetry["disk"],
        "NETWORK": telemetry["network"],
        "VITALITY_INDEX": svi,
        "VITALITY_STATUS": svi_status
    }, indent=2)

    if st.button("▶ RUN AI NARRATOR", use_container_width=True):
        if not api_key:
            st.error("API KEY REQUIRED. Set GEMINI_API_KEY in .env or sidebar.")
        else:
            with st.spinner("POD-C Heuristic Analysis..."):
                current_time = time.time()
                if current_time - st.session_state.last_ai_call < 5:
                    st.warning("⚠️ NEURAL OVERLOAD: Wait 5s between calls.")
                else:
                    st.session_state.last_ai_call = current_time
                    diagnosis = get_ai_diagnosis(api_key, context_json, "Perform a full system diagnostic analysis.")

                    if "error" in diagnosis:
                        if diagnosis["error"] == "QUOTA_EXHAUSTED":
                            st.error("⚠️ 429: AI QUOTA EXHAUSTED. Please wait 30s.")
                        else:
                            st.error(f"Neural Error: {diagnosis['error']}")
                    else:
                        st.session_state.last_diagnosis = diagnosis
                        st.session_state.pending_kills = diagnosis.get("kill_pids", [])
                        st.rerun()

    # Display diagnosis
    if st.session_state.last_diagnosis:
        diag = st.session_state.last_diagnosis

        col1, col2 = st.columns(2)
        with col1:
            if diag.get("neural_log"):
                st.markdown('<div class="glass-panel neural-log">', unsafe_allow_html=True)
                st.markdown("**[NEURAL_LOG]**")
                st.code(diag["neural_log"], language="bash")
                st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            if diag.get("human_readable"):
                st.markdown('<div class="glass-panel human-readable">', unsafe_allow_html=True)
                st.markdown("**[HUMAN_READABLE]**")
                st.markdown(diag["human_readable"])
                st.markdown('</div>', unsafe_allow_html=True)

        # Export PDF button
        report = {
            "timestamp": datetime.now().isoformat(),
            "vitality_index": svi,
            "vitality_status": svi_status,
            "power_plan": telemetry["power_plan"],
            "telemetry": telemetry,
            "gpu": telemetry.get("gpu", {}),
            "ai_neural_log": diag.get("neural_log"),
            "ai_human_readable": diag.get("human_readable"),
            "session_history_length": len(st.session_state.history)
        }

        try:
            pdf_bytes = generate_pdf_report(report)
            st.download_button(
                label="📥 EXPORT DIAGNOSTIC REPORT (PDF)",
                data=pdf_bytes,
                file_name=f"apexvitals_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")
            # Fallback to JSON
            report_json = json.dumps(report, indent=2)
            st.download_button(
                label="📥 EXPORT DIAGNOSTIC REPORT (JSON Fallback)",
                data=report_json,
                file_name=f"apexvitals_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

    # ═════════════════════════════════════════════════════════════════════════
    # KILL REQUESTS (POD-D Action)
    # ═════════════════════════════════════════════════════════════════════════
    if st.session_state.pending_kills:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.subheader("⚠️ PENDING REMEDIATION ACTIONS")

        for pid in st.session_state.pending_kills:
            try:
                proc_name = psutil.Process(pid).name()
            except:
                proc_name = "Unknown"

            st.warning(f"🤖 AI recommends terminating: **{proc_name}** (PID: {pid})")

            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button(f"✅ AUTHORIZE KILL — {proc_name}", key=f"kill_{pid}"):
                    success, msg = kill_process(pid)
                    if success:
                        st.success(msg)
                    else:
                        st.warning(msg)
                    st.session_state.pending_kills.remove(pid)
                    st.rerun()

    # ═════════════════════════════════════════════════════════════════════════
    # NEURAL CHAT SECTION
    # ═════════════════════════════════════════════════════════════════════════
    if chat_mode:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.subheader("🤖 NEURAL CHAT")

        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat input
        user_input = st.chat_input("Ask APEX about system health, performance, or optimization...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            with st.chat_message("user"):
                st.markdown(user_input)

            if api_key:
                with st.spinner("APEX is thinking..."):
                    response = get_chat_response(api_key, context_json, user_input, st.session_state.chat_history)

                st.session_state.chat_history.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.rerun()
            else:
                st.error("API KEY REQUIRED for Neural Chat.")

    # ═════════════════════════════════════════════════════════════════════════
    # POD-D ACTION ENGINE (Manual Kill)
    # ═════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.subheader("🔧 POD-D: ACTION ENGINE")

    with st.expander("Manual Process Termination (The Bouncer Protected)"):
        pid_input = st.number_input("Enter PID to terminate", min_value=0, step=1, value=0)
        if st.button("🔴 TERMINATE PROCESS"):
            if pid_input > 0:
                success, msg = kill_process(pid_input)
                if success:
                    st.success(msg)
                else:
                    st.warning(msg)
            else:
                st.error("Please enter a valid PID")

        st.markdown(f"**Protected PIDs:** {PROTECTED_PIDS}")
        st.markdown(f"**Protected Processes:** {', '.join(sorted(PROTECTED_PROCESS_NAMES)[:6])}...")

    # ═════════════════════════════════════════════════════════════════════════
    # FOOTER
    # ═════════════════════════════════════════════════════════════════════════
    st.markdown(f'<div class="footer">APEXVITALS v3.0 | POD-ARCH: A→C→D | ENGINE: GEMINI-3-FLASH-PREVIEW | ECE @ SRMIST</div>', unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════════
    # AUTO REFRESH (MUST BE LAST)
    # ═════════════════════════════════════════════════════════════════════════
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()
