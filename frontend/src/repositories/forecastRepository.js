import { ForecastService } from '@/api';
export const forecastRepository = {
    listRuns: () => ForecastService.listRunsForecastRunsGet(),
    byRunId: (runId) => ForecastService.getRunForecastRunIdGet({ runId }),
    trigger: (asof, model = 'lgbm') => ForecastService.triggerRunForecastRunPost({ asof, model }),
};
