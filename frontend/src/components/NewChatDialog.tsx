import { useState } from 'react';
import type { ForecastRunDTO } from '@/api';

export function NewChatDialog({
  runs, defaultRunId, onCancel, onCreate,
}: {
  runs: ForecastRunDTO[];
  defaultRunId?: string;
  onCancel: () => void;
  onCreate: (runId: string, title: string) => void;
}) {
  const [runId, setRunId] = useState(defaultRunId ?? runs[0]?.id ?? '');
  const [title, setTitle] = useState('');

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!runId) return;
    onCreate(runId, title.trim() || `Diagnostic for run ${runId.slice(0, 8)}`);
  };

  return (
    <div className="fixed inset-0 z-50 bg-navy-deep/80 flex items-center justify-center px-4">
      <form
        onSubmit={submit}
        className="bg-navy ring-1 ring-white/10 rounded-lg p-6 w-full max-w-lg space-y-4"
      >
        <h2 className="font-serif text-2xl text-chalk">New diagnostic thread</h2>
        <p className="text-muted text-sm">
          Pick the forecast run the agent should diagnose. Its UUID will be pinned to
          the thread and injected into the agent's context — every tool call resolves
          against this run.
        </p>

        <label className="block">
          <div className="text-muted text-xs uppercase tracking-widest mb-1">Forecast run</div>
          <select
            value={runId}
            onChange={e => setRunId(e.target.value)}
            className="w-full bg-navy-deep border border-white/10 rounded px-3 py-2 font-mono text-sm"
          >
            {runs.length === 0 && <option value="">— no runs available —</option>}
            {runs.map(r => {
              const m = (r.metrics ?? {}) as any;
              const date = new Date(r.generated_at).toLocaleString([], {
                month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit',
              });
              const pinball = m.pinball_loss != null ? Number(m.pinball_loss).toFixed(2) : '–';
              return (
                <option key={r.id} value={r.id}>
                  {r.model_name} · {date} · pinball {pinball} · {r.id.slice(0, 8)}
                </option>
              );
            })}
          </select>
        </label>

        <label className="block">
          <div className="text-muted text-xs uppercase tracking-widest mb-1">
            Title <span className="text-muted/60">(optional)</span>
          </div>
          <input
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder={runId ? `Diagnostic for run ${runId.slice(0, 8)}` : ''}
            className="w-full bg-navy-deep border border-white/10 rounded px-3 py-2 text-sm"
          />
        </label>

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button" onClick={onCancel}
            className="px-4 py-2 rounded text-muted hover:text-ink"
          >Cancel</button>
          <button
            type="submit" disabled={!runId}
            className="bg-accent text-navy-deep font-semibold px-5 py-2 rounded hover:brightness-110 disabled:opacity-50"
          >Create thread</button>
        </div>
      </form>
    </div>
  );
}
