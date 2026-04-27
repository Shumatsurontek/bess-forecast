import { motion } from 'framer-motion';

export function KPI({ label, value, unit, accent }: {
  label: string; value: string | number; unit?: string; accent?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="panel"
    >
      <div className="text-muted text-xs uppercase tracking-widest mb-2">{label}</div>
      <div className={`num text-4xl ${accent ? 'text-accent' : 'text-chalk'}`}>
        {value}
        {unit && <span className="text-muted text-base ml-1">{unit}</span>}
      </div>
    </motion.div>
  );
}
