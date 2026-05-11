export interface MockUser {
  username: string;
  email: string;
  role: 'viewer' | 'admin';
  avatar_url: string | null;
  created_at: string;
  comments_count: number;
  likedPages?: Array<{ slug: string; type: string; name: string; image_url: string }>;
}

// Исходный список пользователей
export let mockUsers: MockUser[] = [
  {
    username: 'admin',
    email: 'admin@lotr.com',
    role: 'admin',
    avatar_url: null,
    created_at: new Date().toISOString(),
    comments_count: 5,
  },
  {
    username: 'john',
    email: 'john@example.com',
    role: 'viewer',
    avatar_url: null,
    created_at: new Date(Date.now() - 86400000).toISOString(),
    comments_count: 2,
  },
  {
    username: 'frodo',
    email: 'frodo@shire.me',
    role: 'viewer',
    avatar_url: null,
    created_at: new Date(Date.now() - 172800000).toISOString(),
    comments_count: 12,
    likedPages: [
      { slug: 'aragorn', type: 'character', name: 'Aragorn', image_url: '' },
    ],
  },
];

// Функции для обновления
export const updateUserRole = (username: string, newRole: 'viewer' | 'admin') => {
  const user = mockUsers.find(u => u.username === username);
  if (user) user.role = newRole;
};

export const deleteUser = (username: string) => {
  mockUsers = mockUsers.filter(u => u.username !== username);
};

export const getUserByUsername = (username: string) => mockUsers.find(u => u.username === username);