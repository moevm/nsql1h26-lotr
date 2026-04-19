export const mockCategoryEntities: Record<string, any> = {
  "characters": {
    slug: "characters",
    name: "Персонажи",
    description: "Все персонажи Средиземья",
    parentSlug: null,
    parent: null,
    children: [
      { slug: "good-characters", name: "Добрые персонажи", pageCount: 89 },
      { slug: "evil-characters", name: "Злые персонажи", pageCount: 45 }
    ],
    pages: {
      count: 150,
      next: null,
      previous: null,
      results: [
        { slug: "aragorn", type: "character", name: "Арагорн", imageUrl: "/images/aragorn.jpg" },
        { slug: "frodo", type: "character", name: "Фродо", imageUrl: "/images/frodo.jpg" },
        { slug: "gandalf", type: "character", name: "Гэндальф", imageUrl: "/images/gandalf.jpg" },
        { slug: "legolas", type: "character", name: "Леголас", imageUrl: "/images/legolas.jpg" },
        { slug: "gimli", type: "character", name: "Гимли", imageUrl: "/images/gimli.jpg" },
        { slug: "saruman", type: "character", name: "Саруман", imageUrl: "/images/saruman.jpg" },
        { slug: "sauron", type: "character", name: "Саурон", imageUrl: "/images/sauron.jpg" }
      ]
    }
  },
  "good-characters": {
    slug: "good-characters",
    name: "Добрые персонажи",
    description: "Персонажи, сражающиеся на стороне Свободных народов",
    parentSlug: "characters",
    parent: { slug: "characters", name: "Персонажи" },
    children: [
      { slug: "hobbits-of-the-shire", name: "Хоббиты Шира", pageCount: 14 },
      { slug: "fellowship-members", name: "Члены Братства Кольца", pageCount: 9 }
    ],
    pages: {
      count: 89,
      next: null,
      previous: null,
      results: [
        { slug: "aragorn", type: "character", name: "Арагорн", imageUrl: "/images/aragorn.jpg" },
        { slug: "frodo", type: "character", name: "Фродо", imageUrl: "/images/frodo.jpg" },
        { slug: "gandalf", type: "character", name: "Гэндальф", imageUrl: "/images/gandalf.jpg" },
        { slug: "legolas", type: "character", name: "Леголас", imageUrl: "/images/legolas.jpg" },
        { slug: "gimli", type: "character", name: "Гимли", imageUrl: "/images/gimli.jpg" }
      ]
    }
  },
  "hobbits-of-the-shire": {
    slug: "hobbits-of-the-shire",
    name: "Хоббиты Шира",
    description: "Хоббиты, жившие в Шире",
    parentSlug: "good-characters",
    parent: { slug: "good-characters", name: "Добрые персонажи" },
    children: [],
    pages: {
      count: 14,
      next: null,
      previous: null,
      results: [
        { slug: "frodo", type: "character", name: "Фродо", imageUrl: "/images/frodo.jpg" },
        { slug: "sam", type: "character", name: "Сэм", imageUrl: "/images/sam.jpg" },
        { slug: "merry", type: "character", name: "Мерри", imageUrl: "/images/merry.jpg" },
        { slug: "pippin", type: "character", name: "Пиппин", imageUrl: "/images/pippin.jpg" }
      ]
    }
  },
  "locations": {
    slug: "locations",
    name: "Локации",
    description: "Географические места Средиземья",
    parentSlug: null,
    parent: null,
    children: [
      { slug: "shire", name: "Шир", pageCount: 12 },
      { slug: "gondor", name: "Гондор", pageCount: 18 }
    ],
    pages: {
      count: 80,
      next: null,
      previous: null,
      results: [
        { slug: "rivendell", type: "location", name: "Ривенделл", imageUrl: "/images/rivendell.jpg" },
        { slug: "mordor", type: "location", name: "Мордор", imageUrl: "/images/mordor.jpg" },
        { slug: "shire", type: "location", name: "Шир", imageUrl: "/images/shire.jpg" }
      ]
    }
  }
};