import { motion } from 'framer-motion';

export function SectionTitle({ eyebrow, title, subtitle }: {
  eyebrow?: string; title: string; subtitle?: string;
}) {
  return (
    <motion.header
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="mb-8"
    >
      {eyebrow && (
        <div className="text-accent text-xs font-mono uppercase tracking-[0.25em] mb-2">
          {eyebrow}
        </div>
      )}
      <h1 className="font-serif text-4xl md:text-5xl text-chalk leading-tight">{title}</h1>
      {subtitle && (
        <p className="mt-3 text-muted max-w-2xl leading-relaxed">{subtitle}</p>
      )}
    </motion.header>
  );
}
