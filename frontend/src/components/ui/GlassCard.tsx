import React from 'react';
import { cn } from '@/lib/utils'; // if not present, I'll create it

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export function GlassCard({ children, className, ...props }: GlassCardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-[rgba(150,190,255,0.14)] bg-[rgba(120,170,255,0.06)] backdrop-blur-md",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
