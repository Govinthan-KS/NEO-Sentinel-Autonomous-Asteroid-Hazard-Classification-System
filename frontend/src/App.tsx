import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { Home } from './pages/Home';
import { Predict } from './pages/Predict';
import { Dashboard } from './pages/Dashboard';
import { About } from './pages/About';
import { PrivacyPolicy } from './pages/PrivacyPolicy';
import { TermsOfService } from './pages/TermsOfService';

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
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
              <Predict />
            </motion.div>
          } 
        />
        <Route 
          path="/dashboard" 
          element={
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
              <Dashboard />
            </motion.div>
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
      </Routes>
    </AnimatePresence>
  );
}

import { Toaster } from 'sonner';

function App() {
  return (
    <Router>
      <Toaster 
        position="top-right" 
        duration={4000}
        closeButton
        toastOptions={{
          style: {
            background: 'rgba(9, 13, 22, 0.95)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: '#f1f5f9',
          },
          className: 'text-slate-100',
          descriptionClassName: 'text-slate-400',
        }}
      />
      <AnimatedRoutes />
    </Router>
  );
}

export default App;
