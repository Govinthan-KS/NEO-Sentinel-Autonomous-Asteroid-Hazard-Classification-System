import { motion } from "framer-motion";

export interface ShapFeature {
  name: string;
  value: number;
}

interface ShapBarsProps {
  features: ShapFeature[];
}

export function ShapBars({ features }: ShapBarsProps) {
  // Map features to clean their names and invert their values for display
  // Safe = Positive (points right, blue/lime), Hazardous = Negative (points left, red)
  const displayFeatures = features.map(f => ({
    name: f.name.replace(/^(num__|cat__)/, ''),
    value: f.value * -1
  }));

  // Use a fixed log-odds scale from -2.0 to +2.0 for consistency
  const SCALE_MAX = 2.0;

  return (
    <div className="w-full relative py-4">
      {/* Background Grid Lines */}
      <div className="absolute inset-0 z-0 pointer-events-none mt-4">
        <div className="absolute top-0 bottom-8 left-[5%] w-px border-l border-dashed border-[rgba(150,190,255,0.05)]"></div>
        <div className="absolute top-0 bottom-8 left-[27.5%] w-px border-l border-dashed border-[rgba(150,190,255,0.05)]"></div>
        <div className="absolute top-0 bottom-8 left-[50%] w-px bg-[rgba(150,190,255,0.2)]"></div>
        <div className="absolute top-0 bottom-8 left-[72.5%] w-px border-l border-dashed border-[rgba(150,190,255,0.05)]"></div>
        <div className="absolute top-0 bottom-8 left-[95%] w-px border-l border-dashed border-[rgba(150,190,255,0.05)]"></div>
      </div>

      <div className="flex flex-col gap-3 relative z-10">
        {displayFeatures.map((feature, i) => {
          const isPositive = feature.value >= 0;
          // Scale bar width up to ~45% of container so it doesn't touch the edge
          // Cap at 45% just in case a log-odds value exceeds 2.0
          const widthPercent = Math.min((Math.abs(feature.value) / SCALE_MAX) * 45, 45);
          const barColor = isPositive ? "var(--primary)" : "var(--hazard-red)";

          return (
            <div key={feature.name} className="flex items-center w-full relative h-7">
              {/* Left side (negative) */}
              <div className="flex-1 flex justify-end items-center pr-2.5 gap-2.5 min-w-0">
                {!isPositive && (
                  <>
                    <span className="text-[13px] font-mono font-medium text-[#eef3ff] truncate drop-shadow-md" title={feature.name}>
                      {feature.name}
                    </span>
                    <span className="text-xs font-mono font-bold opacity-90 shrink-0" style={{ color: barColor }}>
                      {feature.value.toFixed(3)}
                    </span>
                    <motion.div
                      className="h-2.5 rounded-l-sm"
                      style={{ backgroundColor: barColor, filter: `drop-shadow(0 0 6px ${barColor})` }}
                      initial={{ width: 0 }}
                      animate={{ width: `${widthPercent}%` }}
                      transition={{ delay: i * 0.1, duration: 0.5, ease: "easeOut" }}
                    />
                  </>
                )}
                {isPositive && (
                  <span className="text-[13px] font-mono font-medium text-[#eef3ff] truncate text-right w-full block drop-shadow-md" title={feature.name}>
                    {feature.name}
                  </span>
                )}
              </div>

              {/* Center spacer */}
              <div className="w-1.5 z-20"></div>

              {/* Right side (positive) */}
              <div className="flex-1 flex justify-start items-center pl-2.5 gap-2.5 min-w-0">
                {isPositive && (
                  <>
                    <motion.div
                      className="h-2.5 rounded-r-sm"
                      style={{ backgroundColor: barColor, filter: `drop-shadow(0 0 6px ${barColor})` }}
                      initial={{ width: 0 }}
                      animate={{ width: `${widthPercent}%` }}
                      transition={{ delay: i * 0.1, duration: 0.5, ease: "easeOut" }}
                    />
                    <span className="text-xs font-mono font-bold opacity-90 shrink-0" style={{ color: barColor }}>
                      +{feature.value.toFixed(3)}
                    </span>
                    <span className="text-[13px] font-mono font-medium text-[#eef3ff] truncate drop-shadow-md" title={feature.name}>
                      {feature.name}
                    </span>
                  </>
                )}
                {!isPositive && (
                  <span className="text-[13px] font-mono font-medium text-[#eef3ff] truncate text-left w-full block drop-shadow-md" title={feature.name}>
                    {feature.name}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* X-Axis Scale */}
      <div className="relative mt-6 h-6 border-t border-[rgba(150,190,255,0.15)] text-[11px] font-mono text-[#8fa3c8] font-medium">
        <div className="absolute left-[5%] -translate-x-1/2 mt-2">-2.0</div>
        <div className="absolute left-[27.5%] -translate-x-1/2 mt-2">-1.0</div>
        <div className="absolute left-[50%] -translate-x-1/2 mt-2 text-white">0.0</div>
        <div className="absolute left-[72.5%] -translate-x-1/2 mt-2">+1.0</div>
        <div className="absolute left-[95%] -translate-x-1/2 mt-2">+2.0</div>
        
        {/* Tick marks */}
        <div className="absolute left-[5%] top-[-1px] w-px h-2 bg-[rgba(150,190,255,0.3)]"></div>
        <div className="absolute left-[27.5%] top-[-1px] w-px h-2 bg-[rgba(150,190,255,0.3)]"></div>
        <div className="absolute left-[50%] top-[-1px] w-px h-2.5 bg-[rgba(150,190,255,0.5)]"></div>
        <div className="absolute left-[72.5%] top-[-1px] w-px h-2 bg-[rgba(150,190,255,0.3)]"></div>
        <div className="absolute left-[95%] top-[-1px] w-px h-2 bg-[rgba(150,190,255,0.3)]"></div>
      </div>
    </div>
  );
}
