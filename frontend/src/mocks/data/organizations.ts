import type { ListOrganizations200 } from '../../api/generated/models';

export const mockOrganizations: ListOrganizations200 = {
  count: 3,
  next: null,
  previous: null,
  results: [
    {
      slug: 'fellowship-of-the-ring',
      type: 'organization',
      name: 'Братство Кольца',
      imageUrl: '/images/fellowship.jpg',
      orgType: 'fellowship',
      foundedDate: 'TA 3018',
      purpose: 'Уничтожить Кольцо',
    },
    {
      slug: 'white-council',
      type: 'organization',
      name: 'Белый Совет',
      imageUrl: '/images/white-council.jpg',
      orgType: 'council',
      foundedDate: 'TA 2463',
      purpose: 'Противодействие Саурону',
    },
    {
      slug: 'the-shire-moot',
      type: 'organization',
      name: 'Мут Шира',
      imageUrl: '/images/shire-moot.jpg',
      orgType: 'assembly',
      foundedDate: 'неизвестно',
      purpose: 'Самоуправление хоббитов',
    },
  ],
};