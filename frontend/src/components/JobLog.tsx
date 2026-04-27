import { motion } from 'framer-motion';
import type { JobEvent } from '@/hooks/useJob';

const stageLabel: Record<string, string> = {
  loading_csv: 'load',
  validating_raw: 'validate raw',
  repairing: 'repair',
  validating_post: 'validate post',
  building_features: 'features',
  fitting: 'fit',
  predicting: 'predict',
  computing_metrics: 'metrics',
  saving: 'save',
  done: 'done',
  error: 'error',
  thinking: 'thinking',
  tool_call: 'tool call',
  tool_result: 'tool result',
  final_message: 'reply',
};

export function JobLog({ events, done }: { events: JobEvent[]; done: boolean }) {
  if (events.length === 0 && !done) {
    return <div className="panel font-mono text-muted text-sm">connecting…</div>;
  }
  return (
    <div className="panel font-mono text-sm">
      <ol className="space-y-1.5">
        {events.map((e, i) => {
          const isLast = i === events.length - 1;
          const isErr = e.stage === 'error';
          const isDone = e.stage === 'done';
          const cls = isErr ? 'text-red-300'
            : isDone ? 'text-teal'
            : (isLast && !done) ? 'text-accent'
            : 'text-muted';
          return (
            <motion.li
              key={i}
              initial={{ opacity: 0, x: -4 }}
              animate={{ opacity: 1, x: 0 }}
              className={`flex gap-3 ${cls}`}
            >
              <span className="w-3 text-center">
                {isLast && !done && !isErr ? '◆' : isErr ? '✗' : isDone ? '●' : '○'}
              </span>
              <span className="w-32 shrink-0">{stageLabel[e.stage] ?? e.stage}</span>
              <span className="flex-1 text-ink/70 truncate">{e.message ?? ''}</span>
              {e.pct != null && <span className="text-muted">{Math.round(e.pct * 100)}%</span>}
            </motion.li>
          );
        })}
      </ol>
    </div>
  );
}
