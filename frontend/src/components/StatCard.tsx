import type { ReactNode } from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  subtext?: string;
}

export function StatCard({ label, value, icon, subtext }: StatCardProps) {
  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 hover:border-[var(--color-accent)] transition-colors duration-200">
      <div className="flex items-start justify-between mb-3">
        <span className="text-[var(--color-text-muted)] text-sm font-medium">{label}</span>
        <span className="text-[var(--color-accent)]">{icon}</span>
      </div>
      <div className="text-2xl font-semibold tracking-tight tabular-nums">{value}</div>
      {subtext && (
        <div className="text-[var(--color-text-muted)] text-xs mt-1">{subtext}</div>
      )}
    </div>
  );
}

