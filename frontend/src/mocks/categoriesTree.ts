export const mockCategoriesTree = [
  {
    slug: "characters",
    name: "Персонажи",
    pageCount: 150,
    children: [
      {
        slug: "good-characters",
        name: "Добрые персонажи",
        pageCount: 89,
        children: [
          {
            slug: "hobbits-of-the-shire",
            name: "Хоббиты Шира",
            pageCount: 14,
            children: []
          },
          {
            slug: "fellowship-members",
            name: "Члены Братства Кольца",
            pageCount: 9,
            children: []
          }
        ]
      },
      {
        slug: "evil-characters",
        name: "Злые персонажи",
        pageCount: 45,
        children: []
      }
    ]
  },
  {
    slug: "locations",
    name: "Локации",
    pageCount: 80,
    children: [
      {
        slug: "shire",
        name: "Шир",
        pageCount: 12,
        children: []
      },
      {
        slug: "gondor",
        name: "Гондор",
        pageCount: 18,
        children: []
      }
    ]
  },
  {
    slug: "items",
    name: "Предметы",
    pageCount: 60,
    children: []
  }
];