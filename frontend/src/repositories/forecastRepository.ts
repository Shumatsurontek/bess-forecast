import { ForecastService } from '@/api';

export const forecastRepository = {
  listRuns: () => ForecastService.listRunsForecastRunsGet(),
  byRunId: (runId: string) => ForecastService.getRunForecastRunIdGet({ runId }),
  trigger: (asof: string, model: 'naive' | 'lgbm' | 'timesfm' = 'lgbm') =>
    ForecastService.triggerRunForecastRunPost({ asof, model }),
};
