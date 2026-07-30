import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { AnimatedBackground } from "@/components/layout/AnimatedBackground";

export function PrivacyPolicy() {
  return (
    <div className="relative min-h-screen bg-background overflow-hidden flex flex-col font-sans">
      <AnimatedBackground />
      <Navbar />

      <main className="flex-1 relative z-10 flex flex-col items-center pt-[100px] pb-20 px-6">
        <div className="w-full max-w-[800px] flex flex-col gap-8 bg-[rgba(150,190,255,0.02)] border border-[rgba(150,190,255,0.08)] rounded-2xl p-10 shadow-2xl backdrop-blur-sm">
          
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-[#eef3ff] border-b border-[rgba(150,190,255,0.1)] pb-6 mb-4">
            Privacy Policy
          </h1>

          <div className="prose prose-invert max-w-none text-text-secondary leading-relaxed space-y-6">
            <p>
              Last updated: July 2026
            </p>
            
            <h2 className="text-xl font-bold text-[#eef3ff] mt-8 mb-4">1. Information We Collect</h2>
            <p>
              NEO-Sentinel is an academic and research-oriented open-source project. We do not require users to create accounts, and we do not collect personal identifiable information (PII) such as names, email addresses, or physical locations during standard browsing of the dashboard.
            </p>

            <h2 className="text-xl font-bold text-[#eef3ff] mt-8 mb-4">2. Telemetry and Analytics</h2>
            <p>
              When utilizing the public API endpoints or the dashboard, standard web server logs (such as IP addresses and browser user-agent strings) may be temporarily captured for security, rate-limiting, and diagnostic purposes. We do not use third-party tracking scripts or advertising cookies.
            </p>

            <h2 className="text-xl font-bold text-[#eef3ff] mt-8 mb-4">3. External Data Sources</h2>
            <p>
              This application interfaces directly with the NASA Near Earth Object Web Service (NeoWs) API. User inputs submitted via the "Predict" page to simulate asteroid parameters are processed locally or via our backend models, but are not permanently retained unless explicitly stated.
            </p>

            <h2 className="text-xl font-bold text-[#eef3ff] mt-8 mb-4">4. Open Source and Contributions</h2>
            <p>
              Code contributions, issues, and pull requests submitted to the GitHub repository are subject to GitHub's Privacy Policy. Any data committed to the public repository becomes publicly accessible.
            </p>

            <h2 className="text-xl font-bold text-[#eef3ff] mt-8 mb-4">5. Contact</h2>
            <p>
              If you have any questions regarding this Privacy Policy or the academic use of this tool, please open an issue in the project's GitHub repository.
            </p>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
