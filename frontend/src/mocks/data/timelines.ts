import type { ListTimelines200 } from '../../api/generated/models';

export const mockTimelines: ListTimelines200 = {
  count: 4,
  next: null,
  previous: null,
  results: [
    {
      slug: 'first-age',
      type: 'timeline',
      name: 'Первая эпоха',
      abbreviation: 'ПЭ',
      startDate: 'до 1500 ВЭ',
      endDate: 'SA 1',
    },
    {
      slug: 'second-age',
      type: 'timeline',
      name: 'Вторая эпоха',
      abbreviation: 'ВЭ',
      startDate: 'SA 1',
      endDate: 'SA 3441',
    },
    {
      slug: 'third-age',
      type: 'timeline',
      name: 'Третья эпоха',
      abbreviation: 'ТА',
      startDate: 'TA 1',
      endDate: 'TA 3021',
    },
    {
      slug: 'fourth-age',
      type: 'timeline',
      name: 'Четвёртая эпоха',
      abbreviation: 'ЧА',
      startDate: 'TA 3021',
      endDate: 'продолжается',
    },
  ],
};