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
  target?: { slug: string; type: string; name: string; image_url: string };
  from?: { slug: string; type: string; name: string; image_url: string };
  properties: Record<string, any>;
  propertiesString?: string;
}
interface RelationGroup { relationType: string; items: RelationItem[]; }

const CreatePage: React.FC = () => {
  const { type } = useParams<{ type: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Общие поля
  const [namesInput, setNamesInput] = useState('');
  const [description, setDescription] = useState('');
  const [image_url, setimage_url] = useState('');

  // Связи (общие)
  const [outgoingGroups, setOutgoingGroups] = useState<RelationGroup[]>([]);
  const [incomingGroups, setIncomingGroups] = useState<RelationGroup[]>([]);
  const [showAddOutgoingForm, setShowAddOutgoingForm] = useState(false);
  const [showAddIncomingForm, setShowAddIncomingForm] = useState(false);

  // --- Специфичные поля для разных типов ---
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

  const [location_type, setLocation_type] = useState('');
  const [population, setPopulation] = useState('');
  const [creation_date, setCreation_date] = useState('');
  const [destruction_date, setDestruction_date] = useState('');
  const [locationnotable_for, setLocationnotable_for] = useState('');

  const [event_type, setEvent_type] = useState('');
  const [start_date, setStart_date] = useState('');
  const [end_date, setEnd_date] = useState('');
  const [casualties, setCasualties] = useState('');
  const [eventnotable_for, setEventnotable_for] = useState('');

  const [item_type, setItem_type] = useState('');
  const [material, setMaterial] = useState('');
  const [itemnotable_for, setItemnotable_for] = useState('');

  const [lifespan, setLifespan] = useState('');
  const [avg_height, setAvg_height] = useState('');
  const [raceHair, setRaceHair] = useState('');
  const [raceEyes, setRaceEyes] = useState('');
  const [skin, setSkin] = useState('');
  const [weaponry, setWeaponry] = useState('');
  const [raceClothing, setRaceClothing] = useState('');
  const [distinctions, setDistinctions] = useState('');

  const [organization_type, setorganization_type] = useState('');
  const [founded_date, setFounded_date] = useState('');
  const [dissolved_date, setDissolved_date] = useState('');
  const [orgClothing, setOrgClothing] = useState('');
  const [orgWeaponry, setOrgWeaponry] = useState('');
  const [purpose, setPurpose] = useState('');
  const [orgnotable_for, setOrgnotable_for] = useState('');

  const [family, setFamily] = useState('');

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

  // --- Функции для управления связями (как в EditPage) ---
  const updateOutgoingGroupType = (groupIndex: number, newType: string) => {
    setOutgoingGroups(prev => prev.map((g, i) => i === groupIndex ? { ...g, relationType: newType } : g));
  };
  const addOutgoingItem = (groupIndex: number) => {
    setOutgoingGroups(prev => prev.map((g, i) => i === groupIndex ? {
      ...g,
      items: [...g.items, { target: { slug: '', type: '', name: '', image_url: '' }, properties: {} }]
    } : g));
  };
  const removeOutgoingItem = (groupIndex: number, itemIndex: number) => {
    setOutgoingGroups(prev => prev.map((g, i) => i === groupIndex ? {
      ...g,
      items: g.items.filter((_, idx) => idx !== itemIndex)
    } : g));
  };
  const updateOutgoingItem = (groupIndex: number, itemIndex: number, field: string, value: any) => {
    setOutgoingGroups(prev => prev.map((g, i) => {
      if (i !== groupIndex) return g;
      const newItems = [...g.items];
      if (field.startsWith('target.')) {
        const targetField = field.split('.')[1];
        (newItems[itemIndex].target as any)[targetField] = value;
      } else if (field === 'properties') {
        newItems[itemIndex].propertiesString = value;
        // Пытаемся распарсить, чтобы обновить properties (опционально)
        try {
          newItems[itemIndex].properties = JSON.parse(value);
        } catch (e) {}
      }
      return { ...g, items: newItems };
    }));
  };
  const removeOutgoingGroup = (groupIndex: number) => {
    setOutgoingGroups(prev => prev.filter((_, i) => i !== groupIndex));
  };

  const updateIncomingGroupType = (groupIndex: number, newType: string) => {
    setIncomingGroups(prev => prev.map((g, i) => i === groupIndex ? { ...g, relationType: newType } : g));
  };
  const addIncomingItem = (groupIndex: number) => {
    setIncomingGroups(prev => prev.map((g, i) => i === groupIndex ? {
      ...g,
      items: [...g.items, { from: { slug: '', type: '', name: '', image_url: '' }, properties: {} }]
    } : g));
  };
  const removeIncomingItem = (groupIndex: number, itemIndex: number) => {
    setIncomingGroups(prev => prev.map((g, i) => i === groupIndex ? {
      ...g,
      items: g.items.filter((_, idx) => idx !== itemIndex)
    } : g));
  };
  const updateIncomingItem = (groupIndex: number, itemIndex: number, field: string, value: any) => {
    setIncomingGroups(prev => prev.map((g, i) => {
      if (i !== groupIndex) return g;
      const newItems = [...g.items];
      if (field.startsWith('from.')) {
        const fromField = field.split('.')[1];
        (newItems[itemIndex].from as any)[fromField] = value;
      } else if (field === 'properties') {
        newItems[itemIndex].propertiesString = value;
        try {
          newItems[itemIndex].properties = JSON.parse(value);
        } catch (e) {}
      }
      return { ...g, items: newItems };
    }));
  };
  const removeIncomingGroup = (groupIndex: number) => {
    setIncomingGroups(prev => prev.filter((_, i) => i !== groupIndex));
  };

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

    const common = {
      slug,
      names: namesArray,
      article: {
        text: description,
        image_url: image_url || undefined,
      },
      categories: [],
    };

    let attributes: Record<string, any> = {};

    switch (type) {
      case 'character': {
        const titlesArray = parseCommaSeparated(titlesInput);
        if (gender) attributes.gender = gender;
        if (birth_date) attributes.birth_date = birth_date;
        if (death_date) attributes.death_date = death_date;
        if (hair) attributes.hair = hair;
        if (eyes) attributes.eyes = eyes;
        if (height) attributes.height = height;
        if (weapon) attributes.weapon = weapon;
        if (clothing) attributes.clothing = clothing;
        if (notable_for) attributes.notable_for = notable_for;
        if (titlesArray.length) attributes.titles = titlesArray;
        break;
      }
      case 'location':
        if (location_type) attributes.entity_type = location_type;
        if (population) attributes.population = population;
        if (creation_date) attributes.creation_date = creation_date;
        if (destruction_date) attributes.destruction_date = destruction_date;
        if (locationnotable_for) attributes.notable_for = locationnotable_for;
        break;
      case 'event':
        if (event_type) attributes.entity_type = event_type;
        if (start_date) attributes.start_date = start_date;
        if (end_date) attributes.end_date = end_date;
        if (casualties) attributes.casualties = casualties;
        if (eventnotable_for) attributes.notable_for = eventnotable_for;
        break;
      case 'item':
        if (item_type) attributes.entity_type = item_type;
        if (material) attributes.material = material;
        if (itemnotable_for) attributes.notable_for = itemnotable_for;
        break;
      case 'race':
        if (distinctions) attributes.distinctions = distinctions;
        if (lifespan) attributes.lifespan = lifespan;
        if (avg_height) attributes.avg_height = avg_height;
        if (raceHair) attributes.hair = raceHair;
        if (raceEyes) attributes.eyes = raceEyes;
        if (skin) attributes.skin = skin;
        if (weaponry) attributes.weaponry = weaponry;
        if (raceClothing) attributes.clothing = raceClothing;
        break;
      case 'organization':
        if (organization_type) attributes.entity_type = organization_type;
        if (founded_date) attributes.founded_date = founded_date;
        if (dissolved_date) attributes.dissolved_date = dissolved_date;
        if (orgClothing) attributes.clothing = orgClothing;
        if (orgWeaponry) attributes.weaponry = orgWeaponry;
        if (purpose) attributes.purpose = purpose;
        if (orgnotable_for) attributes.notable_for = orgnotable_for;
        break;
      case 'language':
        if (family) attributes.family = family;
        break;
      case 'timeline':
        if (abbreviation) attributes.abbreviation = abbreviation;
        if (timelineStart_date) attributes.start_date = timelineStart_date;
        if (timelineEnd_date) attributes.end_date = timelineEnd_date;
        break;
    }

    let requestBody: any = { ...common };
    if (Object.keys(attributes).length) requestBody.attributes = attributes;

    // Формируем relations с outgoing и incoming
    const outgoingRelationsObj: Record<string, any[]> = {};
    outgoingGroups.forEach(group => {
      if (group.relationType && group.items.length) {
        outgoingRelationsObj[group.relationType] = group.items.map(item => {
          let props = item.properties;
          // Если есть временная строка, пытаемся её распарсить
          if (item.propertiesString !== undefined) {
            try {
              props = JSON.parse(item.propertiesString);
            } catch (e) {
              console.warn('Invalid JSON for properties, using empty object');
              props = {};
            }
          }
          return {
            slug: item.target?.slug || '',
            properties: props,
          };
        });
      }
    });
    const incomingRelationsObj: Record<string, any[]> = {};
    incomingGroups.forEach(group => {
      if (group.relationType && group.items.length) {
        incomingRelationsObj[group.relationType] = group.items.map(item => {
          let props = item.properties;
          if (item.propertiesString !== undefined) {
            try {
              props = JSON.parse(item.propertiesString);
            } catch (e) {
              props = {};
            }
          }
          return {
            slug: item.from?.slug || '',
            properties: props,
          };
        });
      }
    });
    const hasOutgoing = Object.keys(outgoingRelationsObj).length > 0;
    const hasIncoming = Object.keys(incomingRelationsObj).length > 0;
    if (hasOutgoing || hasIncoming) {
      requestBody.relations = {};
      if (hasOutgoing) requestBody.relations.outgoing = outgoingRelationsObj;
      if (hasIncoming) requestBody.relations.incoming = incomingRelationsObj;
    }

    try {
      const result = await createMutation.mutateAsync({ data: requestBody });
      const newSlug = result.slug || result.data?.slug;
      await queryClient.invalidateQueries({ queryKey: [`/${type}s`] });
      navigate(`/entity/${type}/${newSlug}`);
    } catch (err: any) {
      console.error('Creation failed:', err);
      const serverError = err.response?.data;
      let errorMessage = 'Ошибка создания.';
      if (serverError?.error?.message) {
        errorMessage = serverError.error.message;
      } else if (serverError?.message) {
        errorMessage = serverError.message;
      } else if (typeof serverError === 'string') {
        errorMessage = serverError;
      }
      alert(errorMessage);
    }
  };

  const renderSpecificFields = () => {
    switch (type) {
      case 'character':
        return (
          <section key="attributes">
            <h2>Атрибуты персонажа</h2>
            <div className="attribute-row"><label>Пол</label><select value={gender} onChange={e=>setGender(e.target.value)}><option value="unknown">Не указано</option><option value="male">Мужской</option><option value="female">Женский</option></select></div>
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
            <div className="attribute-row"><label>Тип события</label><input value={event_type} onChange={e=>setEvent_type(e.target.value)} /></div>
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
            <div className="attribute-row"><label>Тип предмета</label><input value={item_type} onChange={e=>setItem_type(e.target.value)} /></div>
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
          <input value={image_url} onChange={e => setimage_url(e.target.value)} />
          <label>Описание</label>
          <textarea rows={10} value={description} onChange={e => setDescription(e.target.value)} />
        </section>

        {renderSpecificFields()}

        {/* Исходящие связи */}
        <section>
          <h2>Исходящие связи</h2>
          {outgoingGroups.map((group, gIdx) => (
            <div key={gIdx} className="relation-group">
              <div className="relation-group-header">
                <label>Тип связи:</label>
                <input
                  value={group.relationType ?? ''}
                  onChange={e => updateOutgoingGroupType(gIdx, e.target.value)}
                  placeholder="например, friend_of"
                />
                <button type="button" onClick={() => removeOutgoingGroup(gIdx)}>Удалить группу</button>
              </div>
              {group.items.map((item, iIdx) => (
                <div key={iIdx} className="relation-item">
                  <div className="relation-field">
                    <label>slug цели:</label>
                    <input
                      value={item.target?.slug ?? ''}
                      onChange={e => updateOutgoingItem(gIdx, iIdx, 'target.slug', e.target.value)}
                      placeholder="slug"
                    />
                  </div>
                  <div className="relation-field">
                    <label>type цели:</label>
                    <input
                      value={item.target?.type ?? ''}
                      onChange={e => updateOutgoingItem(gIdx, iIdx, 'target.type', e.target.value)}
                      placeholder="character, location..."
                    />
                  </div>
                  <div className="relation-field">
                    <label>name цели:</label>
                    <input
                      value={item.target?.name ?? ''}
                      onChange={e => updateOutgoingItem(gIdx, iIdx, 'target.name', e.target.value)}
                      placeholder="Отображаемое имя"
                    />
                  </div>
                  <div className="relation-field">
                    <label>image_url цели:</label>
                    <input
                      value={item.target?.image_url ?? ''}
                      onChange={e => updateOutgoingItem(gIdx, iIdx, 'target.image_url', e.target.value)}
                      placeholder="URL изображения"
                    />
                  </div>
                  <div className="relation-field">
                    <label>Свойства (JSON):</label>
                    <textarea
                      rows={2}
                      value={item.propertiesString !== undefined ? item.propertiesString : JSON.stringify(item.properties, null, 2)}
                      onChange={e => updateOutgoingItem(gIdx, iIdx, 'properties', e.target.value)}
                      placeholder='{"ключ": "значение"}'
                    />
                  </div>
                  <button type="button" onClick={() => removeOutgoingItem(gIdx, iIdx)}>Удалить связь</button>
                </div>
              ))}
              <button type="button" onClick={() => addOutgoingItem(gIdx)}>+ Добавить связь этого типа</button>
            </div>
          ))}
          <button type="button" onClick={() => setShowAddOutgoingForm(true)}>+ Добавить новую исходящую связь</button>
          {showAddOutgoingForm && (
            <AddRelationForm
              direction="outgoing"
              onAdd={handleAddOutgoingRelation}
              currentEntityType={type!}
              onCancel={() => setShowAddOutgoingForm(false)}
            />
          )}
        </section>

        {/* Входящие связи */}
        <section>
          <h2>Входящие связи</h2>
          {incomingGroups.map((group, gIdx) => (
            <div key={gIdx} className="relation-group">
              <div className="relation-group-header">
                <label>Тип связи:</label>
                <input
                  value={group.relationType ?? ''}
                  onChange={e => updateIncomingGroupType(gIdx, e.target.value)}
                  placeholder="например, member_of"
                />
                <button type="button" onClick={() => removeIncomingGroup(gIdx)}>Удалить группу</button>
              </div>
              {group.items.map((item, iIdx) => (
                <div key={iIdx} className="relation-item">
                  <div className="relation-field">
                    <label>slug источника:</label>
                    <input
                      value={item.from?.slug ?? ''}
                      onChange={e => updateIncomingItem(gIdx, iIdx, 'from.slug', e.target.value)}
                      placeholder="slug"
                    />
                  </div>
                  <div className="relation-field">
                    <label>type источника:</label>
                    <input
                      value={item.from?.type ?? ''}
                      onChange={e => updateIncomingItem(gIdx, iIdx, 'from.type', e.target.value)}
                      placeholder="character, location..."
                    />
                  </div>
                  <div className="relation-field">
                    <label>name источника:</label>
                    <input
                      value={item.from?.name ?? ''}
                      onChange={e => updateIncomingItem(gIdx, iIdx, 'from.name', e.target.value)}
                      placeholder="Отображаемое имя"
                    />
                  </div>
                  <div className="relation-field">
                    <label>image_url источника:</label>
                    <input
                      value={item.from?.image_url ?? ''}
                      onChange={e => updateIncomingItem(gIdx, iIdx, 'from.image_url', e.target.value)}
                      placeholder="URL изображения"
                    />
                  </div>
                  <div className="relation-field">
                    <label>Свойства (JSON):</label>
                    <textarea
                      rows={2}
                      value={item.propertiesString !== undefined ? item.propertiesString : JSON.stringify(item.properties, null, 2)}
                      onChange={e => updateIncomingItem(gIdx, iIdx, 'properties', e.target.value)}
                      placeholder='{"роль": "участник"}'
                    />
                  </div>
                  <button type="button" onClick={() => removeIncomingItem(gIdx, iIdx)}>Удалить связь</button>
                </div>
              ))}
              <button type="button" onClick={() => addIncomingItem(gIdx)}>+ Добавить связь этого типа</button>
            </div>
          ))}
          <button type="button" onClick={() => setShowAddIncomingForm(true)}>+ Добавить новую входящую связь</button>
          {showAddIncomingForm && (
            <AddRelationForm
              direction="incoming"
              onAdd={handleAddIncomingRelation}
              currentEntityType={type!}
              onCancel={() => setShowAddIncomingForm(false)}
            />
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