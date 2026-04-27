import { ForecastService } from '@/api';

export const forecastRepository = {
  listRuns: () => ForecastService.listRunsForecastRunsGet(),
  byRunId: (runId: string) => ForecastService.getRunForecastRunIdGet({ runId }),
  /** Async — returns { job_id, run_id }; subscribe to /ws/jobs/{job_id} for progress. */
  trigger: (asof: string, model: 'naive' | 'lgbm' | 'timesfm' = 'lgbm') =>
    ForecastService.triggerRunForecastRunPost({ asof, model }),
};
