import { DiagnosticService } from '@/api';
export const diagnosticRepository = {
    diagnose: (runId) => DiagnosticService.diagnoseDiagnosticRunIdPost({ runId }),
};
