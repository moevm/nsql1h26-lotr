// src/pages/CreatePage.tsx
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useCreateCharacter } from '../api/generated/characters/characters';
import { useCreateLocation } from '../api/generated/locations/locations';
import { useCreateEvent } from '../api/generated/events/events';
import { useCreateItem } from '../api/generated/items/items';
import { useCreateRace } from '../api/generated/races/races';
import { useCreateOrganization } from '../api/generated/organizations/organizations';
import { useCreateLanguage } from '../api/generated/languages/languages';
import { useCreateScript } from '../api/generated/scripts/scripts';
import { useCreateTimeline } from '../api/generated/timelines/timelines';
import AddRelationForm from '../components/AddRelationForm';

interface RelationItem {
  target?: { slug: string; type: string; name: string; imageUrl: string };
  from?: { slug: string; type: string; name: string; imageUrl: string };
  properties: Record<string, any>;
}
interface RelationGroup { relationType: string; items: RelationItem[]; }

const CreatePage: React.FC = () => {
  const { type } = useParams<{ type: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Общие поля
  const [namesInput, setNamesInput] = useState('');
  const [description, setDescription] = useState('');
  const [imageUrl, setImageUrl] = useState('');

  // Связи (общие)
  const [outgoingGroups, setOutgoingGroups] = useState<RelationGroup[]>([]);
  const [incomingGroups, setIncomingGroups] = useState<RelationGroup[]>([]);
  const [showAddOutgoingForm, setShowAddOutgoingForm] = useState(false);
  const [showAddIncomingForm, setShowAddIncomingForm] = useState(false);

  // --- Специфичные поля для разных типов ---
  // Персонаж (оставляем как было, но можно добавить недостающие поля, если нужно)
  const [gender, setGender] = useState('');
  const [birth_date, setBirth_date] = useState('');
  const [death_date, setDeath_date] = useState('');
  const [hair, setHair] = useState('');
  const [eyes, setEyes] = useState('');
  const [height, setHeight] = useState('');
  const [weapon, setWeapon] = useState('');
  const [clothing, setClothing] = useState('');
  const [notable_for, setNotable_for] = useState('');
  const [titlesInput, setTitlesInput] = useState('');

  // Локация
  const [location_type, setLocation_type] = useState('');
  const [population, setPopulation] = useState('');
  const [creation_date, setCreation_date] = useState('');
  const [destruction_date, setDestruction_date] = useState('');
  const [locationnotable_for, setLocationnotable_for] = useState('');

  // Событие
  const [eventType, setEventType] = useState('');
  const [start_date, setStart_date] = useState('');
  const [end_date, setEnd_date] = useState('');
  const [casualties, setCasualties] = useState('');
  const [eventnotable_for, setEventnotable_for] = useState('');

  // Предмет
  const [itemType, setItemType] = useState('');
  const [material, setMaterial] = useState('');
  const [itemnotable_for, setItemnotable_for] = useState('');

  // Раса
  const [lifespan, setLifespan] = useState('');
  const [avg_height, setAvg_height] = useState('');
  const [raceHair, setRaceHair] = useState('');
  const [raceEyes, setRaceEyes] = useState('');
  const [skin, setSkin] = useState('');
  const [weaponry, setWeaponry] = useState('');
  const [raceClothing, setRaceClothing] = useState('');
  const [distinctions, setDistinctions] = useState('');

  // Организация
  const [organization_type, setorganization_type] = useState('');
  const [founded_date, setFounded_date] = useState('');
  const [dissolved_date, setDissolved_date] = useState('');
  const [orgClothing, setOrgClothing] = useState('');
  const [orgWeaponry, setOrgWeaponry] = useState('');
  const [purpose, setPurpose] = useState('');
  const [orgnotable_for, setOrgnotable_for] = useState('');

  // Язык
  const [family, setFamily] = useState('');

  // Хронология
  const [abbreviation, setAbbreviation] = useState('');
  const [timelineStart_date, setTimelineStart_date] = useState('');
  const [timelineEnd_date, setTimelineEnd_date] = useState('');

  // Мутации
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
  switch (type) {
    case 'character': createMutation = createCharacter; break;
    case 'location':  createMutation = createLocation; break;
    case 'event':     createMutation = createEvent; break;
    case 'item':      createMutation = createItem; break;
    case 'race':      createMutation = createRace; break;
    case 'organization': createMutation = createOrganization; break;
    case 'language':  createMutation = createLanguage; break;
    case 'script':    createMutation = createScript; break;
    case 'timeline':  createMutation = createTimeline; break;
    default: return <div>Неизвестный тип сущности</div>;
  }

  const generateSlug = (input: string) => input
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');

  const parseCommaSeparated = (input: string): string[] => {
    return input.split(',').map(s => s.trim()).filter(s => s !== '');
  };

  // Обработчики связей (аналогично EditPage)
  const handleAddOutgoingRelation = (relType: string, relation: RelationItem) => {
    const idx = outgoingGroups.findIndex(g => g.relationType === relType);
    if (idx !== -1) {
      setOutgoingGroups(prev => prev.map((g, i) => i === idx ? { ...g, items: [...g.items, relation] } : g));
    } else {
      setOutgoingGroups(prev => [...prev, { relationType: relType, items: [relation] }]);
    }
    setShowAddOutgoingForm(false);
  };
  const handleAddIncomingRelation = (relType: string, relation: RelationItem) => {
    const idx = incomingGroups.findIndex(g => g.relationType === relType);
    if (idx !== -1) {
      setIncomingGroups(prev => prev.map((g, i) => i === idx ? { ...g, items: [...g.items, relation] } : g));
    } else {
      setIncomingGroups(prev => [...prev, { relationType: relType, items: [relation] }]);
    }
    setShowAddIncomingForm(false);
  };

  // Валидация обязательных полей
  const validateRequired = (): string | null => {
    if (!namesInput.trim()) return 'Необходимо указать хотя бы одно имя.';
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errorMsg = validateRequired();
    if (errorMsg) {
      alert(errorMsg);
      return;
    }

    const namesArray = parseCommaSeparated(namesInput);
    const slug = generateSlug(namesArray[0]);

    // Общая структура
    const now = new Date().toISOString();
    const common = {
      slug,
      names: namesArray,
      article: {
        text: description,
        imageUrl: imageUrl || undefined,
      },
      categories: [],
      relations: {},
    };

    let requestBody: any = { ...common };

    // Добавляем специфичные поля
    switch (type) {
      case 'character': {
        const titlesArray = parseCommaSeparated(titlesInput);
        requestBody = {
          ...requestBody,
          gender: gender || undefined,
          birth_date: birth_date || undefined,
          death_date: death_date || undefined,
          hair: hair || undefined,
          eyes: eyes || undefined,
          height: height || undefined,
          weapon: weapon || undefined,
          clothing: clothing || undefined,
          notable_for: notable_for || undefined,
          titles: titlesArray.length ? titlesArray : undefined,
        };
        break;
      }
      case 'location':
        requestBody = {
          ...requestBody,
          location_type: location_type || undefined,
          population: population || undefined,
          creation_date: creation_date || undefined,
          destruction_date: destruction_date || undefined,
          notable_for: locationnotable_for || undefined,
        };
        break;
      case 'event':
        requestBody = {
          ...requestBody,
          eventType: eventType || undefined,
          start_date: start_date || undefined,
          end_date: end_date || undefined,
          casualties: casualties || undefined,
          notable_for: eventnotable_for || undefined,
        };
        break;
      case 'item':
        requestBody = {
          ...requestBody,
          itemType: itemType || undefined,
          material: material || undefined,
          notable_for: itemnotable_for || undefined,
        };
        break;
      case 'race':
        requestBody = {
          ...requestBody,
          lifespan: lifespan || undefined,
          avg_height: avg_height || undefined,
          hair: raceHair || undefined,
          eyes: raceEyes || undefined,
          skin: skin || undefined,
          weaponry: weaponry || undefined,
          clothing: raceClothing || undefined,
          distinctions: distinctions || undefined,
        };
        break;
      case 'organization':
        requestBody = {
          ...requestBody,
          organization_type: organization_type || undefined,
          founded_date: founded_date || undefined,
          dissolved_date: dissolved_date || undefined,
          clothing: orgClothing || undefined,
          weaponry: orgWeaponry || undefined,
          purpose: purpose || undefined,
          notable_for: orgnotable_for || undefined,
        };
        break;
      case 'language':
        requestBody = {
          ...requestBody,
          family: family || undefined,
        };
        break;
      case 'script':
        // нет дополнительных полей
        break;
      case 'timeline':
        requestBody = {
          ...requestBody,
          abbreviation: abbreviation || undefined,
          start_date: timelineStart_date || undefined,
          end_date: timelineEnd_date || undefined,
        };
        break;
    }

    // Добавляем связи (преобразуем группы в плоский объект, как для редактирования)
    const relationsObj: Record<string, any[]> = {};
    outgoingGroups.forEach(group => {
      if (group.relationType && group.items.length) {
        relationsObj[group.relationType] = group.items.map(item => ({
          slug: item.target?.slug || '',
          properties: item.properties || {},
        }));
      }
    });
    incomingGroups.forEach(group => {
      if (group.relationType && group.items.length) {
        if (!relationsObj[group.relationType]) relationsObj[group.relationType] = [];
        relationsObj[group.relationType].push(...group.items.map(item => ({
          slug: item.from?.slug || '',
          properties: item.properties || {},
        })));
      }
    });
    if (Object.keys(relationsObj).length) {
      requestBody.relations = relationsObj;
    }

    try {
      const result = await createMutation.mutateAsync({ data: requestBody });
      const newSlug = result.slug || result.data?.slug;
      await queryClient.invalidateQueries({ queryKey: [`/${type}s`] });
      navigate(`/entity/${type}/${newSlug}`);
    } catch (err) {
      console.error('Creation failed:', err);
      alert('Ошибка создания. Проверьте консоль.');
    }
  };

  const renderSpecificFields = () => {
    switch (type) {
      case 'character':
        return (
          <section key="attributes">
            <h2>Атрибуты персонажа</h2>
            <div className="attribute-row"><label>Пол</label><select value={gender} onChange={e=>setGender(e.target.value)}><option value="">Не указано</option><option value="Male">Мужской</option><option value="Female">Женский</option></select></div>
            <div className="attribute-row"><label>Дата рождения</label><input value={birth_date} onChange={e=>setBirth_date(e.target.value)} /></div>
            <div className="attribute-row"><label>Дата смерти</label><input value={death_date} onChange={e=>setDeath_date(e.target.value)} /></div>
            <div className="attribute-row"><label>Волосы</label><input value={hair} onChange={e=>setHair(e.target.value)} /></div>
            <div className="attribute-row"><label>Глаза</label><input value={eyes} onChange={e=>setEyes(e.target.value)} /></div>
            <div className="attribute-row"><label>Рост</label><input value={height} onChange={e=>setHeight(e.target.value)} /></div>
            <div className="attribute-row"><label>Оружие</label><input value={weapon} onChange={e=>setWeapon(e.target.value)} /></div>
            <div className="attribute-row"><label>Одежда</label><input value={clothing} onChange={e=>setClothing(e.target.value)} /></div>
            <div className="attribute-row"><label>Чем известен</label><input value={notable_for} onChange={e=>setNotable_for(e.target.value)} /></div>
            <div className="attribute-row"><label>Титулы (через запятую)</label><input value={titlesInput} onChange={e=>setTitlesInput(e.target.value)} placeholder="King, Hero" /></div>
          </section>
        );
      case 'location':
        return (
          <section key="attributes">
            <h2>Атрибуты локации</h2>
            <div className="attribute-row"><label>Тип локации</label><input value={location_type} onChange={e=>setLocation_type(e.target.value)} /></div>
            <div className="attribute-row"><label>Население</label><input value={population} onChange={e=>setPopulation(e.target.value)} /></div>
            <div className="attribute-row"><label>Дата создания</label><input value={creation_date} onChange={e=>setCreation_date(e.target.value)} /></div>
            <div className="attribute-row"><label>Дата разрушения</label><input value={destruction_date} onChange={e=>setDestruction_date(e.target.value)} /></div>
            <div className="attribute-row"><label>Чем известна</label><input value={locationnotable_for} onChange={e=>setLocationnotable_for(e.target.value)} /></div>
          </section>
        );
      case 'event':
        return (
          <section key="attributes">
            <h2>Атрибуты события</h2>
            <div className="attribute-row"><label>Тип события</label><input value={eventType} onChange={e=>setEventType(e.target.value)} /></div>
            <div className="attribute-row"><label>Дата начала</label><input value={start_date} onChange={e=>setStart_date(e.target.value)} /></div>
            <div className="attribute-row"><label>Дата конца</label><input value={end_date} onChange={e=>setEnd_date(e.target.value)} /></div>
            <div className="attribute-row"><label>Потери</label><input value={casualties} onChange={e=>setCasualties(e.target.value)} /></div>
            <div className="attribute-row"><label>Чем известно</label><input value={eventnotable_for} onChange={e=>setEventnotable_for(e.target.value)} /></div>
          </section>
        );
      case 'item':
        return (
          <section key="attributes">
            <h2>Атрибуты предмета</h2>
            <div className="attribute-row"><label>Тип предмета</label><input value={itemType} onChange={e=>setItemType(e.target.value)} /></div>
            <div className="attribute-row"><label>Материал</label><input value={material} onChange={e=>setMaterial(e.target.value)} /></div>
            <div className="attribute-row"><label>Чем известен</label><input value={itemnotable_for} onChange={e=>setItemnotable_for(e.target.value)} /></div>
          </section>
        );
      case 'race':
        return (
          <section key="attributes">
            <h2>Атрибуты расы</h2>
            <div className="attribute-row"><label>Отличительные черты</label><input value={distinctions} onChange={e=>setDistinctions(e.target.value)} /></div>
            <div className="attribute-row"><label>Продолжительность жизни</label><input value={lifespan} onChange={e=>setLifespan(e.target.value)} /></div>
            <div className="attribute-row"><label>Средний рост</label><input value={avg_height} onChange={e=>setAvg_height(e.target.value)} /></div>
            <div className="attribute-row"><label>Волосы</label><input value={raceHair} onChange={e=>setRaceHair(e.target.value)} /></div>
            <div className="attribute-row"><label>Глаза</label><input value={raceEyes} onChange={e=>setRaceEyes(e.target.value)} /></div>
            <div className="attribute-row"><label>Кожа</label><input value={skin} onChange={e=>setSkin(e.target.value)} /></div>
            <div className="attribute-row"><label>Оружие</label><input value={weaponry} onChange={e=>setWeaponry(e.target.value)} /></div>
            <div className="attribute-row"><label>Одежда</label><input value={raceClothing} onChange={e=>setRaceClothing(e.target.value)} /></div>
          </section>
        );
      case 'organization':
        return (
          <section key="attributes">
            <h2>Атрибуты организации</h2>
            <div className="attribute-row"><label>Тип организации</label><input value={organization_type} onChange={e=>setorganization_type(e.target.value)} /></div>
            <div className="attribute-row"><label>Дата основания</label><input value={founded_date} onChange={e=>setFounded_date(e.target.value)} /></div>
            <div className="attribute-row"><label>Дата роспуска</label><input value={dissolved_date} onChange={e=>setDissolved_date(e.target.value)} /></div>
            <div className="attribute-row"><label>Одежда</label><input value={orgClothing} onChange={e=>setOrgClothing(e.target.value)} /></div>
            <div className="attribute-row"><label>Оружие</label><input value={orgWeaponry} onChange={e=>setOrgWeaponry(e.target.value)} /></div>
            <div className="attribute-row"><label>Цель</label><input value={purpose} onChange={e=>setPurpose(e.target.value)} /></div>
            <div className="attribute-row"><label>Чем известна</label><input value={orgnotable_for} onChange={e=>setOrgnotable_for(e.target.value)} /></div>
          </section>
        );
      case 'language':
        return (
          <section key="attributes">
            <h2>Атрибуты языка</h2>
            <div className="attribute-row"><label>Семья</label><input value={family} onChange={e=>setFamily(e.target.value)} /></div>
          </section>
        );
      case 'timeline':
        return (
          <section key="attributes">
            <h2>Атрибуты хронологии</h2>
            <div className="attribute-row"><label>Аббревиатура</label><input value={abbreviation} onChange={e=>setAbbreviation(e.target.value)} /></div>
            <div className="attribute-row"><label>Дата начала</label><input value={timelineStart_date} onChange={e=>setTimelineStart_date(e.target.value)} /></div>
            <div className="attribute-row"><label>Дата конца</label><input value={timelineEnd_date} onChange={e=>setTimelineEnd_date(e.target.value)} /></div>
          </section>
        );
      default:
        return null;
    }
  };

  return (
    <div className="edit-page">
      <h1>Создание новой сущности: {type}</h1>
      <form onSubmit={handleSubmit}>
        <section className="basic-info">
          <h2>Основная информация</h2>
          <label>Имена (через запятую) *</label>
          <input type="text" value={namesInput} onChange={e => setNamesInput(e.target.value)} required />
          <label>Изображение (URL)</label>
          <input value={imageUrl} onChange={e => setImageUrl(e.target.value)} />
          <label>Описание</label>
          <textarea rows={10} value={description} onChange={e => setDescription(e.target.value)} />
        </section>

        {renderSpecificFields()}

        <section>
          <h2>Исходящие связи</h2>
          {outgoingGroups.map((group, idx) => (
            <div key={idx} className="relation-group">
              <div><strong>{group.relationType}</strong></div>
              {group.items.map((item, i) => <div key={i}>→ {item.target?.name} ({item.target?.slug})</div>)}
            </div>
          ))}
          <button type="button" onClick={() => setShowAddOutgoingForm(true)}>+ Добавить исходящую связь</button>
          {showAddOutgoingForm && (
            <AddRelationForm direction="outgoing" onAdd={handleAddOutgoingRelation} currentEntityType={type!} onCancel={() => setShowAddOutgoingForm(false)} />
          )}
        </section>

        <section>
          <h2>Входящие связи</h2>
          {incomingGroups.map((group, idx) => (
            <div key={idx} className="relation-group">
              <div><strong>{group.relationType}</strong></div>
              {group.items.map((item, i) => <div key={i}>← {item.from?.name} ({item.from?.slug})</div>)}
            </div>
          ))}
          <button type="button" onClick={() => setShowAddIncomingForm(true)}>+ Добавить входящую связь</button>
          {showAddIncomingForm && (
            <AddRelationForm direction="incoming" onAdd={handleAddIncomingRelation} currentEntityType={type!} onCancel={() => setShowAddIncomingForm(false)} />
          )}
        </section>

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