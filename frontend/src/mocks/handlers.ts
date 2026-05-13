import { http, HttpResponse } from 'msw';
import { mockRootCategories, mockCategory } from './data/categories';
import { mockUsers, updateUserRole, deleteUser, getUserByUsername } from './data/users';
import { mockGlobalStats } from './data/analytics';

export const handlers = [
  http.get('/api/v1/categories', ({ request }) => {
    const url = new URL(request.url);
    const parent = url.searchParams.get('parent');
    if (parent === 'root') {
      return HttpResponse.json({ count: mockRootCategories.length, next: null, previous: null, results: mockRootCategories });
    }
    // Если нужен плоский список с другими параметрами, можно добавить логику
    return HttpResponse.json({ count: 0, next: null, previous: null, results: [] });
  }),
  http.get('/api/v1/categories/:slug', ({ params }) => {
    const { slug } = params;
    const category = mockCategory[slug as string];
    if (category) {
      return HttpResponse.json(category);
    }
    return new HttpResponse(null, { status: 404 });
  }),

  // GET /api/v1/users – список пользователей (с пагинацией и фильтрацией)
  http.get('/api/v1/users', ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('page_size') || '20');
    const usernameFilter = url.searchParams.get('username');
    const roleFilter = url.searchParams.get('role');
    let filtered = [...mockUsers];
    if (usernameFilter) {
      filtered = filtered.filter(u => u.username.includes(usernameFilter));
    }
    if (roleFilter) {
      filtered = filtered.filter(u => u.role === roleFilter);
    }
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const results = filtered.slice(start, end);
    return HttpResponse.json({
      count: filtered.length,
      next: end < filtered.length ? `/api/v1/users/?page=${page + 1}&page_size=${pageSize}` : null,
      previous: page > 1 ? `/api/v1/users/?page=${page - 1}&page_size=${pageSize}` : null,
      results: results.map(({ username, email, role, avatar_url, created_at }) => ({
        username, email, role, avatar_url, created_at,
      })),
    });
  }),

  // GET /api/v1/users/:username – публичный профиль
  http.get('/api/v1/users/:username', ({ params }) => {
    const { username } = params;
    const user = getUserByUsername(username as string);
    if (!user) return new HttpResponse(null, { status: 404 });
    return HttpResponse.json({
      username: user.username,
      avatar_url: user.avatar_url,
      created_at: user.created_at,
      comments_count: user.comments_count,
      liked_pages: user.likedPages || [],
    });
  }),

  // GET /api/v1/users/:username/liked – лайкнутые страницы (с пагинацией)
  http.get('/api/v1/users/:username/liked', ({ params, request }) => {
    const { username } = params;
    const user = getUserByUsername(username as string);
    if (!user) return new HttpResponse(null, { status: 404 });
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('page_size') || '20');
    const likedPages = user.likedPages || [];
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const results = likedPages.slice(start, end);
    return HttpResponse.json({
      count: likedPages.length,
      next: end < likedPages.length ? `/api/v1/users/${username}/liked?page=${page + 1}&page_size=${pageSize}` : null,
      previous: page > 1 ? `/api/v1/users/${username}/liked?page=${page - 1}&page_size=${pageSize}` : null,
      results,
    });
  }),

  // PATCH /api/v1/users/:username – изменение роли (только admin)
  http.patch('/api/v1/users/:username', async ({ params, request }) => {
    const { username } = params;
    const body = await request.json() as any;
    const { role } = body;
    if (!role || (role !== 'viewer' && role !== 'admin')) {
      return HttpResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Invalid role', fields: null } },
        { status: 400 }
      );
    }
    const user = getUserByUsername(username as string);
    if (!user) return new HttpResponse(null, { status: 404 });
    updateUserRole(username as string, role);
    return HttpResponse.json({
      username: user.username,
      email: user.email,
      role: user.role,
      avatar_url: user.avatar_url,
      created_at: user.created_at,
    });
  }),

  // DELETE /api/v1/users/:username – удаление пользователя
  http.delete('/api/v1/users/:username', ({ params }) => {
    const { username } = params;
    const user = getUserByUsername(username as string);
    if (!user) return new HttpResponse(null, { status: 404 });
    if (username === 'admin') {
      // Нельзя удалить админа (по логике, можно добавить любую проверку)
      return new HttpResponse(null, { status: 403 });
    }
    deleteUser(username as string);
    return new HttpResponse(null, { status: 204 });
  }),

  http.get('/api/v1/analytics/global', () => {
    return HttpResponse.json(mockGlobalStats);
  }),
];