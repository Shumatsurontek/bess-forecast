import { useEffect, useState } from 'react';
import { OpenAPI } from '@/api';

export interface JobEvent {
  stage: string;
  message?: string;
  pct?: number | null;
  extra?: Record<string, unknown>;
}

const wsBase = (): string =>
  (OpenAPI.BASE || 'http://localhost:8000').replace(/^http/, 'ws');

export function useJob(jobId?: string | null) {
  const [events, setEvents] = useState<JobEvent[]>([]);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) { setEvents([]); setDone(false); setError(null); return; }
    const ws = new WebSocket(`${wsBase()}/ws/jobs/${jobId}`);
    ws.onmessage = (e) => {
      try {
        const evt: JobEvent = JSON.parse(e.data);
        if (evt.stage === '__done__') { setDone(true); return; }
        setEvents(prev => [...prev, evt]);
        if (evt.stage === 'error') setError(evt.message ?? 'unknown error');
        if (evt.stage === 'done') setDone(true);
      } catch (err) { /* ignore non-JSON frames */ }
    };
    ws.onerror = () => setError('websocket error');
    ws.onclose = () => setDone(true);
    return () => { try { ws.close(); } catch { /* noop */ } };
  }, [jobId]);

  return { events, done, error };
}
