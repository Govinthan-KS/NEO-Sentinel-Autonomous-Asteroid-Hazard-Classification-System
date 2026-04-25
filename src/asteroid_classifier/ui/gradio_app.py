"""
NEO-Sentinel: Prediction Portal — Gradio UI
============================================
Deep ocean-themed prediction interface consistent with the Admin Dashboard.
Connects to the in-process AsteroidPredictor via the PredictorWrapper injected
by api/main.py — no local HTTP overhead.

Navigation:
  - "Admin Dashboard →" button links to port 8501 (Streamlit).
"""

import gradio as gr
from asteroid_classifier.api.schemas import AsteroidFeatures


# ---------------------------------------------------------------------------
# Shared CSS — mirrors the dashboard ocean design system exactly
# ---------------------------------------------------------------------------
OCEAN_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global canvas ── */
body, .gradio-container {
    background: linear-gradient(160deg, #03111f 0%, #041e33 40%, #062c4a 75%, #04223c 100%) !important;
    font-family: 'Inter', sans-serif !important;
    color: #d6eaf8 !important;
    min-height: 100vh;
}

/* ── Ambient ocean glow ── */
.gradio-container::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background:
        radial-gradient(ellipse 70% 40% at 15% 75%, rgba(0,168,232,0.05) 0%, transparent 55%),
        radial-gradient(ellipse 50% 30% at 85% 20%, rgba(0,210,200,0.04) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
}

/* ── Hero banner ── */
.neo-banner {
    background: linear-gradient(135deg, rgba(0,90,160,0.55) 0%, rgba(0,160,200,0.35) 100%);
    border: 1px solid rgba(0,180,220,0.25);
    border-radius: 14px;
    padding: 1.5rem 2rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 32px rgba(0,120,200,0.18), inset 0 1px 0 rgba(255,255,255,0.06);
    margin-bottom: 0.5rem;
}
.neo-banner h1 {
    font-size: 1.65rem;
    font-weight: 700;
    color: #e8f4fd;
    margin: 0 0 0.25rem 0;
    letter-spacing: -0.4px;
}
.neo-banner p {
    font-size: 0.84rem;
    color: #7ec8e3;
    margin: 0;
}

/* ── Nav button strip ── */
.nav-strip {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 1.2rem;
}
.nav-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0,100,160,0.28);
    border: 1px solid rgba(0,160,210,0.3);
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 0.82rem;
    font-weight: 600;
    color: #7ec8e3 !important;
    text-decoration: none;
    transition: background 0.2s, border-color 0.2s;
    cursor: pointer;
}
.nav-btn:hover {
    background: rgba(0,130,190,0.4);
    border-color: rgba(0,180,220,0.5);
    color: #b8e4f4 !important;
}

/* ── Panel cards ── */
.panel-card {
    background: rgba(4, 30, 54, 0.72) !important;
    border: 1px solid rgba(0, 160, 210, 0.18) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(8px);
    box-shadow: 0 2px 20px rgba(0,80,160,0.15);
}

/* ── Section heading labels ── */
.section-heading {
    font-size: 0.75rem;
    font-weight: 600;
    color: #7ec8e3;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(0,160,210,0.2);
}

/* ── Slider tracks ── */
input[type=range] { accent-color: #0096c7; }

/* ── Dropdown ── */
select, .gr-dropdown select {
    background: rgba(3, 20, 40, 0.85) !important;
    border: 1px solid rgba(0,160,210,0.2) !important;
    color: #d6eaf8 !important;
    border-radius: 8px !important;
}

/* ── Predict button ── */
button.primary, #predict-btn {
    background: linear-gradient(135deg, #005a9e 0%, #007bbd 100%) !important;
    border: none !important;
    border-radius: 9px !important;
    color: #e8f4fd !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.3px;
    box-shadow: 0 3px 18px rgba(0,120,200,0.35) !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}
button.primary:hover, #predict-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 5px 24px rgba(0,140,220,0.45) !important;
}

/* ── Reset button ── */
button.secondary {
    background: rgba(0,80,130,0.22) !important;
    border: 1px solid rgba(0,160,210,0.25) !important;
    border-radius: 9px !important;
    color: #7ec8e3 !important;
    font-weight: 600 !important;
}
button.secondary:hover {
    background: rgba(0,100,160,0.35) !important;
}

/* ── Output result card ── */
.result-card {
    background: rgba(3, 20, 40, 0.82);
    border-radius: 12px;
    border: 1px solid rgba(0,160,210,0.2);
    padding: 1.4rem 1.8rem;
    min-height: 90px;
    color: #e8f4fd;
}
.result-card h3 { color: #a8d8ea; margin-top: 0; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.6px; }
.result-card p  { color: #e8f4fd; margin: 0.4rem 0; font-size: 0.95rem; }
.result-card strong { color: #ffffff; }
.result-hazardous {
    border-left: 4px solid #e05252;
    background: rgba(40, 8, 8, 0.55);
}
.result-safe {
    border-left: 4px solid #00c896;
    background: rgba(0, 30, 20, 0.55);
}

/* ── Markdown output ── */
.gr-prose, .prose { color: #d6eaf8 !important; }
.gr-prose h3 { color: #7ec8e3 !important; margin-top: 0 !important; }
.gr-prose strong { color: #e8f4fd !important; }

/* ── Divider ── */
.sea-hr {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,160,210,0.3) 30%, rgba(0,200,200,0.3) 70%, transparent);
    margin: 1rem 0;
    border: none;
}

/* ── Footer ── */
.neo-footer {
    text-align: center;
    color: #7ba0b8;
    font-size: 0.73rem;
    padding: 1rem 0 0.2rem;
    letter-spacing: 0.3px;
}
"""

# ---------------------------------------------------------------------------
# Navigation HTML snippets
# ---------------------------------------------------------------------------
_BANNER_HTML = """
<div class="neo-banner">
    <h1>☄️ NEO-Sentinel: Prediction Portal</h1>
    <p>Enter asteroid telemetry data to classify its threat level in real time &nbsp;·&nbsp;
    Powered by XGBoost · @champion model via MLflow Registry</p>
</div>
"""

# The dashboard runs on port 8501. In production on HF Spaces the URL pattern
# is different, so we use a relative host approach: JS opens :8501 in a new tab.
_NAV_TO_DASHBOARD_HTML = """
<div class="nav-strip">
    <a class="nav-btn" onclick="window.open(window.location.protocol + '//' + window.location.hostname + ':8501', '_blank')">
        📊 &nbsp; Admin Dashboard →
    </a>
</div>
"""

_FOOTER_HTML = """
<div class="sea-hr"></div>
<div class="neo-footer">
    NEO-Sentinel &nbsp;·&nbsp; Autonomous Asteroid Hazard Classification System &nbsp;·&nbsp;
    XGBoost · MLflow · DagsHub · FastAPI
</div>
"""


# ---------------------------------------------------------------------------
# UI builder
# ---------------------------------------------------------------------------
def build_ui(predictor):

    def predict_interface(mag, min_dia, max_dia, vel, miss, body):
        try:
            features = AsteroidFeatures(
                absolute_magnitude_h=mag,
                estimated_diameter_min_km=min_dia,
                estimated_diameter_max_km=max_dia,
                relative_velocity_kmph=vel,
                miss_distance_km=miss,
                orbiting_body=body,
            )
            is_haz, conf = predictor.predict(features.model_dump())
            if is_haz:
                result_str = "🛑 HAZARDOUS"
                card_class = "result-hazardous"
            else:
                result_str = "✅ SAFE"
                card_class = "result-safe"
            return (
                f'<div class="result-card {card_class}">'
                f"<h3>Prediction Result</h3>"
                f"<p><strong>Status:</strong> {result_str}</p>"
                f"<p><strong>Confidence:</strong> {conf:.2%}</p>"
                f"</div>"
            )
        except Exception as e:
            from pydantic import ValidationError
            if isinstance(e, ValidationError):
                error_msg = "\n".join(
                    [
                        f"- {err['loc'][0]}: {err['msg']}"
                        for err in e.errors()
                        if "loc" in err and len(err["loc"]) > 0
                    ]
                )
                if not error_msg:
                    error_msg = "\n".join([f"- {err['msg']}" for err in e.errors()])
                return (
                    f'<div class="result-card" style="border-left:4px solid #e05252;">'
                    f"<h3>Validation Error</h3>"
                    f"<p>Please check your inputs:</p><pre>{error_msg}</pre>"
                    f"</div>"
                )
            return (
                f'<div class="result-card" style="border-left:4px solid #e05252;">'
                f"<h3>Error</h3><p>{str(e)}</p>"
                f"</div>"
            )

    def reset_interface():
        return 20.0, 0.1, 0.2, 50000, 5000000, "Earth", ""

    with gr.Blocks(
        title="NEO-Sentinel: Prediction Portal",
        theme=gr.themes.Base(),
        css=OCEAN_CSS,
    ) as demo:

        # ── Header ──
        gr.HTML(_BANNER_HTML)
        gr.HTML(_NAV_TO_DASHBOARD_HTML)
        gr.HTML(
            """
            <div style="
                background: rgba(0,100,160,0.12);
                border: 1px solid rgba(0,160,210,0.2);
                border-left: 3px solid #0096c7;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 0.78rem;
                color: #7ec8e3;
                margin-bottom: 0.8rem;
                font-family: 'Inter', sans-serif;
            ">
                ℹ️ &nbsp;<strong style="color:#a8d8ea;">Note:</strong>
                The Admin Dashboard link is available in local Docker deployments.
                In public Hugging Face Spaces, this port (8501) is restricted for security.
            </div>
            """
        )
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML('<div class="section-heading">🔭 &nbsp; Dimensional &amp; Luminous Properties</div>')
                mag = gr.Slider(
                    0, 50, value=20.0,
                    label="Absolute Magnitude (H) — Brightness Proxy",
                )
                min_dia = gr.Slider(
                    0, 50.0, step=0.01, value=0.1,
                    label="Min Estimated Diameter (km)",
                )
                max_dia = gr.Slider(
                    0, 50.0, step=0.01, value=0.2,
                    label="Max Estimated Diameter (km)",
                )

            with gr.Column(scale=1):
                gr.HTML('<div class="section-heading">🌊 &nbsp; Trajectory Properties</div>')
                vel = gr.Slider(
                    0, 150000, step=100, value=50000,
                    label="Relative Velocity (km/h)",
                )
                miss = gr.Slider(
                    0, 10_000_000, step=1000, value=5_000_000,
                    label="Miss Distance (km)",
                )
                body = gr.Dropdown(
                    choices=["Earth"], value="Earth",
                    label="Orbiting Body",
                )

        # ── Action buttons ──
        with gr.Row():
            btn = gr.Button("⚡ Classify Threat", variant="primary", elem_id="predict-btn")
            reset_btn = gr.Button("↺ Reset", variant="secondary")

        # ── Result output ──
        out = gr.HTML(
            value='<div class="result-card"><p style="color:#4a6878;font-size:0.85rem;">Run a classification to see the result here.</p></div>'
        )

        btn.click(
            fn=predict_interface,
            inputs=[mag, min_dia, max_dia, vel, miss, body],
            outputs=out,
        )
        reset_btn.click(
            fn=reset_interface,
            inputs=[],
            outputs=[mag, min_dia, max_dia, vel, miss, body, out],
        )

        # ── Footer ──
        gr.HTML(_FOOTER_HTML)

    return demo
