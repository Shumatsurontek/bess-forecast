import {
  Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts';

type Row = { ts: string; actual?: number; forecast?: number };

export function ChartForecast({ data, threshold }: { data: Row[]; threshold?: number }) {
  return (
    <div className="panel h-[420px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 12, right: 16, left: 0, bottom: 8 }}>
          <defs>
            <linearGradient id="g-forecast" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#5cd9c1" stopOpacity={0.45} />
              <stop offset="100%" stopColor="#5cd9c1" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="g-actual" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ffe066" stopOpacity={0.30} />
              <stop offset="100%" stopColor="#ffe066" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#1a3043" strokeDasharray="3 3" />
          <XAxis dataKey="ts" tick={{ fill: '#7a8b9c', fontSize: 11 }} />
          <YAxis tick={{ fill: '#7a8b9c', fontSize: 11 }} unit=" kW" />
          <Tooltip
            contentStyle={{ background: '#081827', border: '1px solid #1a3043',
              borderRadius: 6, fontFamily: 'JetBrains Mono', color: '#e8e6e3' }}
          />
          {threshold != null && (
            <ReferenceLine y={threshold} stroke="#ffe066" strokeDasharray="4 4" />
          )}
          <Area type="monotone" dataKey="actual" stroke="#ffe066" fill="url(#g-actual)"
                strokeWidth={1.6} isAnimationActive={false} />
          <Area type="monotone" dataKey="forecast" stroke="#5cd9c1" fill="url(#g-forecast)"
                strokeWidth={1.8} isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
