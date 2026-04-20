import { http, HttpResponse } from 'msw';
import { mockCharacters } from './data/characters';
import { mockLocations } from './data/locations';
import { mockEvents } from './data/events';
import { mockLanguages } from './data/languages';
import { mockRaces } from './data/races';
import { mockItems } from './data/items';
import { mockScripts } from './data/scripts';
import { mockOrganizations } from './data/organizations';
import { mockTimelines } from './data/timelines';
import { mockPages } from './data/pages';
import { nodeTypes, relationTypes } from './data/meta';
import { mockUsers } from './data/users';


export const handlers = [
  http.get('/characters', () => {
    console.warn('Перехвачен запрос на /characters без /api. Исправьте источник.');
    return HttpResponse.json(mockCharacters);
  }),

  // POST /characters - создание (только для админов)
  http.post('/api/v1/characters/', async ({ request }) => {
    const body = await request.json() as any;
    
    // Генерируем slug из имени (упрощённо)
    const slug = body.name.toLowerCase().replace(/\s+/g, '-');
    const now = new Date().toISOString();
    
    // Создаём объект новой страницы (CharacterPage)
    const newPage = {
      slug,
      names: [body.name],
      article: {
        text: body.article?.text || '',
        imageUrl: body.article?.imageUrl || '',
        createdAt: now,
        updatedAt: now,
      },
      attributes: body.attributes || {},
      relations: body.relations || {},
      categories: [],
      likesCount: 0,
      isLiked: false,
      commentsCount: 0,
    };
    
    // Сохраняем в мок (например, в mockPages)
    mockPages[slug] = newPage;
    
    // Возвращаем структуру, ожидаемую клиентом
    return HttpResponse.json({ data: newPage }, { status: 201 });
  }),

  // Получение страницы
  http.get('/api/v1/pages/:slug', ({ params }) => {
    const { slug } = params;
    const page = mockPages[slug as string];
    if (page) {
      return HttpResponse.json(page);
    }
    return new HttpResponse(null, { status: 404 });
  }),

  // Редактирование страницы
  http.patch('/api/v1/pages/:slug', async ({ params, request }) => {
    const { slug } = params;
    const page = mockPages[slug as string];
    if (!page) return new HttpResponse(null, { status: 404 });
    const body = await request.json() as any;
    
    // Мутируем существующий объект
    if (body.names) page.names = body.names;
    if (body.article) page.article = { ...page.article, ...body.article };
    if (body.attributes) page.attributes = body.attributes;
    if (body.relations) page.relations = body.relations;
    
    return HttpResponse.json(page);
  }),

  http.get('/api/v1/search/', ({ request }) => {
    const url = new URL(request.url);
    const q = url.searchParams.get('q') || '';
    const types = url.searchParams.get('types')?.split(',') || [];
    const limit = parseInt(url.searchParams.get('limit') || '5');

    const allEntities = [
      ...(mockCharacters.results || []).map(e => ({ ...e, type: 'character' })),
      ...(mockLocations.results || []).map(e => ({ ...e, type: 'location' })),
      ...(mockOrganizations.results || []).map(e => ({ ...e, type: 'organization' })),
      ...(mockLanguages.results || []).map(e => ({ ...e, type: 'language' })),
    ];
    const filtered = allEntities.filter(e =>
      e.name.toLowerCase().includes(q.toLowerCase()) &&
      (types.length === 0 || types.includes(e.type))
    ).slice(0, limit);
    return HttpResponse.json(filtered);
  }),

  http.get('/api/v1/auth/me', ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) return new HttpResponse(null, { status: 401 });
    const token = authHeader.split(' ')[1];
    // В моках токен — это просто строка, декодируем username
    try {
      const username = atob(token).split(':')[0];
      const user = mockUsers.find(u => u.username === username);
      if (!user) return new HttpResponse(null, { status: 401 });
      return HttpResponse.json({
        username: user.username,
        email: user.email,
        role: user.role,
      });
    } catch {
      return new HttpResponse(null, { status: 401 });
    }
  }),

  http.get('/api/v1/characters', () => HttpResponse.json(mockCharacters)),
  http.get('/api/v1/locations', () => HttpResponse.json(mockLocations)),
  http.get('/api/v1/events', () => HttpResponse.json(mockEvents)),
  http.get('/api/v1/languages', () => HttpResponse.json(mockLanguages)),
  http.get('/api/v1/races', () => HttpResponse.json(mockRaces)),
  http.get('/api/v1/items', () => HttpResponse.json(mockItems)),
  http.get('/api/v1/scripts', () => HttpResponse.json(mockScripts)),
  http.get('/api/v1/organizations', () => HttpResponse.json(mockOrganizations)),
  http.get('/api/v1/timelines', () => HttpResponse.json(mockTimelines)),
  http.get('/api/v1/meta/node-types', () => HttpResponse.json(nodeTypes)),
  http.get('/api/v1/meta/relation-types', () => HttpResponse.json(relationTypes)),
];