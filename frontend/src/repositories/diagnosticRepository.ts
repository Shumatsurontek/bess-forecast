import { DiagnosticService } from '@/api';

export const diagnosticRepository = {
  diagnose: (runId: string) =>
    DiagnosticService.diagnoseDiagnosticRunIdPost({ runId }),
};
