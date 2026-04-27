import { ValidationService } from '@/api';

export const validationRepository = {
  last: () => ValidationService.validateLastValidationLastGet(),
};
