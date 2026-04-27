import { ThreadsService } from '@/api';

export const threadsRepository = {
  list: () => ThreadsService.listThreadsThreadsGet({}),
  create: (forecastRunId?: string, title?: string) =>
    ThreadsService.createThreadThreadsPost({
      requestBody: { forecast_run_id: forecastRunId ?? null, title: title ?? null },
    }),
  messages: (threadId: string) =>
    ThreadsService.listMessagesThreadsThreadIdMessagesGet({ threadId }),
  send: (threadId: string, content: string) =>
    ThreadsService.sendMessageThreadsThreadIdMessagesPost({
      threadId, requestBody: { content },
    }),
};
