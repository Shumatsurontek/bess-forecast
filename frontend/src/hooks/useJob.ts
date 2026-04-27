import { useEffect, useRef, useState } from 'react';
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
  const subId = useRef(0);

  useEffect(() => {
    // Always reset on every (re)subscription — prevents StrictMode double-mount
    // and back-to-back triggers from accumulating events from prior runs.
    setEvents([]);
    setDone(false);
    setError(null);
    if (!jobId) return;

    const mySub = ++subId.current;
    const ws = new WebSocket(`${wsBase()}/ws/jobs/${jobId}`);
    ws.onmessage = (e) => {
      if (mySub !== subId.current) return; // stale connection — ignore
      try {
        const evt: JobEvent = JSON.parse(e.data);
        if (evt.stage === '__done__') { setDone(true); return; }
        setEvents(prev => [...prev, evt]);
        if (evt.stage === 'error') setError(evt.message ?? 'unknown error');
        if (evt.stage === 'done') setDone(true);
      } catch { /* ignore non-JSON frames */ }
    };
    ws.onerror = () => { if (mySub === subId.current) setError('websocket error'); };
    ws.onclose = () => { if (mySub === subId.current) setDone(true); };
    return () => { try { ws.close(); } catch { /* noop */ } };
  }, [jobId]);

  return { events, done, error };
}
