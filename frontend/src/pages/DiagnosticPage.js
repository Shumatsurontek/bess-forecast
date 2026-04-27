import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import { motion } from 'framer-motion';
import { SectionTitle } from '@/components/SectionTitle';
import { diagnosticRepository } from '@/repositories/diagnosticRepository';
export default function DiagnosticPage() {
    const [runId, setRunId] = useState('');
    const m = useMutation({
        mutationFn: () => diagnosticRepository.diagnose(runId),
    });
    return (_jsxs("div", { className: "max-w-4xl mx-auto px-6 py-12", children: [_jsx(SectionTitle, { eyebrow: "diagnostic agent", title: "Why did the forecast miss?", subtitle: "Read-only LangChain agent. Calls the same domain ports as the pipeline, never writes. Trace lives in LangSmith." }), _jsxs("div", { className: "panel mb-6 flex gap-3", children: [_jsx("input", { value: runId, onChange: e => setRunId(e.target.value), placeholder: "forecast run id (uuid)", className: "bg-navy-deep border border-white/10 rounded px-3 py-2 font-mono text-sm flex-1" }), _jsx("button", { onClick: () => m.mutate(), disabled: !runId || m.isPending, className: "bg-accent text-navy-deep font-semibold px-5 py-2 rounded hover:brightness-110 disabled:opacity-50", children: m.isPending ? 'Asking the agent…' : 'Diagnose' })] }), m.data && (_jsx(motion.article, { initial: { opacity: 0, y: 6 }, animate: { opacity: 1, y: 0 }, className: "panel prose prose-invert max-w-none font-serif", children: _jsx(ReactMarkdown, { children: m.data.report_markdown }) }))] }));
}
