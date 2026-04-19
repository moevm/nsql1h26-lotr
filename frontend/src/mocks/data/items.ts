import type { ListItems200 } from '../../api/generated/models';

export const mockItems: ListItems200 = {
  count: 4,
  next: null,
  previous: null,
  results: [
    {
      slug: 'the-one-ring',
      type: 'item',
      name: 'Кольцо Всевластия',
      imageUrl: '/images/one-ring.jpg',
      itemType: 'ring',
      material: 'gold',
      notableFor: 'Кольцо, чтобы править всеми',
    },
    {
      slug: 'sting',
      type: 'item',
      name: 'Жало',
      imageUrl: '/images/sting.jpg',
      itemType: 'sword',
      material: 'steel',
      notableFor: 'Меч Фродо, сияющий при орках',
    },
    {
      slug: 'mithril-shirt',
      type: 'item',
      name: 'Мифриловая кольчуга',
      imageUrl: '/images/mithril-shirt.jpg',
      itemType: 'armor',
      material: 'mithril',
      notableFor: 'Подарок Бильбо Фродо',
    },
    {
      slug: 'palantir',
      type: 'item',
      name: 'Палантир',
      imageUrl: '/images/palantir.jpg',
      itemType: 'artifact',
      material: 'crystal',
      notableFor: 'Камень видения',
    },
  ],
};