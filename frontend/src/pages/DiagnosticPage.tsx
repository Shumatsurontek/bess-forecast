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

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <SectionTitle
        eyebrow="diagnostic agent"
        title="Why did the forecast miss?"
        subtitle="Read-only LangChain agent. Calls the same domain ports as the pipeline, never writes. Trace lives in LangSmith."
      />

      <div className="panel mb-6 flex gap-3">
        <input
          value={runId}
          onChange={e => setRunId(e.target.value)}
          placeholder="forecast run id (uuid)"
          className="bg-navy-deep border border-white/10 rounded px-3 py-2 font-mono text-sm flex-1"
        />
        <button
          onClick={() => m.mutate()}
          disabled={!runId || m.isPending}
          className="bg-accent text-navy-deep font-semibold px-5 py-2 rounded hover:brightness-110 disabled:opacity-50"
        >
          {m.isPending ? 'Asking the agent…' : 'Diagnose'}
        </button>
      </div>

      {m.data && (
        <motion.article
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="panel prose prose-invert max-w-none font-serif"
        >
          <ReactMarkdown>{(m.data as any).report_markdown}</ReactMarkdown>
        </motion.article>
      )}
    </div>
  );
}
