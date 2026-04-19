import type { ListRaces200 } from '../../api/generated/models';

export const mockRaces: ListRaces200 = {
  count: 5,
  next: null,
  previous: null,
  results: [
    {
      slug: 'hobbits',
      type: 'race',
      name: 'Хоббиты',
      imageUrl: '/images/hobbits.jpg',
      distinctions: 'Маленький рост, волосатые ступни',
      lifespan: '100+ лет',
      avgHeight: '3-4 фута',
    },
    {
      slug: 'elves',
      type: 'race',
      name: 'Эльфы',
      imageUrl: '/images/elves.jpg',
      distinctions: 'Бессмертие, мудрость',
      lifespan: 'бессмертны',
      avgHeight: '5-6 футов',
    },
    {
      slug: 'dwarves',
      type: 'race',
      name: 'Гномы',
      imageUrl: '/images/dwarves.jpg',
      distinctions: 'Бородатые, искусные кузнецы',
      lifespan: '250+ лет',
      avgHeight: '4-5 футов',
    },
    {
      slug: 'men',
      type: 'race',
      name: 'Люди',
      imageUrl: '/images/men.jpg',
      distinctions: 'Смертные, амбициозные',
      lifespan: '70-100 лет',
      avgHeight: '5-6 футов',
    },
    {
      slug: 'ents',
      type: 'race',
      name: 'Энты',
      imageUrl: '/images/ents.jpg',
      distinctions: 'Древние, похожие на деревья',
      lifespan: 'тысячи лет',
      avgHeight: '14+ футов',
    },
  ],
};