export interface MockUser {
  id: number;
  username: string;
  email: string;
  password: string;
  role: 'user' | 'admin';
}

// Начальные тестовые пользователи
export const mockUsers: MockUser[] = [
  {
    id: 1,
    username: 'john',
    email: 'john@example.com',
    password: '123456',
    role: 'user',
  },
  {
    id: 2,
    username: 'admin',
    email: 'admin@lotr.com',
    password: 'admin123',
    role: 'admin',
  },
];

// Вспомогательные функции для работы с пользователями в моках
export const findUserByUsername = (username: string): MockUser | undefined => {
  return mockUsers.find(u => u.username === username);
};

export const findUserByEmail = (email: string): MockUser | undefined => {
  return mockUsers.find(u => u.email === email);
};

export const createUser = (
  username: string,
  email: string,
  password: string,
  role: 'user' | 'admin' = 'user'
): MockUser => {
  const newId = Math.max(...mockUsers.map(u => u.id), 0) + 1;
  const newUser: MockUser = { id: newId, username, email, password, role };
  mockUsers.push(newUser);
  return newUser;
};

export const updateUser = (
  id: number,
  updates: Partial<{ username: string; email: string; password: string }>
): MockUser | undefined => {
  const user = mockUsers.find(u => u.id === id);
  if (user) {
    Object.assign(user, updates);
    return user;
  }
  return undefined;
};