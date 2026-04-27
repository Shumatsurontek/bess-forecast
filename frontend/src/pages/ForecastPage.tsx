import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ChartForecast } from '@/components/ChartForecast';
import { JobLog } from '@/components/JobLog';
import { KPI } from '@/components/KPI';
import { RationalePanel } from '@/components/RationalePanel';
import { RunPicker } from '@/components/RunPicker';
import { SectionTitle } from '@/components/SectionTitle';
import { useJob } from '@/hooks/useJob';
import { forecastRepository } from '@/repositories/forecastRepository';

export default function ForecastPage() {
  const qc = useQueryClient();
  const nav = useNavigate();
  const { runId: urlRunId } = useParams<{ runId?: string }>();
  const [asof, setAsof] = useState('2025-12-01T00:00:00');
  const [model, setModel] = useState<'naive' | 'lgbm' | 'timesfm'>('lgbm');

  const runsQ = useQuery({
    queryKey: ['runs'],
    queryFn: () => forecastRepository.listRuns(),
  });
  const runs = (runsQ.data as any[]) ?? [];

  // The "active" run is whatever is in the URL, or the most-recent one.
  const activeRunId = urlRunId ?? runs[0]?.id ?? null;

  const runQ = useQuery({
    queryKey: ['run', activeRunId],
    queryFn: () => forecastRepository.byRunId(activeRunId!),
    enabled: !!activeRunId,
  });

  const trigger = useMutation({
    mutationFn: () => forecastRepository.trigger(asof, model),
  });
  const { events, done } = useJob(trigger.data?.job_id);

  // After a job completes: refetch the runs list and navigate to the new run.
  useEffect(() => {
    if (done && trigger.data) {
      qc.invalidateQueries({ queryKey: ['runs'] });
      nav(`/forecast/${(trigger.data as any).run_id}`);
    }
  }, [done, trigger.data, qc, nav]);

  const points: any[] = (runQ.data as any)?.points ?? [];
  const metrics = (runQ.data as any)?.run?.metrics ?? {};

  const chartData = useMemo(() => points.map((p: any) => ({
    ts: new Date(p.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    forecast: p.kw_pred,
  })), [points]);

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <SectionTitle
        eyebrow="forecast"
        title="Short-term load — peak shaving lens"
        subtitle="Quantile q=0.75 biases predictions slightly upward. Watch the pipeline stream stage by stage; every run is persisted and browsable below."
      />

      <div className="panel mb-6 flex flex-wrap items-end gap-4">
        <label className="block">
          <div className="text-muted text-xs uppercase tracking-widest mb-1">As of</div>
          <input
            value={asof}
            onChange={e => setAsof(e.target.value)}
            className="bg-navy-deep border border-white/10 rounded px-3 py-2 font-mono text-sm"
          />
        </label>
        <label className="block">
          <div className="text-muted text-xs uppercase tracking-widest mb-1">Model</div>
          <select
            value={model}
            onChange={e => setModel(e.target.value as any)}
            className="bg-navy-deep border border-white/10 rounded px-3 py-2 font-mono text-sm"
          >
            <option value="naive">naive (lag-672)</option>
            <option value="lgbm">lightgbm quantile</option>
            <option value="timesfm">timesfm zero-shot</option>
          </select>
        </label>
        <button
          onClick={() => trigger.mutate()}
          disabled={trigger.isPending || (!!trigger.data && !done)}
          className="bg-accent text-navy-deep font-semibold px-5 py-2 rounded hover:brightness-110 disabled:opacity-60"
        >
          {!!trigger.data && !done ? 'Streaming…' : 'Run forecast'}
        </button>
      </div>

      {trigger.data && (
        <div className="mb-6">
          <JobLog events={events} done={done} />
        </div>
      )}

      <RationalePanel />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KPI label="Pinball loss" value={fmt(metrics.pinball_loss, 2)} unit="kW" accent
             hint="Quantile (α=0.75) loss — penalizes under-forecasts heavier than over-forecasts. Lower is better." />
        <KPI label="RMSE" value={fmt(metrics.rmse, 2)} unit="kW"
             hint="Root mean squared error vs the actuals over the horizon. Symmetric — informational only here." />
        <KPI label="Peak capture" value={`${metrics.peaks_captured ?? '–'}/${metrics.peaks_total ?? '–'}`}
             hint="Of the actual peaks above the threshold, how many did the forecast also place above? The decision-relevant metric." />
        <KPI label="Threshold" value={fmt(metrics.threshold_kw, 1)} unit="kW"
             hint="Operating threshold = 85% of max(actuals) over the horizon. Above this line the controller would discharge." />
      </div>

      <div className="mb-8">
        <ChartForecast data={chartData} threshold={metrics.threshold_kw} />
      </div>

      <RunPicker runs={runs} activeId={activeRunId} />
    </div>
  );
}

function fmt(v: any, d = 2): string {
  if (v == null || Number.isNaN(v)) return '–';
  return Number(v).toFixed(d);
}
