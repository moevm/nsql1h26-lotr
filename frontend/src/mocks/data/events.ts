import type { ListEvents200 } from '../../api/generated/models';

export const mockEvents: ListEvents200 = {
  count: 4,
  next: null,
  previous: null,
  results: [
    {
      slug: 'war-of-the-ring',
      type: 'event',
      name: 'Война Кольца',
      imageUrl: '/images/war-of-the-ring.jpg',
      eventType: 'war',
      startDate: 'TA 3018',
      endDate: 'TA 3019',
    },
    {
      slug: 'battle-of-five-armies',
      type: 'event',
      name: 'Битва Пяти Воинств',
      imageUrl: '/images/battle-five-armies.jpg',
      eventType: 'battle',
      startDate: 'TA 2941',
      endDate: 'TA 2941',
    },
    {
      slug: 'council-of-elrond',
      type: 'event',
      name: 'Совет Эльронда',
      imageUrl: '/images/council-elrond.jpg',
      eventType: 'council',
      startDate: 'TA 3018',
      endDate: 'TA 3018',
    },
    {
      slug: 'downfall-of-sauron',
      type: 'event',
      name: 'Падение Саурона',
      imageUrl: '/images/downfall-sauron.jpg',
      eventType: 'catastrophe',
      startDate: 'TA 3019',
      endDate: 'TA 3019',
    },
  ],
};