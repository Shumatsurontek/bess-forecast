import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ChartForecast } from '@/components/ChartForecast';
import { KPI } from '@/components/KPI';
import { SectionTitle } from '@/components/SectionTitle';
import { forecastRepository } from '@/repositories/forecastRepository';
export default function ForecastPage() {
    const [asof, setAsof] = useState('2025-12-01T00:00:00');
    const [model, setModel] = useState('lgbm');
    const trigger = useMutation({
        mutationFn: () => forecastRepository.trigger(asof, model),
    });
    const runs = useQuery({
        queryKey: ['runs', trigger.isSuccess ? trigger.data?.run.id : null],
        queryFn: () => forecastRepository.listRuns(),
    });
    const lastRun = trigger.data ?? (runs.data && runs.data[0]);
    const points = trigger.data?.points ?? [];
    const metrics = lastRun?.run?.metrics ?? lastRun?.metrics ?? {};
    const chartData = useMemo(() => points.map(p => ({
        ts: new Date(p.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        forecast: p.kw_pred,
    })), [points]);
    return (_jsxs("div", { className: "max-w-6xl mx-auto px-6 py-12", children: [_jsx(SectionTitle, { eyebrow: "forecast", title: "Short-term load \u2014 peak shaving lens", subtitle: "Quantile q=0.75 biases predictions slightly upward. The aim is not RMSE \u2014 it's catching peaks before they happen." }), _jsxs("div", { className: "panel mb-8 flex flex-wrap items-end gap-4", children: [_jsxs("label", { className: "block", children: [_jsx("div", { className: "text-muted text-xs uppercase tracking-widest mb-1", children: "As of" }), _jsx("input", { value: asof, onChange: e => setAsof(e.target.value), className: "bg-navy-deep border border-white/10 rounded px-3 py-2 font-mono text-sm" })] }), _jsxs("label", { className: "block", children: [_jsx("div", { className: "text-muted text-xs uppercase tracking-widest mb-1", children: "Model" }), _jsxs("select", { value: model, onChange: e => setModel(e.target.value), className: "bg-navy-deep border border-white/10 rounded px-3 py-2 font-mono text-sm", children: [_jsx("option", { value: "naive", children: "naive (lag-672)" }), _jsx("option", { value: "lgbm", children: "lightgbm quantile" }), _jsx("option", { value: "timesfm", children: "timesfm zero-shot" })] })] }), _jsx("button", { onClick: () => trigger.mutate(), className: "bg-accent text-navy-deep font-semibold px-5 py-2 rounded hover:brightness-110 transition", disabled: trigger.isPending, children: trigger.isPending ? 'Running…' : 'Run forecast' })] }), _jsxs("div", { className: "grid grid-cols-2 md:grid-cols-4 gap-4 mb-8", children: [_jsx(KPI, { label: "Pinball loss", value: fmt(metrics.pinball_loss, 2), unit: "kW", accent: true }), _jsx(KPI, { label: "RMSE", value: fmt(metrics.rmse, 2), unit: "kW" }), _jsx(KPI, { label: "Peak capture", value: `${metrics.peaks_captured ?? '–'}/${metrics.peaks_total ?? '–'}` }), _jsx(KPI, { label: "Threshold", value: fmt(metrics.threshold_kw, 1), unit: "kW" })] }), _jsx(ChartForecast, { data: chartData, threshold: metrics.threshold_kw })] }));
}
function fmt(v, d = 2) {
    if (v == null || Number.isNaN(v))
        return '–';
    return Number(v).toFixed(d);
}
