import { motion } from "framer-motion";

interface AnimatedGaugeProps {
  value: number; // 0 to 1
  size?: number;
  strokeWidth?: number;
  color?: string;
  label?: string;
}

export function AnimatedGauge({ 
  value, 
  size = 120, 
  strokeWidth = 10,
  color = "var(--hazard-red)",
  label
}: AnimatedGaugeProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDashoffset = circumference - value * circumference;

  return (
    <div className="relative flex flex-col items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-[rgba(150,190,255,0.1)]"
        />
        {/* Progress circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1, ease: "easeOut" }}
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 8px ${color})` }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center text-center">
        <span className="font-mono text-2xl font-bold text-text-primary">
          {Math.round(value * 100)}%
        </span>
        {label && (
          <span className="text-[10px] uppercase tracking-wider text-muted-secondary mt-1">
            {label}
          </span>
        )}
      </div>
    </div>
  );
}
