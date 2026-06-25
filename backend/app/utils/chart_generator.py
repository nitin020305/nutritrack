"""
Generates nutrient comparison charts (goal vs actual).
Returns charts as base64-encoded PNG strings for API responses.
"""

import io
import base64
import matplotlib
matplotlib.use("Agg")   # Non-interactive backend (no display needed)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

CHART_STYLE = {
    "bg": "#0f1117",
    "surface": "#1a1d27",
    "accent_goal": "#4ade80",    # green
    "accent_actual": "#f97316",  # orange
    "text": "#e2e8f0",
    "subtext": "#94a3b8",
    "grid": "#2d3748",
}

def _fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=CHART_STYLE["bg"])
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded

def generate_goal_vs_actual_chart(goal_nutrients: dict, actual_nutrients: dict,
                                   title: str = "Today's Nutrients") -> str:
    """
    Bar chart comparing goal vs actual nutrients.

    Args:
        goal_nutrients: {calories, protein_g, carbs_g, fat_g, fiber_g}
        actual_nutrients: same keys

    Returns:
        base64-encoded PNG string
    """
    labels = ["Calories\n(kcal)", "Protein\n(g)", "Carbs\n(g)", "Fat\n(g)", "Fiber\n(g)"]
    keys = ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g"]

    goal_vals = [goal_nutrients.get(k, 0) for k in keys]
    actual_vals = [actual_nutrients.get(k, 0) for k in keys]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor(CHART_STYLE["bg"])
    ax.set_facecolor(CHART_STYLE["surface"])

    bars_goal = ax.bar(x - width/2, goal_vals, width, label="Goal",
                       color=CHART_STYLE["accent_goal"], alpha=0.85, zorder=3)
    bars_actual = ax.bar(x + width/2, actual_vals, width, label="Actual",
                         color=CHART_STYLE["accent_actual"], alpha=0.85, zorder=3)

    # Value labels on bars
    for bar in bars_goal:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + max(goal_vals)*0.01,
                f"{h:.0f}", ha="center", va="bottom",
                color=CHART_STYLE["accent_goal"], fontsize=8, fontweight="bold")
    for bar in bars_actual:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + max(actual_vals or [1])*0.01,
                f"{h:.0f}", ha="center", va="bottom",
                color=CHART_STYLE["accent_actual"], fontsize=8, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=CHART_STYLE["text"], fontsize=9)
    ax.yaxis.label.set_color(CHART_STYLE["subtext"])
    ax.tick_params(colors=CHART_STYLE["subtext"])
    ax.spines[:].set_color(CHART_STYLE["grid"])
    ax.yaxis.grid(True, color=CHART_STYLE["grid"], linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.set_title(title, color=CHART_STYLE["text"], fontsize=13, fontweight="bold", pad=14)

    legend = ax.legend(facecolor=CHART_STYLE["surface"], edgecolor=CHART_STYLE["grid"],
                       labelcolor=CHART_STYLE["text"], fontsize=9)

    plt.tight_layout()
    return _fig_to_base64(fig)

def generate_weekly_trend_chart(daily_data: list, calorie_goal: float) -> str:
    """
    Line chart of daily calories over the past 7 days vs goal.

    Args:
        daily_data: [{date, calories}, ...] sorted oldest to newest
        calorie_goal: daily target

    Returns:
        base64-encoded PNG string
    """
    dates = [d["date"] for d in daily_data]
    calories = [d["calories"] for d in daily_data]

    fig, ax = plt.subplots(figsize=(9, 4))
    fig.patch.set_facecolor(CHART_STYLE["bg"])
    ax.set_facecolor(CHART_STYLE["surface"])

    ax.plot(dates, calories, color=CHART_STYLE["accent_actual"],
            linewidth=2.5, marker="o", markersize=6, zorder=3, label="Actual")
    ax.axhline(calorie_goal, color=CHART_STYLE["accent_goal"],
               linewidth=1.5, linestyle="--", zorder=2, label=f"Goal ({calorie_goal:.0f} kcal)")

    ax.fill_between(range(len(dates)), calories, calorie_goal,
                    where=[c < calorie_goal for c in calories],
                    alpha=0.12, color=CHART_STYLE["accent_goal"], interpolate=True)
    ax.fill_between(range(len(dates)), calories, calorie_goal,
                    where=[c >= calorie_goal for c in calories],
                    alpha=0.12, color=CHART_STYLE["accent_actual"], interpolate=True)

    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(dates, rotation=35, ha="right",
                       color=CHART_STYLE["subtext"], fontsize=8)
    ax.tick_params(colors=CHART_STYLE["subtext"])
    ax.spines[:].set_color(CHART_STYLE["grid"])
    ax.yaxis.grid(True, color=CHART_STYLE["grid"], linewidth=0.5)
    ax.set_title("7-Day Calorie Trend", color=CHART_STYLE["text"],
                 fontsize=13, fontweight="bold", pad=14)
    ax.legend(facecolor=CHART_STYLE["surface"], edgecolor=CHART_STYLE["grid"],
              labelcolor=CHART_STYLE["text"], fontsize=9)

    plt.tight_layout()
    return _fig_to_base64(fig)

def generate_macros_pie_chart(calories: float, protein_g: float,
                               carbs_g: float, fat_g: float) -> str:
    """
    Donut chart showing macronutrient breakdown.
    Returns base64 PNG.
    """
    protein_kcal = protein_g * 4
    carbs_kcal = carbs_g * 4
    fat_kcal = fat_g * 9

    sizes = [protein_kcal, carbs_kcal, fat_kcal]
    labels = [f"Protein\n{protein_g:.0f}g", f"Carbs\n{carbs_g:.0f}g", f"Fat\n{fat_g:.0f}g"]
    colors = ["#818cf8", "#f97316", "#facc15"]

    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor(CHART_STYLE["bg"])
    ax.set_facecolor(CHART_STYLE["bg"])

    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors,
        autopct="%1.0f%%", startangle=90,
        wedgeprops=dict(width=0.55, edgecolor=CHART_STYLE["bg"], linewidth=2),
        textprops=dict(color=CHART_STYLE["text"], fontsize=9),
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_color(CHART_STYLE["bg"])
        at.set_fontweight("bold")

    ax.text(0, 0, f"{calories:.0f}\nkcal", ha="center", va="center",
            color=CHART_STYLE["text"], fontsize=12, fontweight="bold")
    ax.set_title("Macro Breakdown", color=CHART_STYLE["text"],
                 fontsize=13, fontweight="bold", pad=10)

    plt.tight_layout()
    return _fig_to_base64(fig)
