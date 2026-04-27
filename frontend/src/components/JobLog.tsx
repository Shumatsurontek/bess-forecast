import { motion } from 'framer-motion';
import type { JobEvent } from '@/hooks/useJob';

const stageLabel: Record<string, string> = {
  loading_csv: 'load',
  validating_raw: 'validate raw',
  repairing: 'repair',
  validating_post: 'validate post',
  building_features: 'features',
  fitting: 'fit',
  predicting: 'predict',
  computing_metrics: 'metrics',
  saving: 'save',
  done: 'done',
  error: 'error',
  thinking: 'thinking',
  tool_call: 'tool call',
  tool_result: 'tool result',
  final_message: 'reply',
};

const stageWhy: Record<string, string> = {
  loading_csv: 'Read the 15-min telemetry CSV (Europe/Berlin tz, German decimals).',
  validating_raw: 'Run typed rules: temporal continuity, sentinels, stuck sensors, gaps. Issues are classified BLOCKING vs WARNING.',
  repairing: 'Fail-safe sanitize: drop sensor sentinels, clip negatives, ffill short gaps so a single dirty quarter-hour doesn\'t take the controller down.',
  validating_post: 'Re-run the rules on the repaired series to be sure no BLOCKING remains. If it does, abort and fall back to the previous forecast.',
  building_features: 'Lag-1, lag-96 (1d), lag-672 (1w) + rolling means + calendar (holiday DE, dayofweek, hour, DST flag).',
  fitting: 'Train the chosen model. LightGBM uses pinball loss with α=0.75 — biased slightly upward so missed peaks cost less than over-forecasts.',
  predicting: 'Recursive 1-step-ahead so lag features stay valid through the 24h horizon (96 quarter-hours).',
  computing_metrics: 'Pinball loss (α=0.75), RMSE, MAE, plus the operational Peak Capture Rate at 85% of max(actuals).',
  saving: 'Persist the run + 96 points into Postgres. Bi-temporal: every run carries its own generated_at so historical decisions are reconstructable.',
  done: 'Forecast available. The peak-shaving controller can now compare predictions against the threshold to schedule charge/discharge.',
  error: 'A stage failed. The controller falls back to the last good forecast.',
  thinking: 'Agent is reasoning about which tool to call next.',
  tool_call: 'Agent invokes one of its read-only tools (get_forecast_run, get_actuals, compute_peak_metrics, get_calendar_context).',
  tool_result: 'Tool returned data — agent will incorporate it into its reasoning.',
  final_message: 'Agent has produced its diagnostic Markdown report.',
};

export function JobLog({ events, done }: { events: JobEvent[]; done: boolean }) {
  if (events.length === 0 && !done) {
    return <div className="panel font-mono text-muted text-sm">connecting…</div>;
  }
  return (
    <div className="panel font-mono text-sm">
      <ol className="space-y-1.5">
        {events.map((e, i) => {
          const isLast = i === events.length - 1;
          const isErr = e.stage === 'error';
          const isDone = e.stage === 'done';
          const cls = isErr ? 'text-red-300'
            : isDone ? 'text-teal'
            : (isLast && !done) ? 'text-accent'
            : 'text-muted';
          const why = stageWhy[e.stage];
          return (
            <motion.li
              key={i}
              initial={{ opacity: 0, x: -4 }}
              animate={{ opacity: 1, x: 0 }}
              className={`flex gap-3 group ${cls}`}
              title={why}
            >
              <span className="w-3 text-center">
                {isLast && !done && !isErr ? '◆' : isErr ? '✗' : isDone ? '●' : '○'}
              </span>
              <span className="w-32 shrink-0 underline decoration-dotted decoration-muted/40 underline-offset-2">
                {stageLabel[e.stage] ?? e.stage}
              </span>
              <span className="flex-1 text-ink/70 truncate">{e.message ?? ''}</span>
              {e.pct != null && <span className="text-muted">{Math.round(e.pct * 100)}%</span>}
            </motion.li>
          );
        })}
      </ol>
    </div>
  );
}
