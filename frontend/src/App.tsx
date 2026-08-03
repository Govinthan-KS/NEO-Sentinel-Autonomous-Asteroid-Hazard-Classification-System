import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { Home } from './pages/Home';
import { Predict } from './pages/Predict';
import { Dashboard } from './pages/Dashboard';
import { About } from './pages/About';
import { PrivacyPolicy } from './pages/PrivacyPolicy';
import { TermsOfService } from './pages/TermsOfService';
import { License } from './pages/License';
import { Contact } from './pages/Contact';

import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import { Login } from './pages/Login';
import { Profile } from './pages/Profile';

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route 
          path="/" 
          element={
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
              <Home />
            </motion.div>
          } 
        />
        <Route 
          path="/login" 
          element={
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
              <Login />
            </motion.div>
          } 
        />
        <Route 
          path="/about" 
          element={
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
              <About />
            </motion.div>
          } 
        />
        <Route 
          path="/predict" 
          element={
            <ProtectedRoute>
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
                <Predict />
              </motion.div>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
                <Dashboard />
              </motion.div>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/profile" 
          element={
            <ProtectedRoute>
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
                <Profile />
              </motion.div>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/privacy" 
          element={
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
              <PrivacyPolicy />
            </motion.div>
          } 
        />
        <Route 
          path="/terms" 
          element={
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
              <TermsOfService />
            </motion.div>
          } 
        />
        <Route 
          path="/license" 
          element={
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
              <License />
            </motion.div>
          } 
        />
        <Route 
          path="/contact" 
          element={
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
              <Contact />
            </motion.div>
          } 
        />
      </Routes>
    </AnimatePresence>
  );
}

import { Toaster } from 'sonner';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Toaster 
          position="top-right" 
          duration={4000}
          closeButton
          toastOptions={{
            style: {
              background: 'rgba(238, 242, 246, 0.85)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255, 255, 255, 0.5)',
              color: '#0f172a',
              boxShadow: '0 8px 32px rgba(0,0,0,0.2), inset 0 0 0 1px rgba(255,255,255,0.2)',
            },
            classNames: {
              toast: 'group !rounded-xl !p-4 !pr-10',
              title: '!text-[14px] !font-bold',
              description: '!text-[#475569] !text-[13px]',
              closeButton: '!absolute !left-auto !right-1.5 !top-1.5 !bg-transparent !border-none !text-[#64748b] hover:!bg-[rgba(0,0,0,0.06)] hover:!text-[#0f172a] !transition-all !w-7 !h-7 flex items-center justify-center !rounded-md',
            },
          }}
        />
        <AnimatedRoutes />
      </Router>
    </AuthProvider>
  );
}

export default App;
