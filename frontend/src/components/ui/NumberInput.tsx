import { ChevronUp, ChevronDown } from 'lucide-react';

interface NumberInputProps {
  value: number | '';
  onChange: (val: number | '') => void;
  step?: number;
  min?: number;
  max?: number;
  placeholder?: string;
  className?: string;
}

export function NumberInput({ value, onChange, step = 1, min, max, placeholder, className = '' }: NumberInputProps) {
  const handleIncrement = () => {
    const current = value === '' ? 0 : value;
    const next = current + step;
    if (max !== undefined && next > max) return;
    // Fix floating point precision issues for small steps
    const precision = step.toString().split('.')[1]?.length || 0;
    onChange(Number(next.toFixed(precision)));
  };

  const handleDecrement = () => {
    const current = value === '' ? 0 : value;
    const next = current - step;
    if (min !== undefined && next < min) return;
    const precision = step.toString().split('.')[1]?.length || 0;
    onChange(Number(next.toFixed(precision)));
  };

  return (
    <div className={`relative flex items-center min-h-[44px] bg-[rgba(12,16,28,0.6)] backdrop-blur-md border border-[rgba(150,190,255,0.2)] rounded-lg transition-colors hover:border-[rgba(90,200,250,0.5)] shadow-inner group focus-within:border-primary-bright ${className}`}>
      <input
        type="number"
        value={value}
        step={step}
        min={min}
        max={max}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))}
        className="w-full bg-transparent px-3.5 py-2 text-[13px] text-[#eef3ff] font-mono outline-none placeholder:text-[#5c6f94] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
      />
      <div className="absolute right-2 flex flex-col items-center justify-center opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
        <button 
          onClick={handleIncrement}
          className="text-[#8fa3c8] hover:text-primary-bright p-0.5 rounded transition-colors"
          type="button"
          tabIndex={-1}
        >
          <ChevronUp size={12} strokeWidth={3} />
        </button>
        <button 
          onClick={handleDecrement}
          className="text-[#8fa3c8] hover:text-primary-bright p-0.5 rounded transition-colors"
          type="button"
          tabIndex={-1}
        >
          <ChevronDown size={12} strokeWidth={3} />
        </button>
      </div>
    </div>
  );
}
