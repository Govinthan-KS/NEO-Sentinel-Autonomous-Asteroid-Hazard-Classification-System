import { useState, useEffect } from 'react';
import { Navbar } from '../components/layout/Navbar';
import { Footer } from '../components/layout/Footer';
import { AnimatedBackground } from '../components/layout/AnimatedBackground';
import { GlassCard } from '../components/ui/GlassCard';
import { useAuth } from '../context/AuthContext';
import { showSuccessToast, handleApiError, showWarningToast } from '../utils/toast';
import { motion } from 'framer-motion';

export function Contact() {
  const { session, user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
    honeypot: ''
  });

  // Pre-fill user data if logged in
  useEffect(() => {
    if (user) {
      setForm(prev => ({
        ...prev,
        name: user.user_metadata?.full_name || prev.name,
        email: user.email || prev.email
      }));
    }
  }, [user]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;

    // Basic validation
    if (!form.name || !form.email || !form.subject || !form.message) {
      showWarningToast('Missing Fields', 'Please fill out all required fields.');
      return;
    }

    setLoading(true);

    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:7860';
      
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      };
      
      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`;
      }

      const res = await fetch(`${baseUrl}/contact`, {
        method: 'POST',
        headers,
        body: JSON.stringify(form)
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => null);
        throw new Error(errorData?.detail || 'Failed to send message.');
      }

      showSuccessToast('Message Sent', "We've received your message. Our team will review it and follow up if necessary.");
      
      // Reset form but keep name/email if logged in
      setForm(prev => ({
        ...prev,
        subject: '',
        message: '',
        honeypot: ''
      }));

    } catch (err: any) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden bg-[#02040a]">
      <AnimatedBackground />
      <Navbar />

      <main className="flex-1 w-full max-w-[600px] mx-auto px-6 pt-32 pb-24 relative z-10 flex flex-col justify-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full"
        >
          <div className="text-center mb-10">
            <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight mb-3">
              Contact Support
            </h1>
            <p className="text-[#8fa3c8] text-sm md:text-base">
              Have a question about the classification models or need technical assistance? Drop us a message.
            </p>
          </div>

          <GlassCard className="p-8">
            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
              
              {/* Invisible Honeypot */}
              <div style={{ display: 'none' }}>
                <label>Leave this field blank</label>
                <input type="text" name="honeypot" value={form.honeypot} onChange={handleChange} tabIndex={-1} autoComplete="off" />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <label className="flex flex-col gap-1.5">
                  <span className="text-xs text-muted-secondary font-medium">Name</span>
                  <input 
                    type="text" 
                    name="name"
                    value={form.name}
                    onChange={handleChange}
                    readOnly={!!user}
                    className={`min-h-[44px] border rounded-lg px-4 py-2.5 text-white text-sm focus:border-accent-lime focus:outline-none transition-colors ${user ? 'bg-[rgba(5,7,13,0.4)] border-[rgba(150,190,255,0.1)] text-[#5c6f94] cursor-not-allowed' : 'bg-[rgba(5,7,13,0.6)] border-[rgba(150,190,255,0.15)]'}`}
                    placeholder="Jane Doe"
                    required
                  />
                </label>

                <label className="flex flex-col gap-1.5">
                  <span className="text-xs text-muted-secondary font-medium">Email</span>
                  <input 
                    type="email" 
                    name="email"
                    value={form.email}
                    onChange={handleChange}
                    readOnly={!!user}
                    className={`min-h-[44px] border rounded-lg px-4 py-2.5 text-white text-sm focus:border-accent-lime focus:outline-none transition-colors ${user ? 'bg-[rgba(5,7,13,0.4)] border-[rgba(150,190,255,0.1)] text-[#5c6f94] cursor-not-allowed' : 'bg-[rgba(5,7,13,0.6)] border-[rgba(150,190,255,0.15)]'}`}
                    placeholder="jane@example.com"
                    required
                  />
                </label>
              </div>

              <label className="flex flex-col gap-1.5">
                <span className="text-xs text-muted-secondary font-medium">Subject</span>
                <input 
                  type="text" 
                  name="subject"
                  value={form.subject}
                  onChange={handleChange}
                  className="min-h-[44px] bg-[rgba(5,7,13,0.6)] border border-[rgba(150,190,255,0.15)] rounded-lg px-4 py-2.5 text-white text-sm focus:border-accent-lime focus:outline-none transition-colors"
                  placeholder="How can we help?"
                  required
                />
              </label>

              <label className="flex flex-col gap-1.5">
                <span className="text-xs text-muted-secondary font-medium">Message</span>
                <textarea 
                  name="message"
                  value={form.message}
                  onChange={handleChange}
                  rows={5}
                  className="bg-[rgba(5,7,13,0.6)] border border-[rgba(150,190,255,0.15)] rounded-lg px-4 py-3 text-white text-sm focus:border-accent-lime focus:outline-none transition-colors resize-none"
                  placeholder="Enter your message here..."
                  required
                />
              </label>

              <button 
                type="submit"
                disabled={loading}
                className={`mt-4 min-h-[44px] w-full py-3.5 rounded-xl flex items-center justify-center gap-2 bg-gradient-to-br from-[rgba(90,200,250,0.25)] to-[rgba(163,230,53,0.18)] border border-[rgba(150,190,255,0.4)] shadow-[0_0_24px_rgba(90,200,250,0.15)] text-text-primary font-bold text-sm hover:scale-[1.02] active:scale-[0.98] transition-all ${loading ? 'opacity-50 cursor-wait pointer-events-none' : ''}`}
              >
                {loading && (
                  <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                {loading ? 'Sending Message...' : 'Send Message'}
              </button>
            </form>
          </GlassCard>
        </motion.div>
      </main>

      <Footer />
    </div>
  );
}
