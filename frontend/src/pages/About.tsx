import { motion } from 'framer-motion';
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { AnimatedBackground } from "@/components/layout/AnimatedBackground";
import { ArchitectureFlowchart } from "@/components/ui/ArchitectureFlowchart";

export function About() {
  return (
    <div className="relative min-h-screen bg-background overflow-hidden flex flex-col font-sans">
      <AnimatedBackground />
      <Navbar />

      <main className="flex-1 relative z-10 flex flex-col items-center pt-[100px] pb-20 px-6">
        <div className="w-full max-w-[1000px] flex flex-col gap-12">
          
          <section>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4 text-[#eef3ff]">
                About NEO-Sentinel
              </h1>
              
              <div className="bg-[rgba(150,190,255,0.05)] border border-[rgba(150,190,255,0.15)] rounded-xl p-6 mb-8">
                <p className="text-[19px] leading-[1.5] font-semibold m-0 mb-4 text-text-primary">
                  "A Multi-Model Approach Using XAI and Anomaly Detection to Predict Asteroid Hazards"
                </p>
                <p className="text-sm leading-[1.65] text-muted-secondary m-0">
                  Introduced a multi-model classification approach paired with SHAP-based explainability and unsupervised anomaly detection for identifying potentially hazardous asteroids.
                </p>
              </div>

              <div className="prose prose-invert max-w-none text-text-secondary leading-relaxed">
                <p className="mb-4">
                  NEO-Sentinel combines a multi-model ensemble with explainable AI and anomaly detection to flag Potentially Hazardous Asteroids — with the reasoning behind every call, not just a verdict.
                </p>
                <p className="mb-4">
                  XGBoost, LightGBM and Random Forest candidates are trained continuously; the strongest performer is promoted to champion. The entire MLOps pipeline lifecycle ensures that models are robustly evaluated on fresh telemetry data and only deployed if they meet strict performance thresholds.
                </p>
              </div>
            </motion.div>
          </section>

          <section>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <h2 className="text-2xl font-bold mb-8 text-[#eef3ff] border-b border-[rgba(150,190,255,0.1)] pb-4">
                System Architecture
              </h2>
              <div className="flex justify-center w-full">
                <ArchitectureFlowchart />
              </div>
            </motion.div>
          </section>

        </div>
      </main>

      <Footer />
    </div>
  );
}
