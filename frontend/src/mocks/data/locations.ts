import type { ListLocations200 } from '../../api/generated/models';

export const mockLocations: ListLocations200 = {
  count: 4,
  next: null,
  previous: null,
  results: [
    {
      slug: 'shire',
      name: 'Шир',
      imageUrl: '/images/shire.jpg',
      type: 'location',
      locationType: 'region',
      notableFor: 'Родина хоббитов',
      creationDate: 'TA 1601',
    },
    {
      slug: 'rivendell',
      name: 'Ривенделл',
      imageUrl: '/images/rivendell.jpg',
      type: 'location',
      locationType: 'city',
      notableFor: 'Убежище Эльронда',
      creationDate: null,
    },
    {
      slug: 'mordor',
      name: 'Мордор',
      imageUrl: '/images/mordor.jpg',
      type: 'location',
      locationType: 'region',
      notableFor: 'Владения Саурона',
      creationDate: null,
    },
    {
      slug: 'gondor',
      name: 'Гондор',
      imageUrl: '/images/gondor.jpg',
      type: 'location',
      locationType: 'kingdom',
      notableFor: 'Королевство людей',
      creationDate: 'TA 3320',
    },
  ],
};