import { Link } from 'react-router-dom';
import type { ForecastRunDTO } from '@/api';

const fmt = (v: any, d = 2) =>
  v == null || Number.isNaN(v) ? '–' : Number(v).toFixed(d);

export function RunPicker({
  runs, activeId,
}: { runs: ForecastRunDTO[]; activeId?: string | null }) {
  if (runs.length === 0) {
    return <div className="panel text-muted text-sm italic">No runs yet — trigger one above.</div>;
  }
  return (
    <div className="panel">
      <div className="text-muted text-xs uppercase tracking-widest mb-3">
        Past runs ({runs.length})
      </div>
      <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {runs.map(r => {
          const m = r.metrics ?? {};
          const isActive = r.id === activeId;
          return (
            <li key={r.id}>
              <Link
                to={`/forecast/${r.id}`}
                className={`block px-3 py-2 rounded ring-1 transition-colors ${
                  isActive
                    ? 'ring-accent/60 bg-navy text-ink'
                    : 'ring-white/5 hover:ring-teal/40 bg-navy-deep'
                }`}
              >
                <div className="flex justify-between items-baseline">
                  <span className="font-mono text-xs text-teal">{r.model_name}</span>
                  <span className="font-mono text-xs text-muted">
                    {new Date(r.generated_at).toLocaleString([], {
                      month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit',
                    })}
                  </span>
                </div>
                <div className="mt-1 flex gap-4 text-xs text-muted">
                  <span>pinball <span className="text-ink num">{fmt((m as any).pinball_loss)}</span></span>
                  <span>peaks <span className="text-ink num">
                    {(m as any).peaks_captured ?? '–'}/{(m as any).peaks_total ?? '–'}
                  </span></span>
                  {(m as any).horizon_has_actuals === false && (
                    <span className="text-accent/70 italic">future</span>
                  )}
                </div>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
