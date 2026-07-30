import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface Option {
  label: string;
  value: string;
}

interface SelectProps {
  value: string;
  options: Option[];
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export function Select({ value, options, onChange, placeholder = 'Select...', className = '' }: SelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setIsOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const selectedOption = options.find(o => o.value === value);

  return (
    <div className={`relative ${className}`} ref={ref}>
      <div 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full bg-[rgba(12,16,28,0.6)] backdrop-blur-md border border-[rgba(150,190,255,0.2)] hover:border-[rgba(90,200,250,0.5)] rounded-lg px-3.5 py-2 cursor-pointer transition-colors shadow-inner"
      >
        <span className={`text-[13px] font-mono ${selectedOption ? 'text-[#eef3ff]' : 'text-[#5c6f94]'}`}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronDown size={14} className={`text-[#8fa3c8] transition-transform duration-300 ${isOpen ? 'rotate-180 text-primary-bright' : ''}`} />
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            transition={{ duration: 0.15 }}
            className="absolute left-0 right-0 top-[calc(100%+6px)] bg-[rgba(12,16,28,0.95)] backdrop-blur-xl border border-[rgba(150,190,255,0.2)] rounded-lg shadow-[0_10px_40px_rgba(0,0,0,0.5)] z-50 overflow-hidden"
          >
            {options.map((opt) => (
              <div
                key={opt.value}
                onClick={() => { onChange(opt.value); setIsOpen(false); }}
                className={`px-3.5 py-2.5 text-[13px] font-mono cursor-pointer transition-colors ${
                  opt.value === value 
                    ? 'bg-[rgba(90,200,250,0.15)] text-primary-bright font-bold border-l-2 border-primary-bright' 
                    : 'text-[#c7d3ee] hover:bg-[rgba(150,190,255,0.08)] border-l-2 border-transparent'
                }`}
              >
                {opt.label}
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
