import { ForecastService } from '@/api';

export const forecastRepository = {
  listRuns: () => ForecastService.listRunsForecastRunsGet(),
  byRunId: (runId: string) =>
    ForecastService.getRunForecastRunIdGet({ runId } as any),
  trigger: (asof: string, model: 'naive' | 'lgbm' | 'timesfm' = 'lgbm') =>
    ForecastService.triggerRunForecastRunPost({ asof, model } as any),
};
