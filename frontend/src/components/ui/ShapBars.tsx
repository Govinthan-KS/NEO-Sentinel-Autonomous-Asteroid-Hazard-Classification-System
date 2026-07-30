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

  // Find max absolute value to scale the bars proportionally
  const maxAbsValue = Math.max(...displayFeatures.map(f => Math.abs(f.value)), 0.01);

  return (
    <div className="w-full relative py-4">
      {/* Center line */}
      <div className="absolute top-0 bottom-0 left-1/2 w-px bg-[rgba(150,190,255,0.2)] z-0"></div>

      <div className="flex flex-col gap-3 relative z-10">
        {displayFeatures.map((feature, i) => {
          const isPositive = feature.value >= 0;
          // Scale bar width up to ~45% of container so it doesn't touch the edge
          const widthPercent = (Math.abs(feature.value) / maxAbsValue) * 45;
          const barColor = isPositive ? "var(--primary)" : "var(--hazard-red)";

          return (
            <div key={feature.name} className="flex items-center w-full relative h-6">
              {/* Left side (negative) */}
              <div className="flex-1 flex justify-end items-center pr-2 gap-2 overflow-visible">
                {!isPositive && (
                  <>
                    <span className="text-xs font-mono text-[#c7d3ee] whitespace-nowrap">
                      {feature.name}
                    </span>
                    <span className="text-[10px] font-mono opacity-80" style={{ color: barColor }}>
                      {feature.value.toFixed(3)}
                    </span>
                    <motion.div
                      className="h-2 rounded-l-sm"
                      style={{ backgroundColor: barColor, filter: `drop-shadow(0 0 4px ${barColor})` }}
                      initial={{ width: 0 }}
                      animate={{ width: `${widthPercent}%` }}
                      transition={{ delay: i * 0.1, duration: 0.5, ease: "easeOut" }}
                    />
                  </>
                )}
                {isPositive && (
                  <span className="text-xs font-mono text-[#c7d3ee] whitespace-nowrap">
                    {feature.name}
                  </span>
                )}
              </div>

              {/* Center spacer */}
              <div className="w-1"></div>

              {/* Right side (positive) */}
              <div className="flex-1 flex justify-start items-center pl-2 gap-2 overflow-visible">
                {isPositive && (
                  <>
                    <motion.div
                      className="h-2 rounded-r-sm"
                      style={{ backgroundColor: barColor, filter: `drop-shadow(0 0 4px ${barColor})` }}
                      initial={{ width: 0 }}
                      animate={{ width: `${widthPercent}%` }}
                      transition={{ delay: i * 0.1, duration: 0.5, ease: "easeOut" }}
                    />
                    <span className="text-[10px] font-mono opacity-80" style={{ color: barColor }}>
                      +{feature.value.toFixed(3)}
                    </span>
                    <span className="text-xs font-mono text-[#c7d3ee] whitespace-nowrap">
                      {feature.name}
                    </span>
                  </>
                )}
                {!isPositive && (
                  <span className="text-xs font-mono text-[#c7d3ee] whitespace-nowrap">
                    {feature.name}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
