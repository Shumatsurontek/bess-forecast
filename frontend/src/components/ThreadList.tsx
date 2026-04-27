import type { AgentThreadDTO } from '@/api';

export function ThreadList({
  threads, activeId, onSelect, onNew,
}: {
  threads: AgentThreadDTO[];
  activeId?: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
}) {
  return (
    <aside className="w-72 shrink-0 border-r border-white/5 px-4 py-6 h-screen sticky top-0 overflow-y-auto">
      <button
        onClick={onNew}
        className="w-full bg-accent text-navy-deep font-semibold py-2 rounded hover:brightness-110 mb-4"
      >
        + New chat
      </button>
      <div className="text-muted text-xs uppercase tracking-widest mb-2">Threads</div>
      <ul className="space-y-1">
        {threads.length === 0 && (
          <li className="text-muted text-sm italic">No threads yet</li>
        )}
        {threads.map(t => (
          <li key={t.id}>
            <button
              onClick={() => onSelect(t.id)}
              className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                activeId === t.id ? 'bg-navy text-accent' : 'hover:bg-navy/50 text-ink'
              }`}
            >
              <div className="truncate font-serif">{t.title}</div>
              {t.forecast_run_id && (
                <div className="text-muted text-xs font-mono mt-0.5">
                  run {t.forecast_run_id.slice(0, 8)}
                </div>
              )}
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
