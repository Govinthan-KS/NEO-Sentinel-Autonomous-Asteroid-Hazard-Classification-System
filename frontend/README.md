# NEO-Sentinel Frontend

Operational Dashboard and Prediction interface for the Asteroid Hazard Classifier system.
Built with Vite, React, TypeScript, Tailwind CSS, and Recharts.

## Getting Started

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment:**
   Copy `.env.example` to `.env` and set the backend URL:
   ```env
   VITE_API_BASE_URL=http://localhost:7860
   ```
   *(If running the backend locally via `uvicorn main:app --port 7860`, use the default above.)*

3. **Run local dev server:**
   ```bash
   npm run dev
   ```
   The app will start at `http://localhost:5173`.

## Deployment (Vercel)

This frontend is configured as a standard Vite React application and is ready to be deployed to Vercel.

1. Connect the repository to Vercel.
2. Select **Vite** as the Framework Preset.
3. Add the `VITE_API_BASE_URL` Environment Variable in the Vercel project settings, pointing to your deployed FastAPI backend URL.
4. Deploy!
