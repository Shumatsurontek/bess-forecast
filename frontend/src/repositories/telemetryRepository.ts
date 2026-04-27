import { TelemetryService } from '@/api';

export const telemetryRepository = {
  range: (since: string, until: string) =>
    TelemetryService.getTelemetryTelemetryGet({ since, until } as any),
};
