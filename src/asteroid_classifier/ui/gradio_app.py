import gradio as gr
from asteroid_classifier.api.schemas import AsteroidFeatures

def build_ui(predictor):
    
    def predict_interface(mag, min_dia, max_dia, vel, miss, body):
        try:
            features = AsteroidFeatures(
                absolute_magnitude_h=mag,
                estimated_diameter_min_km=min_dia,
                estimated_diameter_max_km=max_dia,
                relative_velocity_kmph=vel,
                miss_distance_km=miss,
                orbiting_body=body
            )
            # Directly call predictor logic to avoid local network overhead
            is_haz, conf = predictor.predict(features.model_dump())
            result_str = "🛑 HAZARDOUS" if is_haz else "✅ SAFE"
            return f"### Prediction Result\n\n**Status**: {result_str}\n\n**Confidence**: {conf:.2%}"
        except Exception as e:
            from pydantic import ValidationError
            if isinstance(e, ValidationError):
                error_msg = "\n".join([f"- {err['loc'][0]}: {err['msg']}" for err in e.errors() if 'loc' in err and len(err['loc']) > 0])
                if not error_msg:
                    error_msg = "\n".join([f"- {err['msg']}" for err in e.errors()])
                return f"### Validation Error\n\n**Please check your inputs:**\n{error_msg}"
            return f"### Error\n\nFailed to process prediction: {str(e)}"

    def reset_interface():
        return 20.0, 0.1, 0.2, 50000, 5000000, "Earth", ""

    with gr.Blocks(title="Asteroid Hazard Classifier", theme=gr.themes.Monochrome()) as demo:
        gr.Markdown("# ☄️ Asteroid Hazard Classifier Dashboard")
        gr.Markdown("Enter the physical metrics of a Near-Earth Object (NEO) to classify its threat level. This model predicts if the asteroid is **Potentially Hazardous** based on NASA telemetry data.")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Dimensional & Luminous Properties")
                mag = gr.Slider(0, 50, value=20.0, label="Absolute Magnitude (H) - Brightness Proxy")
                min_dia = gr.Slider(0, 50.0, step=0.01, value=0.1, label="Min Estimated Diameter (km)")
                max_dia = gr.Slider(0, 50.0, step=0.01, value=0.2, label="Max Estimated Diameter (km)")
                
            with gr.Column(scale=1):
                gr.Markdown("### Trajectory Properties")
                vel = gr.Slider(0, 150000, step=100, value=50000, label="Relative Velocity (km/h)")
                miss = gr.Slider(0, 10000000, step=1000, value=5000000, label="Miss Distance (km)")
                body = gr.Dropdown(choices=["Earth"], value="Earth", label="Orbiting Body")
                
        with gr.Row():
            btn = gr.Button("Predict Hazard Status", variant="primary")
            reset_btn = gr.Button("Reset", variant="secondary")
            
        with gr.Row():
            out = gr.Markdown(label="Output")
            
        btn.click(fn=predict_interface, inputs=[mag, min_dia, max_dia, vel, miss, body], outputs=out)
        reset_btn.click(fn=reset_interface, inputs=[], outputs=[mag, min_dia, max_dia, vel, miss, body, out])
        
    return demo
