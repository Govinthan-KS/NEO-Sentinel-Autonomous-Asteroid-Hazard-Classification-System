import { motion } from 'framer-motion';

interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
}

export function Switch({ checked, onChange, label }: SwitchProps) {
  return (
    <div 
      className="flex items-center gap-3 cursor-pointer"
      onClick={() => onChange(!checked)}
    >
      <div 
        className={`relative w-10 h-5.5 rounded-full transition-colors duration-300 ease-in-out border ${
          checked 
            ? 'bg-[rgba(163,230,53,0.2)] border-[rgba(163,230,53,0.5)] shadow-[0_0_15px_rgba(163,230,53,0.15)]' 
            : 'bg-[rgba(12,16,28,0.6)] border-[rgba(150,190,255,0.2)]'
        }`}
      >
        <motion.div
          className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full shadow-md ${
            checked ? 'bg-accent-lime shadow-[0_0_8px_var(--accent-lime)]' : 'bg-[#8fa3c8]'
          }`}
          animate={{ x: checked ? 18 : 0 }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        />
      </div>
      {label && (
        <span className={`text-[13px] font-mono select-none transition-colors ${checked ? 'text-accent-lime font-bold' : 'text-[#c7d3ee]'}`}>
          {label}
        </span>
      )}
    </div>
  );
}
