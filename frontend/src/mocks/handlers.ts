import { http, HttpResponse } from 'msw';
import { mockRootCategories, mockCategory } from './data/categories';


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
];