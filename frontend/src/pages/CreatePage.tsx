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

  // Основные поля
  const [namesInput, setNamesInput] = useState('');
  const [description, setDescription] = useState('');
  const [imageUrl, setImageUrl] = useState('');

  // Связи
  const [outgoingGroups, setOutgoingGroups] = useState<RelationGroup[]>([]);
  const [incomingGroups, setIncomingGroups] = useState<RelationGroup[]>([]);
  const [showAddOutgoingForm, setShowAddOutgoingForm] = useState(false);
  const [showAddIncomingForm, setShowAddIncomingForm] = useState(false);

  // Специфичные поля для разных типов
  // Персонаж
  const [gender, setGender] = useState('');
  const [birthDate, setBirthDate] = useState('');
  const [deathDate, setDeathDate] = useState('');
  const [hair, setHair] = useState('');
  const [eyes, setEyes] = useState('');
  const [height, setHeight] = useState('');
  const [weapon, setWeapon] = useState('');
  const [clothing, setClothing] = useState('');
  const [notableFor, setNotableFor] = useState('');
  const [titlesInput, setTitlesInput] = useState('');   // титулы через запятую

  // Локация
  const [area, setArea] = useState('');
  const [population, setPopulation] = useState('');
  const [founded, setFounded] = useState('');

  // Событие
  const [eventType, setEventType] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Предмет
  const [itemType, setItemType] = useState('');
  const [material, setMaterial] = useState('');

  // Раса
  const [distinctions, setDistinctions] = useState('');
  const [lifespan, setLifespan] = useState('');
  const [avgHeight, setAvgHeight] = useState('');

  // Организация
  const [orgType, setOrgType] = useState('');
  const [foundedDate, setFoundedDate] = useState('');
  const [purpose, setPurpose] = useState('');

  // Язык
  const [family, setFamily] = useState('');

  // Хронология
  const [abbreviation, setAbbreviation] = useState('');
  const [startYear, setStartYear] = useState('');
  const [endYear, setEndYear] = useState('');

  // Выбор мутации
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

  // Обработчики связей
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const namesArray = parseCommaSeparated(namesInput);
    if (namesArray.length === 0) return;
    const firstname = namesArray[0];
    const slug = generateSlug(firstname);

    const titlesArray = parseCommaSeparated(titlesInput);

    const common = {
      slug,
      names: namesArray,
      article: { text: description, imageUrl: imageUrl },
    };
    let requestBody: any = { ...common };

    const outgoing = outgoingGroups.reduce((acc, g) => {
      acc[g.relationType] = g.items.map(item => ({ target: item.target, properties: item.properties }));
      return acc;
    }, {} as Record<string, any>);
    const incoming = incomingGroups.reduce((acc, g) => {
      acc[g.relationType] = g.items.map(item => ({ from: item.from, properties: item.properties }));
      return acc;
    }, {} as Record<string, any>);
    requestBody.relations = { outgoing, incoming };

    switch (type) {
      case 'character':
        requestBody = {
          ...requestBody,
          gender: gender || undefined,
          birthDate: birthDate || undefined,
          deathDate: deathDate || undefined,
          hair: hair || undefined,
          eyes: eyes || undefined,
          height: height || undefined,
          weapon: weapon || undefined,
          clothing: clothing || undefined,
          notableFor: notableFor || undefined,
          titles: titlesArray.length ? titlesArray : undefined,
        };
        break;
      case 'location':
        requestBody = { ...requestBody, area, population, founded };
        break;
      case 'event':
        requestBody = { ...requestBody, eventType, startDate, endDate };
        break;
      case 'item':
        requestBody = { ...requestBody, itemType, material };
        break;
      case 'race':
        requestBody = { ...requestBody, distinctions, lifespan, avgHeight };
        break;
      case 'organization':
        requestBody = { ...requestBody, orgType, foundedDate, purpose };
        break;
      case 'language':
        requestBody = { ...requestBody, family };
        break;
      case 'script':
        break;
      case 'timeline':
        requestBody = { ...requestBody, abbreviation, startDate: startYear, endDate: endYear };
        break;
    }

    try {
      const result = await createMutation.mutateAsync({ data: requestBody });
      const newSlug = result.slug || result.data?.slug;
      navigate(`/entity/${type}/${newSlug}`);
    } catch (err) {
      console.error('Creation failed:', err);
    }
  };

  const renderSpecificFields = () => {
    switch (type) {
      case 'character':
        return (
          <section key="attributes">
            <h2>Атрибуты персонажа</h2>
            <div className="attribute-row"><label>Gender</label><select value={gender} onChange={e=>setGender(e.target.value)}><option value="">Не указано</option><option value="Male">Мужской</option><option value="Female">Женский</option></select></div>
            <div className="attribute-row"><label>Birth date</label><input value={birthDate} onChange={e=>setBirthDate(e.target.value)} /></div>
            <div className="attribute-row"><label>Death date</label><input value={deathDate} onChange={e=>setDeathDate(e.target.value)} /></div>
            <div className="attribute-row"><label>Hair</label><input value={hair} onChange={e=>setHair(e.target.value)} /></div>
            <div className="attribute-row"><label>Eyes</label><input value={eyes} onChange={e=>setEyes(e.target.value)} /></div>
            <div className="attribute-row"><label>Height</label><input value={height} onChange={e=>setHeight(e.target.value)} /></div>
            <div className="attribute-row"><label>Weapon</label><input value={weapon} onChange={e=>setWeapon(e.target.value)} /></div>
            <div className="attribute-row"><label>Clothing</label><input value={clothing} onChange={e=>setClothing(e.target.value)} /></div>
            <div className="attribute-row"><label>Notable for</label><input value={notableFor} onChange={e=>setNotableFor(e.target.value)} /></div>
            <div className="attribute-row"><label>Титулы (через запятую)</label><input value={titlesInput} onChange={e => setTitlesInput(e.target.value)}/>
            </div>
          </section>
        );
      case 'location':
        return (
          <section key="attributes">
            <h2>Атрибуты локации</h2>
            <div className="attribute-row"><label>Площадь</label><input value={area} onChange={e=>setArea(e.target.value)} /></div>
            <div className="attribute-row"><label>Население</label><input value={population} onChange={e=>setPopulation(e.target.value)} /></div>
            <div className="attribute-row"><label>Основана</label><input value={founded} onChange={e=>setFounded(e.target.value)} /></div>
          </section>
        );
      case 'event':
        return (
          <section key="attributes">
            <h2>Атрибуты события</h2>
            <div className="attribute-row"><label>Тип события</label><input value={eventType} onChange={e=>setEventType(e.target.value)} /></div>
            <div className="attribute-row"><label>Дата начала</label><input value={startDate} onChange={e=>setStartDate(e.target.value)} /></div>
            <div className="attribute-row"><label>Дата конца</label><input value={endDate} onChange={e=>setEndDate(e.target.value)} /></div>
          </section>
        );
      case 'item':
        return (
          <section key="attributes">
            <h2>Атрибуты предмета</h2>
            <div className="attribute-row"><label>Тип предмета</label><input value={itemType} onChange={e=>setItemType(e.target.value)} /></div>
            <div className="attribute-row"><label>Материал</label><input value={material} onChange={e=>setMaterial(e.target.value)} /></div>
          </section>
        );
      case 'race':
        return (
          <section key="attributes">
            <h2>Атрибуты расы</h2>
            <div className="attribute-row"><label>Отличительные черты</label><input value={distinctions} onChange={e=>setDistinctions(e.target.value)} /></div>
            <div className="attribute-row"><label>Продолжительность жизни</label><input value={lifespan} onChange={e=>setLifespan(e.target.value)} /></div>
            <div className="attribute-row"><label>Средний рост</label><input value={avgHeight} onChange={e=>setAvgHeight(e.target.value)} /></div>
          </section>
        );
      case 'organization':
        return (
          <section key="attributes">
            <h2>Атрибуты организации</h2>
            <div className="attribute-row"><label>Тип организации</label><input value={orgType} onChange={e=>setOrgType(e.target.value)} /></div>
            <div className="attribute-row"><label>Дата основания</label><input value={foundedDate} onChange={e=>setFoundedDate(e.target.value)} /></div>
            <div className="attribute-row"><label>Цель</label><input value={purpose} onChange={e=>setPurpose(e.target.value)} /></div>
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
            <div className="attribute-row"><label>Год начала</label><input value={startYear} onChange={e=>setStartYear(e.target.value)} /></div>
            <div className="attribute-row"><label>Год конца</label><input value={endYear} onChange={e=>setEndYear(e.target.value)} /></div>
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
          <label>Имена (через запятую, первое будет использовано для slug)</label>
          <input type="text" value={namesInput} onChange={e => setNamesInput(e.target.value)} placeholder="Frodo Baggins, Frodo, Ring-bearer" required />
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
          <button type="submit" disabled={createMutation.isPending}>{createMutation.isPending ? 'Создание...' : 'Создать'}</button>
          <button type="button" onClick={() => navigate(`/${type}s`)}>Отмена</button>
        </div>
      </form>
    </div>
  );
};

export default CreatePage;