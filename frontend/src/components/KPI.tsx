import { motion } from 'framer-motion';

export function KPI({ label, value, unit, accent, hint }: {
  label: string; value: string | number; unit?: string; accent?: boolean; hint?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="panel relative group"
      title={hint}
    >
      <div className="text-muted text-xs uppercase tracking-widest mb-2 flex items-center gap-1">
        {label}
        {hint && <span className="text-muted/60">ⓘ</span>}
      </div>
      <div className={`num text-4xl ${accent ? 'text-accent' : 'text-chalk'}`}>
        {value}
        {unit && <span className="text-muted text-base ml-1">{unit}</span>}
      </div>
    </motion.div>
  );
}
