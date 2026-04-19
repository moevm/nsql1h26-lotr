import type { ListLanguages200 } from '../../api/generated/models';

export const mockLanguages: ListLanguages200 = {
  count: 4,
  next: null,
  previous: null,
  results: [
    {
      slug: 'quenya',
      type: 'language',
      name: 'Квэнья',
      family: 'Эльфийские',
    },
    {
      slug: 'sindarin',
      type: 'language',
      name: 'Синдарин',
      family: 'Эльфийские',
    },
    {
      slug: 'khuzdul',
      type: 'language',
      name: 'Кхуздул',
      family: 'Гномьи',
    },
    {
      slug: 'westron',
      type: 'language',
      name: 'Вестрон',
      family: 'Людские',
    },
  ],
};