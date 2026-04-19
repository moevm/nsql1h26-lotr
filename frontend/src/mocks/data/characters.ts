import type { ListCharacters200 } from '../../api/generated/models';

export const mockCharacters: ListCharacters200 = {
  count: 3,
  next: null,
  previous: null,
  results: [
    {
      slug: 'frodo-baggins',
      type: 'character',
      name: 'Frodo Baggins',
      imageUrl: '/images/frodo.jpg',
      notableFor: 'Ring-bearer',
      gender: 'male',
      birthDate: 'TA 2968',
      race: { slug: 'hobbits', type: 'race', name: 'Hobbits' },
    },
    {
      slug: 'gandalf',
      type: 'character',
      name: 'Gandalf',
      imageUrl: '/images/gandalf.jpg',
      notableFor: 'Wizard, leader of the Fellowship',
      gender: 'male',
      birthDate: 'before TA 1000',
      race: { slug: 'maiar', type: 'race', name: 'Maiar' },
    },
    {
      slug: 'aragorn',
      type: 'character',
      name: 'Aragorn',
      imageUrl: '/images/aragorn.jpg',
      notableFor: 'King of Gondor',
      gender: 'male',
      birthDate: 'TA 2931',
      race: { slug: 'men', type: 'race', name: 'Men' },
    },
  ],
};