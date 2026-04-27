import { TelemetryService } from '@/api';
export const telemetryRepository = {
    range: (since, until) => TelemetryService.getTelemetryTelemetryGet({ since, until }),
};
