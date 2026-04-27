import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ChartForecast } from '@/components/ChartForecast';
import { KPI } from '@/components/KPI';
import { SectionTitle } from '@/components/SectionTitle';
import { forecastRepository } from '@/repositories/forecastRepository';

export default function ForecastPage() {
  const [asof, setAsof] = useState('2025-12-01T00:00:00');
  const [model, setModel] = useState<'naive' | 'lgbm' | 'timesfm'>('lgbm');

  const trigger = useMutation({
    mutationFn: () => forecastRepository.trigger(asof, model),
  });

  const runs = useQuery({
    queryKey: ['runs', trigger.isSuccess ? trigger.data?.run.id : null],
    queryFn: () => forecastRepository.listRuns(),
  });

  const lastRun: any = trigger.data ?? (runs.data && (runs.data as any[])[0]);
  const points: any[] = trigger.data?.points ?? [];
  const metrics = lastRun?.run?.metrics ?? lastRun?.metrics ?? {};

  const chartData = useMemo(() => points.map(p => ({
    ts: new Date(p.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    forecast: p.kw_pred,
  })), [points]);

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <SectionTitle
        eyebrow="forecast"
        title="Short-term load — peak shaving lens"
        subtitle="Quantile q=0.75 biases predictions slightly upward. The aim is not RMSE — it's catching peaks before they happen."
      />

      <div className="panel mb-8 flex flex-wrap items-end gap-4">
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
          className="bg-accent text-navy-deep font-semibold px-5 py-2 rounded hover:brightness-110 transition"
          disabled={trigger.isPending}
        >
          {trigger.isPending ? 'Running…' : 'Run forecast'}
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KPI label="Pinball loss" value={fmt(metrics.pinball_loss, 2)} unit="kW" accent />
        <KPI label="RMSE" value={fmt(metrics.rmse, 2)} unit="kW" />
        <KPI label="Peak capture" value={`${metrics.peaks_captured ?? '–'}/${metrics.peaks_total ?? '–'}`} />
        <KPI label="Threshold" value={fmt(metrics.threshold_kw, 1)} unit="kW" />
      </div>

      <ChartForecast data={chartData} threshold={metrics.threshold_kw} />
    </div>
  );
}

function fmt(v: any, d = 2): string {
  if (v == null || Number.isNaN(v)) return '–';
  return Number(v).toFixed(d);
}
