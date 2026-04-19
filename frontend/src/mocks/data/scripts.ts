import type { ListScripts200 } from '../../api/generated/models';

export const mockScripts: ListScripts200 = {
  count: 2,
  next: null,
  previous: null,
  results: [
    {
      slug: 'tengwar',
      type: 'script',
      name: 'Тенгвар',
    },
    {
      slug: 'cirth',
      type: 'script',
      name: 'Кирт',
    },
  ],
};