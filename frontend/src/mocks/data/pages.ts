export const mockPages: Record<string, any> = {
  'frodo-baggins': {
    slug: 'frodo-baggins',
    names: ['Frodo Baggins', 'Frodo'],
    article: {
      text: "Frodo Baggins is a hobbit of the Shire who inherited the One Ring from his uncle Bilbo Baggins and undertook the quest to destroy it in the fires of Mount Doom. He was a member of the Fellowship of the Ring and showed great resilience against the Ring's corruption.",
      imageUrl: '/images/frodo.jpg',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    relations: {
      outgoing: {
        owns: [
          {
            target: {
              slug: 'one-ring',
              type: 'item',
              name: 'One Ring',
              imageUrl: '/images/one-ring.jpg',
            },
            properties: { acquired: 'TA 3001' },
          },
        ],
        friend_of: [
          {
            target: {
              slug: 'samwise-gamgee',
              type: 'character',
              name: 'Samwise Gamgee',
              imageUrl: '/images/sam.jpg',
            },
            properties: { relationship: 'closest friend' },
          },
        ],
      },
      incoming: {
        member_of: [
          {
            from: {
              slug: 'fellowship-of-the-ring',
              type: 'organization',
              name: 'Fellowship of the Ring',
              imageUrl: '/images/fellowship.jpg',
            },
            properties: { role: 'Ring-bearer' },
          },
        ],
      },
    },
    categories: [
      { slug: 'hobbits', name: 'Hobbits' },
      { slug: 'ring-bearers', name: 'Ring-bearers' },
    ],
    likesCount: 42,
    isLiked: false,
    commentsCount: 7,
    attributes: {
      gender: 'male',
      birthDate: 'TA 2968',
      deathDate: '?',
      hair: 'brown curly',
      eyes: 'blue',
      height: "3'6\"",
      weapon: 'Sting',
      clothing: 'Elven cloak, mithril shirt',
      notableFor: 'Destroyed the One Ring',
    },
  },

  'shire': {
    slug: 'shire',
    names: ['The Shire', 'Shire'],
    article: {
      text: 'The Shire is a region in Eriador...',
      imageUrl: '/images/shire.jpg',
      createdAt: '2024-02-10T12:00:00Z',
      updatedAt: '2025-03-01T09:15:00Z',
    },
    relations: { outgoing: {}, incoming: {} },
    categories: [{ slug: 'regions', name: 'Regions' }],
    likesCount: 128,
    isLiked: true,
    commentsCount: 15,
    attributes: {
      area: '18,000 sq mi',
      population: '~15,000 Hobbits',
      founded: 'TA 1601',
      notableFor: 'Home of the Hobbits',
    },
  },
  
  'one-ring': {
    slug: 'one-ring',
    names: ['The One Ring', 'One Ring'],
    article: {
      text: 'The One Ring was an artifact of great power created by the Dark Lord Sauron...',
      imageUrl: '/images/one-ring.jpg',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    relations: {
      outgoing: {},
      incoming: {
        owns: [
          {
            from: {
              slug: 'frodo-baggins',
              type: 'character',
              name: 'Frodo Baggins',
              imageUrl: '/images/frodo.jpg',
            },
            properties: { acquired: 'TA 3001' },
          },
        ],
      },
    },
    categories: [{ slug: 'artifacts', name: 'Artifacts' }],
    likesCount: 256,
    isLiked: false,
    commentsCount: 32,
    attributes: {
      material: 'Gold',
      inscription: 'Ash nazg durbatulûk...',
      power: 'Invisibility, corruption, control over other Rings',
      createdBy: 'Sauron',
      destroyed: 'TA 3019',
    },
  },
};