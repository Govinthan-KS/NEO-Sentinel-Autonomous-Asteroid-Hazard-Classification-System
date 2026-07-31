import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { AnimatedBackground } from "@/components/layout/AnimatedBackground";

export function TermsOfService() {
  return (
    <div className="relative min-h-screen bg-background overflow-hidden flex flex-col font-sans">
      <AnimatedBackground />
      <Navbar />

      <main className="flex-1 relative z-10 flex flex-col items-center pt-[100px] pb-20 px-6">
        <div className="w-full max-w-[800px] flex flex-col gap-8 bg-[rgba(150,190,255,0.02)] border border-[rgba(150,190,255,0.08)] rounded-2xl p-10 shadow-2xl backdrop-blur-sm">
          
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-[#eef3ff] border-b border-[rgba(150,190,255,0.1)] pb-6 mb-4">
            Terms of Service
          </h1>

          <div className="prose prose-invert max-w-none text-text-secondary leading-relaxed space-y-6">
            <p>
              Last updated: July 2026
            </p>
            
            <h2 className="text-xl font-bold text-[#eef3ff] mt-8 mb-4">1. Acceptance of Terms</h2>
            <p>
              By accessing and using the NEO-Sentinel web application and its associated APIs, you accept and agree to be bound by the terms and provision of this agreement. This tool is provided strictly for academic, research, and educational purposes.
            </p>

            <h2 className="text-xl font-bold text-[#eef3ff] mt-8 mb-4">2. Disclaimer of Warranties (Not for Mission-Critical Use)</h2>
            <p>
              NEO-Sentinel is an experimental machine learning system. The hazard classifications, predictions, and anomaly detection scores provided by this software are NOT validated by the Planetary Defense Coordination Office (PDCO) or any other space agency. 
              <strong> You must not rely on this system for real-world planetary defense decisions, spacecraft navigation, or any life-critical applications.</strong> 
              The software is provided "AS IS", without warranty of any kind, express or implied.
            </p>

            <h2 className="text-xl font-bold text-[#eef3ff] mt-8 mb-4">3. Fair Use, API Abuse, and Scraping</h2>
            <p>
              If you utilize the FastAPI serving endpoints associated with NEO-Sentinel, you agree to do so responsibly. The following behaviors are strictly prohibited and may result in a permanent IP ban:
            </p>
            <ul className="list-disc pl-5 mt-2 space-y-1">
              <li><strong>Rate Limits:</strong> Exceeding the stated rate limits or attempting to bypass rate limiting controls.</li>
              <li><strong>Automated Scraping:</strong> Mass scraping of prediction endpoints or dashboard data without prior written authorization.</li>
              <li><strong>Denial of Service:</strong> Intentionally submitting malformed payloads or overwhelmingly large concurrent requests designed to degrade server performance.</li>
            </ul>

            <h2 className="text-xl font-bold text-[#eef3ff] mt-8 mb-4">4. Intellectual Property</h2>
            <p>
              The source code of NEO-Sentinel is open-source. The telemetry data ingested by this application is the intellectual property of the NASA Jet Propulsion Laboratory (JPL) Center for Near Earth Object Studies (CNEOS). We claim no ownership over the raw NASA NeoWs datasets.
            </p>

            <h2 className="text-xl font-bold text-[#eef3ff] mt-8 mb-4">5. Service Availability and Modifications</h2>
            <p>
              We provide no Service Level Agreement (SLA) for uptime. We reserve the right to modify, suspend, or discontinue the service (or any part thereof) at any time, with or without notice, particularly concerning model registry resets, maintenance windows, or infrastructure changes on the hosted platform.
            </p>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
