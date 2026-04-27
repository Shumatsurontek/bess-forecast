import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import type { AgentMessageDTO } from '@/api';
import type { JobEvent } from '@/hooks/useJob';

export function MessageList({
  messages, liveEvents = [], pending = false,
}: {
  messages: AgentMessageDTO[];
  liveEvents?: JobEvent[];
  pending?: boolean;
}) {
  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5">
      {messages.map(m => (
        <Bubble key={m.id} m={m} />
      ))}
      {pending && <LiveStream events={liveEvents} />}
    </div>
  );
}

function Bubble({ m }: { m: AgentMessageDTO }) {
  if (m.role === 'tool') return <ToolCard m={m} />;
  const isUser = m.role === 'user';
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`max-w-[80%] rounded-lg px-4 py-3 ${
        isUser ? 'bg-navy text-ink' : 'bg-navy-deep ring-1 ring-white/5 text-ink'
      }`}>
        <div className={`text-xs font-mono uppercase tracking-widest mb-1 ${
          isUser ? 'text-muted' : 'text-accent'
        }`}>{m.role}</div>
        <div className="prose prose-invert prose-sm max-w-none font-serif">
          <ReactMarkdown>{m.content}</ReactMarkdown>
        </div>
      </div>
    </motion.div>
  );
}

function ToolCard({ m }: { m: AgentMessageDTO }) {
  return (
    <details className="bg-navy-deep ring-1 ring-white/5 rounded-md px-4 py-2 text-sm">
      <summary className="cursor-pointer text-teal font-mono">
        ⚙ {m.tool_name ?? 'tool'} <span className="text-muted">— {m.content.length} chars</span>
      </summary>
      <pre className="mt-2 text-xs text-muted overflow-x-auto whitespace-pre-wrap">{m.content}</pre>
    </details>
  );
}

function LiveStream({ events }: { events: JobEvent[] }) {
  if (events.length === 0) return <div className="text-muted text-sm italic">thinking…</div>;
  return (
    <div className="bg-navy/40 ring-1 ring-accent/20 rounded-lg p-4 font-mono text-xs space-y-1">
      <div className="text-accent uppercase tracking-widest mb-2">live</div>
      {events.map((e, i) => (
        <div key={i} className="text-muted">
          <span className="text-teal">{e.stage}</span>{' '}
          {e.message ?? ''}
          {e.extra && (e.extra as any).tool && <span className="text-accent"> ({(e.extra as any).tool})</span>}
        </div>
      ))}
    </div>
  );
}
