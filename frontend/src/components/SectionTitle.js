import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { motion } from 'framer-motion';
export function SectionTitle({ eyebrow, title, subtitle }) {
    return (_jsxs(motion.header, { initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.5 }, className: "mb-8", children: [eyebrow && (_jsx("div", { className: "text-accent text-xs font-mono uppercase tracking-[0.25em] mb-2", children: eyebrow })), _jsx("h1", { className: "font-serif text-4xl md:text-5xl text-chalk leading-tight", children: title }), subtitle && (_jsx("p", { className: "mt-3 text-muted max-w-2xl leading-relaxed", children: subtitle }))] }));
}
