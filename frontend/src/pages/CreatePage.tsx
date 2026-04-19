import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useCreateCharacter } from '../api/generated/characters/characters';
import { useCreateLocation } from '../api/generated/locations/locations';
import { useCreateEvent } from '../api/generated/events/events';
import { useCreateItem } from '../api/generated/items/items';
import { useCreateRace } from '../api/generated/races/races';
import { useCreateOrganization } from '../api/generated/organizations/organizations';
import { useCreateLanguage } from '../api/generated/languages/languages';
import { useCreateScript } from '../api/generated/scripts/scripts';
import { useCreateTimeline } from '../api/generated/timelines/timelines';

const CreatePage: React.FC = () => {
  const { type } = useParams<{ type: string }>();
  const navigate = useNavigate();

  // Состояния формы
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [imageUrl, setImageUrl] = useState('');

  // Выбираем нужную мутацию в зависимости от типа
  const createCharacter = useCreateCharacter();
  const createLocation = useCreateLocation();
  const createEvent = useCreateEvent();
  const createItem = useCreateItem();
  const createRace = useCreateRace();
  const createOrganization = useCreateOrganization();
  const createLanguage = useCreateLanguage();
  const createScript = useCreateScript();
  const createTimeline = useCreateTimeline();

  let createMutation: any = null;
  let entityTypeForRedirect = type;

  switch (type) {
    case 'character':
      createMutation = createCharacter;
      break;
    case 'location':
      createMutation = createLocation;
      break;
    case 'event':
      createMutation = createEvent;
      break;
    case 'item':
      createMutation = createItem;
      break;
    case 'race':
      createMutation = createRace;
      break;
    case 'organization':
      createMutation = createOrganization;
      break;
    case 'language':
      createMutation = createLanguage;
      break;
    case 'script':
      createMutation = createScript;
      break;
    case 'timeline':
      createMutation = createTimeline;
      break;
    default:
      return <div>Неизвестный тип сущности</div>;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name) return;
    // Формируем тело запроса
    const requestBody: any = {
      name,
      article: {
        text: description,
        imageUrl,
      },
      // Пока пустые атрибуты и связи
      attributes: {},
      relations: {},
    };
    try {
      const result = await createMutation.mutateAsync({ data: requestBody });
      // Предполагается, что ответ содержит slug новой сущности
      const newSlug = result.data.slug;
      navigate(`/entity/${type}/${newSlug}`);
    } catch (err) {
      console.error('Creation failed:', err);
    }
  };

  return (
    <div className="edit-page">
      <h1>Создание новой сущности: {type}</h1>
      <form onSubmit={handleSubmit}>
        <section className="basic-info">
          <h2>Основная информация</h2>
          <label>Название (обязательно)</label>
          <input value={name} onChange={e => setName(e.target.value)} required />
          <label>Изображение (URL)</label>
          <input value={imageUrl} onChange={e => setImageUrl(e.target.value)} />
          <label>Описание</label>
          <textarea rows={10} value={description} onChange={e => setDescription(e.target.value)} />
        </section>
        {/* Добавить блоки для атрибутов и связей */}
        <div className="edit-actions">
          <button type="submit" disabled={createMutation.isPending}>
            {createMutation.isPending ? 'Создание...' : 'Создать'}
          </button>
          <button type="button" onClick={() => navigate(`/${type}s`)}>Отмена</button>
        </div>
      </form>
    </div>
  );
};

export default CreatePage;