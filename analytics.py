"""
APEXVITALS v3.5 — Analytics Module
Matplotlib-based diagnostic visualizations with dark theme
matching the Indigo/Slate Streamlit dashboard.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for Streamlit/PDF compatibility
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.ticker as mticker
import tempfile
import os

# ═══════════════════════════════════════════════════════════════════════════════
# THEME CONSTANTS — Matched to ApexVitals Indigo/Slate Design System
# ═══════════════════════════════════════════════════════════════════════════════

DARK_BG = '#0f172a'          # Deep slate blue (matches BG_DEEP)
CARD_BG = '#1e293b'          # Slate 800 (matches BG_DARK)
GRID_COLOR = '#334155'       # Slate 700
TEXT_WHITE = '#f8fafc'        # Primary text
TEXT_MUTED = '#94a3b8'        # Muted text
ACCENT_INDIGO = '#6366f1'    # Primary accent
ACCENT_VIOLET = '#8b5cf6'    # Secondary accent
ACCENT_EMERALD = '#10b981'   # Success
ACCENT_AMBER = '#f59e0b'     # Warning
ACCENT_ROSE = '#ef4444'      # Danger
ACCENT_CYAN = '#06b6d4'      # Info


def _normalize_metric(value, low_threshold, high_threshold):
    """Normalize a raw metric to 0-100 scale for radar chart.
    
    Values at or below low_threshold → 100 (optimal).
    Values at or above high_threshold → 0 (critical).
    Linear interpolation between thresholds.
    """
    if value is None:
        return 50  # Neutral fallback for unavailable data
    clamped = max(low_threshold, min(high_threshold, value))
    # Invert: low raw value = high score (optimal)
    normalized = 100 * (1 - (clamped - low_threshold) / (high_threshold - low_threshold))
    return max(0, min(100, normalized))


def _power_plan_efficiency(power_plan_name, cpu_usage):
    """Calculate Power Plan Efficiency score (0-100).
    
    Heuristic: penalize mismatches between power plan and workload.
    - High Performance + Low Load = wasteful (moderate penalty)
    - Power Saver + High Load = bottleneck (heavy penalty)
    - Balanced = generally optimal (minor penalties)
    """
    plan = (power_plan_name or "").lower()
    
    if "saver" in plan or "power saver" in plan:
        # Power Saver: great for idle, terrible for heavy load
        if cpu_usage > 70:
            return max(10, 100 - (cpu_usage - 70) * 3)  # Heavy penalty
        return 90
    elif "high" in plan or "performance" in plan or "ultimate" in plan:
        # High Performance: great for heavy load, wasteful for idle
        if cpu_usage < 30:
            return 65  # Moderate penalty for wasting power
        return min(100, 70 + cpu_usage * 0.3)
    else:
        # Balanced / HP Optimized / Default: generally good
        if cpu_usage > 85:
            return max(50, 100 - (cpu_usage - 85) * 2)
        return 85


def generate_svi_radar_chart(metrics):
    """Generate a professional radar chart for the System Vitality Index breakdown.
    
    Args:
        metrics (dict): Dictionary with keys:
            - cpu_usage (float): CPU utilization percentage (0-100)
            - ram_usage (float): RAM utilization percentage (0-100)
            - gpu_temp (float|None): GPU temperature in °C
            - power_plan (str): Active power plan name
            - gpu_util (float|None): GPU core utilization percentage
            - vram_percent (float|None): VRAM usage percentage
    
    Returns:
        matplotlib.figure.Figure: The radar chart figure ready for st.pyplot() or savefig().
    """
    # ── Extract and normalize metrics to 0-100 inverted scale ──
    cpu_usage = metrics.get("cpu_usage", 0)
    ram_usage = metrics.get("ram_usage", 0)
    gpu_temp = metrics.get("gpu_temp")
    power_plan = metrics.get("power_plan", "Balanced")
    gpu_util = metrics.get("gpu_util")
    vram_percent = metrics.get("vram_percent")

    # Axis 1: Compute Load (CPU + GPU averaged, inverted → lower load = higher score)
    cpu_score = _normalize_metric(cpu_usage, 0, 100)
    gpu_score = _normalize_metric(gpu_util, 0, 100) if gpu_util is not None else cpu_score
    compute_load = (cpu_score * 0.6 + gpu_score * 0.4)

    # Axis 2: Memory Pressure (RAM + VRAM averaged, inverted)
    ram_score = _normalize_metric(ram_usage, 0, 100)
    vram_score = _normalize_metric(vram_percent, 0, 100) if vram_percent is not None else ram_score
    memory_pressure = (ram_score * 0.6 + vram_score * 0.4)

    # Axis 3: Thermal Stress (GPU temp inverted — lower temp = higher score)
    thermal_stress = _normalize_metric(gpu_temp, 40, 95) if gpu_temp is not None else 75

    # Axis 4: Power Plan Efficiency
    power_efficiency = _power_plan_efficiency(power_plan, cpu_usage)

    # ── Radar chart data ──
    categories = ['Compute\nLoad', 'Memory\nPressure', 'Thermal\nStress', 'Power Plan\nEfficiency']
    values = [compute_load, memory_pressure, thermal_stress, power_efficiency]
    N = len(categories)

    # Close the polygon
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    values_closed = values + [values[0]]
    angles_closed = angles + [angles[0]]

    # ── Create figure with dark theme ──
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)

    # ── Draw reference rings (grid circles) ──
    ring_levels = [20, 40, 60, 80, 100]
    for level in ring_levels:
        ring_angles = np.linspace(0, 2 * np.pi, 100)
        ring_values = [level] * 100
        ax.plot(ring_angles, ring_values, color=GRID_COLOR, linewidth=0.5, alpha=0.6)
        # Label on the first spoke
        ax.text(angles[0], level + 2, str(level), fontsize=7, color=TEXT_MUTED,
                ha='center', va='bottom', fontfamily='monospace')

    # ── Draw axis spokes ──
    for angle in angles:
        ax.plot([angle, angle], [0, 105], color=GRID_COLOR, linewidth=0.5, alpha=0.5)

    # ── Draw the data polygon ──
    # Gradient fill
    ax.fill(angles_closed, values_closed, alpha=0.15, color=ACCENT_INDIGO)
    
    # Outer glow effect (slightly larger, more transparent)
    ax.plot(angles_closed, values_closed, color=ACCENT_INDIGO, linewidth=2.5, alpha=0.3)
    
    # Main line
    ax.plot(angles_closed, values_closed, color=ACCENT_INDIGO, linewidth=2, alpha=0.9,
            marker='o', markersize=0)

    # ── Data point markers with color coding ──
    for i, (angle, value) in enumerate(zip(angles, values)):
        if value >= 70:
            point_color = ACCENT_EMERALD
        elif value >= 40:
            point_color = ACCENT_AMBER
        else:
            point_color = ACCENT_ROSE

        # Outer glow
        ax.plot(angle, value, 'o', color=point_color, markersize=12, alpha=0.2)
        # Inner point
        ax.plot(angle, value, 'o', color=point_color, markersize=7, alpha=0.9,
                markeredgecolor=DARK_BG, markeredgewidth=1.5)
        
        # Value label
        label_offset = 12
        ax.text(angle, value + label_offset, f'{value:.0f}',
                fontsize=10, fontweight='bold', color=point_color,
                ha='center', va='center', fontfamily='sans-serif')

    # ── Category labels ──
    ax.set_xticks(angles)
    ax.set_xticklabels(categories, fontsize=10, color=TEXT_WHITE, fontweight='600',
                       fontfamily='sans-serif')
    
    # Adjust label padding
    ax.tick_params(axis='x', pad=18)

    # ── Clean up axes ──
    ax.set_ylim(0, 115)
    ax.set_yticks([])  # Remove radial tick labels (we draw custom ones)
    ax.spines['polar'].set_visible(False)

    # ── Title ──
    fig.suptitle('SYSTEM VITALITY BREAKDOWN', fontsize=13, fontweight='bold',
                 color=TEXT_WHITE, fontfamily='sans-serif', y=0.98,
                 fontstyle='normal')
    
    # Subtitle with overall score
    avg_score = np.mean(values)
    if avg_score >= 70:
        status_text = "NOMINAL"
        status_color = ACCENT_EMERALD
    elif avg_score >= 40:
        status_text = "ELEVATED LOAD"
        status_color = ACCENT_AMBER
    else:
        status_text = "CRITICAL"
        status_color = ACCENT_ROSE

    fig.text(0.5, 0.93, f'Composite Score: {avg_score:.0f}/100 — {status_text}',
             fontsize=9, color=status_color, ha='center', fontfamily='monospace',
             fontstyle='normal')

    plt.tight_layout(rect=[0, 0.02, 1, 0.90])

    return fig


def save_chart_to_tempfile(fig, prefix='apexvitals_chart_'):
    """Save a Matplotlib figure to a temporary PNG file for PDF embedding.
    
    Args:
        fig (matplotlib.figure.Figure): The figure to save.
        prefix (str): Filename prefix for the temp file.
    
    Returns:
        str: Absolute path to the temporary PNG file.
    """
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False, prefix=prefix)
    fig.savefig(tmp.name, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor(),
                edgecolor='none', transparent=False)
    plt.close(fig)
    return tmp.name


# Legacy alias for backwards compatibility
save_radar_chart_to_tempfile = save_chart_to_tempfile


def generate_trend_chart(history):
    """Generate a time-series trend chart for CPU%, RAM%, and GPU Temp.
    
    Args:
        history (list[dict]): List of telemetry snapshots, each with keys:
            - timestamp (str): Time label (e.g., "14:32:05")
            - cpu (float): CPU usage %
            - ram (float): RAM usage %
            - gpu_temp (float): GPU temperature in °C (0 if unavailable)
    
    Returns:
        matplotlib.figure.Figure: The trend chart figure.
    """
    if not history or len(history) < 2:
        return None

    fig, ax1 = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(DARK_BG)
    ax1.set_facecolor(DARK_BG)

    timestamps = [h.get("timestamp", "") for h in history]
    cpu_vals = [h.get("cpu", 0) for h in history]
    ram_vals = [h.get("ram", 0) for h in history]
    gpu_vals = [h.get("gpu_temp", 0) for h in history]
    x = range(len(timestamps))

    # Plot CPU and RAM on primary y-axis (0-100%)
    ax1.plot(x, cpu_vals, color=ACCENT_INDIGO, linewidth=2, alpha=0.9, label='CPU %')
    ax1.fill_between(x, cpu_vals, alpha=0.08, color=ACCENT_INDIGO)
    ax1.plot(x, ram_vals, color=ACCENT_VIOLET, linewidth=2, alpha=0.9, label='RAM %')
    ax1.fill_between(x, ram_vals, alpha=0.08, color=ACCENT_VIOLET)

    ax1.set_ylabel('Utilization %', color=TEXT_MUTED, fontsize=10, fontfamily='sans-serif')
    ax1.set_ylim(0, 105)
    ax1.tick_params(axis='y', colors=TEXT_MUTED, labelsize=8)
    ax1.tick_params(axis='x', colors=TEXT_MUTED, labelsize=7)

    # Plot GPU Temp on secondary y-axis (°C)
    has_gpu = any(v > 0 for v in gpu_vals)
    if has_gpu:
        ax2 = ax1.twinx()
        ax2.set_facecolor('none')
        ax2.plot(x, gpu_vals, color=ACCENT_AMBER, linewidth=2, alpha=0.9,
                 linestyle='--', label='GPU Temp °C')
        ax2.set_ylabel('Temperature °C', color=ACCENT_AMBER, fontsize=10, fontfamily='sans-serif')
        ax2.set_ylim(30, 100)
        ax2.tick_params(axis='y', colors=ACCENT_AMBER, labelsize=8)
        ax2.spines['right'].set_color(GRID_COLOR)
        ax2.spines['right'].set_alpha(0.3)

    # X-axis labels (show every Nth label to avoid crowding)
    max_labels = 10
    step = max(1, len(timestamps) // max_labels)
    visible_ticks = list(range(0, len(timestamps), step))
    ax1.set_xticks(visible_ticks)
    ax1.set_xticklabels([timestamps[i] for i in visible_ticks], rotation=45, ha='right')

    # Threshold lines
    ax1.axhline(y=85, color=ACCENT_ROSE, linewidth=0.8, linestyle=':', alpha=0.5)
    ax1.text(len(x) - 1, 86.5, 'CPU DANGER', fontsize=7, color=ACCENT_ROSE, alpha=0.7,
             ha='right', fontfamily='monospace')

    # Grid and spines
    ax1.grid(axis='y', color=GRID_COLOR, alpha=0.3, linewidth=0.5)
    for spine in ['top', 'bottom', 'left', 'right']:
        ax1.spines[spine].set_color(GRID_COLOR)
        ax1.spines[spine].set_alpha(0.3)

    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    if has_gpu:
        lines2, labels2 = ax2.get_legend_handles_labels()
        lines1 += lines2
        labels1 += labels2
    ax1.legend(lines1, labels1, loc='upper left', fontsize=8,
               facecolor=CARD_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_WHITE,
               framealpha=0.9)

    # Title
    fig.suptitle('TELEMETRY TREND — SESSION HISTORY', fontsize=12, fontweight='bold',
                 color=TEXT_WHITE, fontfamily='sans-serif', y=1.02)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    return fig


def generate_svi_forecast_chart(current_svi, forecast_svi, current_status="", forecast_status=""):
    """Generate a bar chart comparing current SVI vs 5-minute forecast.
    
    Args:
        current_svi (int|float): Current System Vitality Index (0-100).
        forecast_svi (int|float): Predicted SVI in 5 minutes (0-100).
        current_status (str): Current status label (e.g., "NOMINAL").
        forecast_status (str): Predicted status label (e.g., "STRESSED").
    
    Returns:
        matplotlib.figure.Figure: The forecast comparison chart.
    """
    fig, ax = plt.subplots(figsize=(5, 4))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)

    labels = ['Current\nSVI', '5-Min\nForecast']
    values = [current_svi, forecast_svi]

    def _svi_color(val):
        if val >= 80:
            return ACCENT_EMERALD
        elif val >= 55:
            return ACCENT_AMBER
        elif val >= 30:
            return '#f97316'  # Orange
        return ACCENT_ROSE

    colors = [_svi_color(v) for v in values]

    bars = ax.bar(labels, values, width=0.5, color=colors, alpha=0.85,
                  edgecolor=[c for c in colors], linewidth=1.5)

    # Add glow effect behind bars
    for bar, color in zip(bars, colors):
        ax.bar(bar.get_x() + bar.get_width() / 2, bar.get_height(),
               width=bar.get_width() * 1.1, alpha=0.12, color=color, zorder=0)

    # Value labels on top of bars
    for bar, val, status in zip(bars, values, [current_status, forecast_status]):
        height = bar.get_height()
        color = _svi_color(val)
        ax.text(bar.get_x() + bar.get_width() / 2, height + 2,
                f'{val:.0f}', ha='center', va='bottom', fontsize=18,
                fontweight='bold', color=color, fontfamily='sans-serif')
        if status:
            ax.text(bar.get_x() + bar.get_width() / 2, height + 10,
                    status.upper(), ha='center', va='bottom', fontsize=8,
                    fontweight='bold', color=TEXT_MUTED, fontfamily='monospace')

    # Delta arrow between bars
    delta = forecast_svi - current_svi
    if abs(delta) > 0.5:
        arrow_color = ACCENT_EMERALD if delta > 0 else ACCENT_ROSE
        arrow_symbol = "▲" if delta > 0 else "▼"
        ax.text(0.5, max(values) + 18, f'{arrow_symbol} {delta:+.0f}',
                ha='center', va='bottom', fontsize=14, fontweight='bold',
                color=arrow_color, fontfamily='sans-serif',
                transform=ax.get_xaxis_transform())

    # Axes styling
    ax.set_ylim(0, max(values) + 25)
    ax.set_ylabel('SVI Score', color=TEXT_MUTED, fontsize=10, fontfamily='sans-serif')
    ax.tick_params(axis='y', colors=TEXT_MUTED, labelsize=8)
    ax.tick_params(axis='x', colors=TEXT_WHITE, labelsize=10)

    # Threshold bands
    ax.axhspan(0, 30, alpha=0.04, color=ACCENT_ROSE)
    ax.axhspan(30, 55, alpha=0.03, color='#f97316')
    ax.axhspan(55, 80, alpha=0.03, color=ACCENT_AMBER)
    ax.axhspan(80, 100, alpha=0.03, color=ACCENT_EMERALD)

    # Grid and spines
    ax.grid(axis='y', color=GRID_COLOR, alpha=0.3, linewidth=0.5)
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['bottom', 'left']:
        ax.spines[spine].set_color(GRID_COLOR)
        ax.spines[spine].set_alpha(0.3)

    # Title
    fig.suptitle('SVI FORECAST', fontsize=12, fontweight='bold',
                 color=TEXT_WHITE, fontfamily='sans-serif', y=1.0)

    fig.subplots_adjust(top=0.88, bottom=0.12, left=0.15, right=0.95)
    return fig
