import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { motion } from 'framer-motion';
export function KPI({ label, value, unit, accent }) {
    return (_jsxs(motion.div, { initial: { opacity: 0, y: 6 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.4 }, className: "panel", children: [_jsx("div", { className: "text-muted text-xs uppercase tracking-widest mb-2", children: label }), _jsxs("div", { className: `num text-4xl ${accent ? 'text-accent' : 'text-chalk'}`, children: [value, unit && _jsx("span", { className: "text-muted text-base ml-1", children: unit })] })] }));
}
