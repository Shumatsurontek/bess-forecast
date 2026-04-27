import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { MessageList } from '@/components/MessageList';
import { SectionTitle } from '@/components/SectionTitle';
import { ThreadList } from '@/components/ThreadList';
import { useJob } from '@/hooks/useJob';
import { forecastRepository } from '@/repositories/forecastRepository';
import { threadsRepository } from '@/repositories/threadsRepository';

export default function ChatPage() {
  const qc = useQueryClient();
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [draft, setDraft] = useState('');

  const threads = useQuery({
    queryKey: ['threads'],
    queryFn: () => threadsRepository.list(),
  });

  const runs = useQuery({
    queryKey: ['runs'],
    queryFn: () => forecastRepository.listRuns(),
  });

  const messages = useQuery({
    queryKey: ['messages', activeThreadId],
    queryFn: () => threadsRepository.messages(activeThreadId!),
    enabled: !!activeThreadId,
    refetchInterval: activeJobId ? 2000 : false,
  });

  const createThread = useMutation({
    mutationFn: () => {
      const latestRunId = (runs.data as any[])?.[0]?.id;
      return threadsRepository.create(
        latestRunId,
        latestRunId ? `Diagnostic for run ${latestRunId.slice(0, 8)}` : 'New conversation',
      );
    },
    onSuccess: (t: any) => {
      qc.invalidateQueries({ queryKey: ['threads'] });
      setActiveThreadId(t.id);
    },
  });

  const send = useMutation({
    mutationFn: (content: string) => threadsRepository.send(activeThreadId!, content),
    onSuccess: (d: any) => setActiveJobId(d.job_id),
  });

  const { events, done } = useJob(activeJobId);

  useEffect(() => {
    if (done && activeJobId) {
      setActiveJobId(null);
      qc.invalidateQueries({ queryKey: ['messages', activeThreadId] });
      qc.invalidateQueries({ queryKey: ['threads'] });
    }
  }, [done, activeJobId, activeThreadId, qc]);

  // Auto-pick the first thread (or trigger creation if none and runs exist).
  useEffect(() => {
    if (activeThreadId) return;
    const list = (threads.data as any[]) ?? [];
    if (list.length > 0) setActiveThreadId(list[0].id);
  }, [threads.data, activeThreadId]);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!draft.trim() || !activeThreadId || activeJobId) return;
    send.mutate(draft.trim());
    setDraft('');
  };

  return (
    <div className="flex">
      <ThreadList
        threads={(threads.data as any) ?? []}
        activeId={activeThreadId}
        onSelect={setActiveThreadId}
        onNew={() => createThread.mutate()}
      />
      <div className="flex-1 flex flex-col min-h-screen">
        <header className="px-6 pt-12 pb-4">
          <SectionTitle
            eyebrow="diagnostic agent"
            title="Forecast diagnostic chat"
            subtitle="Read-only LangChain agent. Ask why a run missed peaks; the tools, args and results stream live, conversation persists in Postgres."
          />
        </header>

        {!activeThreadId && (
          <div className="px-6 text-muted">
            Pick a thread on the left or click <span className="text-accent">+ New chat</span>.
          </div>
        )}

        {activeThreadId && (
          <>
            <MessageList
              messages={(messages.data as any) ?? []}
              liveEvents={events}
              pending={!!activeJobId}
            />
            <form onSubmit={onSubmit} className="border-t border-white/5 px-6 py-4 flex gap-3">
              <textarea
                value={draft}
                onChange={e => setDraft(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) onSubmit(e as any);
                }}
                placeholder="Diagnose this run, or ask a follow-up…"
                rows={2}
                disabled={!!activeJobId}
                className="flex-1 bg-navy-deep border border-white/10 rounded px-3 py-2 text-sm font-sans resize-none disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!draft.trim() || !!activeJobId}
                className="bg-accent text-navy-deep font-semibold px-5 py-2 rounded hover:brightness-110 disabled:opacity-50"
              >
                {activeJobId ? 'Streaming…' : 'Send'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
