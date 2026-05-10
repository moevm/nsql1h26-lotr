import type { CategoryListItem, CategoryDetail } from '../../api/generated/models';

export const mockRootCategories: CategoryListItem[] = [
  {
    slug: 'characters',
    name: 'Characters',
    description: 'All characters of Middle-earth',
    parent_slug: null,
    child_count: 2,
    page_count: 150,
  },
  {
    slug: 'locations',
    name: 'Locations',
    description: 'Places in Middle-earth',
    parent_slug: null,
    child_count: 2,
    page_count: 80,
  }
];

export const mockCategory: Record<string, CategoryDetail> = {
  characters: {
    slug: 'characters',
    name: 'Characters',
    description: 'All characters of Middle-earth',
    parent_slug: null,
    child_count: 2,
    page_count: 150,
    parent: null,
    children: [
      { slug: 'good-characters', name: 'Good Characters', page_count: 89 },
      { slug: 'evil-characters', name: 'Evil Characters', page_count: 45 }
    ],
    pages: {
      count: 150,
      next: null,
      previous: null,
      results: [
        { slug: 'frodo-baggins', type: 'character', name: 'Frodo Baggins', image_url: '/images/frodo.jpg' },
        { slug: 'aragorn', type: 'character', name: 'Aragorn', image_url: '/images/aragorn.jpg' }
      ]
    }
  },
  'good-characters': {
    slug: 'good-characters',
    name: 'Good Characters',
    description: 'Heroic characters',
    parent_slug: 'characters',
    child_count: 2,
    page_count: 89,
    parent: { slug: 'characters', name: 'Characters' },
    children: [
      { slug: 'hobbits-of-the-shire', name: 'Hobbits of the Shire', page_count: 14 },
      { slug: 'fellowship-members', name: 'Fellowship Members', page_count: 9 }
    ],
    pages: {
      count: 89,
      next: null,
      previous: null,
      results: [
        { slug: 'frodo-baggins', type: 'character', name: 'Frodo Baggins', image_url: '/images/frodo.jpg' },
        { slug: 'aragorn', type: 'character', name: 'Aragorn', image_url: '/images/aragorn.jpg' }
      ]
    }
  }
};