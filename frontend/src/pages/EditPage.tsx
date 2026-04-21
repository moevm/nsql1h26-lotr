// src/pages/EditPage.tsx
import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { useGetPage, useUpdatePage } from '../api/generated/pages/pages';
import type { PageUpdateRequest } from '../api/generated/models';
import AddRelationForm from '../components/AddRelationForm';

interface RelationItem {
  target?: {
    slug: string;
    type: string;
    name: string;
    image_url: string;
  };
  from?: {
    slug: string;
    type: string;
    name: string;
    image_url: string;
  };
  properties: Record<string, any>;
  propertiesString?: string; // добавлено для временного хранения строки JSON
}

interface RelationGroup {
  relationType: string;
  items: RelationItem[];
}

const EditPage: React.FC = () => {
  const { type: currentEntityType, slug } = useParams<{ type: string; slug: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: page, isLoading, error } = useGetPage(slug!);
  const pageData = page as any;
  const updateMutation = useUpdatePage();
  const [initialAttributes, setInitialAttributes] = useState<Record<string, any>>({});

  const [_names, setNames] = useState<string[]>([]);
  const [namesInput, setNamesInput] = useState('');
  const [titlesInput, setTitlesInput] = useState('');
  const [genderInput, setGenderInput] = useState('');
  const [articleText, setArticleText] = useState('');
  const [articleImage_url, setArticleImage_url] = useState('');
  const [attributes, setAttributes] = useState<Record<string, any>>({});
  const [outgoingGroups, setOutgoingGroups] = useState<RelationGroup[]>([]);
  const [incomingGroups, setIncomingGroups] = useState<RelationGroup[]>([]);
  const [showAddOutgoingForm, setShowAddOutgoingForm] = useState(false);
  const [showAddIncomingForm, setShowAddIncomingForm] = useState(false);

  useEffect(() => {
    if (pageData) {
      setNames(pageData.names || []);
      setNamesInput((pageData.names || []).join(', '))
      setArticleText(pageData.article?.text || '');
      setArticleImage_url(pageData.article?.image_url || null);
      setAttributes(pageData.attributes || {});
      const genderValue = pageData.attributes?.gender;
      setGenderInput(genderValue && typeof genderValue === 'string' ? genderValue : '');
      const titlesAttr = pageData.attributes?.titles;
      if (Array.isArray(titlesAttr)) {
        setTitlesInput(titlesAttr.join(', '));
      } else {
        setTitlesInput('');
      }
      setInitialAttributes(pageData.attributes || {});

      const outGroups = Object.entries(pageData.relations?.outgoing || {}).map(([relType, items]) => ({
        relationType: relType,
        items: items as RelationItem[],
      }));
      setOutgoingGroups(outGroups);

      const inGroups = Object.entries(pageData.relations?.incoming || {}).map(([relType, items]) => ({
        relationType: relType,
        items: (items as any[]).map((item: any) => ({
          from: item.from,
          properties: item.properties,
        })) as RelationItem[],
      }));
      setIncomingGroups(inGroups);
    }
  }, [pageData]);

  // Обработчики для групп связей (модифицированы для propertiesString)
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
        // Сохраняем строку во временное поле
        newItems[itemIndex].propertiesString = value;
        // Пытаемся распарсить, чтобы обновить properties (опционально)
        try {
          newItems[itemIndex].properties = JSON.parse(value);
        } catch (e) { /* невалидный JSON – оставляем старые properties */ }
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

  const handleAddOutgoingRelation = (relationType: string, relation: RelationItem) => {
    const existingGroupIndex = outgoingGroups.findIndex(g => g.relationType === relationType);
    if (existingGroupIndex !== -1) {
      setOutgoingGroups(prev => prev.map((g, i) => i === existingGroupIndex ? {
        ...g,
        items: [...g.items, relation]
      } : g));
    } else {
      setOutgoingGroups(prev => [...prev, { relationType, items: [relation] }]);
    }
    setShowAddOutgoingForm(false);
  };
  const handleAddIncomingRelation = (relationType: string, relation: RelationItem) => {
    const existingGroupIndex = incomingGroups.findIndex(g => g.relationType === relationType);
    if (existingGroupIndex !== -1) {
      setIncomingGroups(prev => prev.map((g, i) => i === existingGroupIndex ? {
        ...g,
        items: [...g.items, relation]
      } : g));
    } else {
      setIncomingGroups(prev => [...prev, { relationType, items: [relation] }]);
    }
    setShowAddIncomingForm(false);
  };

  const clearAttributeValue = (key: string) => {
    setAttributes(prev => ({ ...prev, [key]: null }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const parsedNames = namesInput.split(',').map(s => s.trim()).filter(s => s !== '');
    if (parsedNames.length === 0) {
      alert('Необходимо указать хотя бы одно имя.');
      return;
    }

    const finalAttributes = { ...attributes };
    if (currentEntityType === 'character') {
      if (!genderInput) {
        finalAttributes.gender = null;
      } else {
        finalAttributes.gender = genderInput;
      }
      if (titlesInput.trim() === '') {
        finalAttributes.titles = null;
      } else {
        const titlesArray = titlesInput.split(',').map(s => s.trim()).filter(s => s !== '');
        finalAttributes.titles = titlesArray;
      }
    }
    Object.keys(initialAttributes).forEach(key => {
      if (!(key in attributes)) {
        finalAttributes[key] = null;
      }
    });
    const cleanedAttributes = Object.fromEntries(
      Object.entries(finalAttributes).filter(([_, v]) => v !== undefined)
    );

    // Формируем исходящие связи, парся propertiesString при наличии
    const outgoingObj: Record<string, any[]> = {};
    outgoingGroups.forEach(group => {
      if (group.relationType && group.items.length) {
        outgoingObj[group.relationType] = group.items.map(item => {
          let props = item.properties;
          if (item.propertiesString !== undefined) {
            try {
              props = JSON.parse(item.propertiesString);
            } catch (e) {
              console.warn('Invalid JSON for outgoing relation properties, using empty object');
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

    // Формируем входящие связи
    const incomingObj: Record<string, any[]> = {};
    incomingGroups.forEach(group => {
      if (group.relationType && group.items.length) {
        incomingObj[group.relationType] = group.items.map(item => {
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

    const updateData: PageUpdateRequest = {
      names: parsedNames,
      article: {
        text: articleText,
        image_url: articleImage_url,
      },
      attributes: cleanedAttributes,
      relations: {
        outgoing: outgoingObj,
        incoming: incomingObj,
      },
    };

    try {
      await updateMutation.mutateAsync({ slug: slug!, data: updateData });
      await queryClient.invalidateQueries({ queryKey: [`/pages/${slug}`] });
      navigate(`/entity/${currentEntityType}/${slug}`);
    } catch (err: any) {
      const serverError = err.response?.data;
      console.error('Update failed:', serverError || err.message);
      let errorMsg = 'Ошибка сохранения.';
      if (serverError?.error?.message) {
        errorMsg = serverError.error.message;
      } else if (serverError?.message) {
        errorMsg = serverError.message;
      } else if (typeof serverError === 'string') {
        errorMsg = serverError;
      }
      alert(errorMsg);
    }
  };

  if (isLoading) return <div>Загрузка...</div>;
  if (error) return <div>Ошибка загрузки</div>;
  if (!page) return <div>Страница не найдена</div>;

  return (
    <div className="edit-page">
      <h1>Редактирование: {pageData.names[0]}</h1>
      <form onSubmit={handleSubmit}>
        <section className="basic-info">
          <h2>Основная информация</h2>
          <label>Имена (через запятую)</label>
          <input value={namesInput || ''} onChange={e => setNamesInput(e.target.value)} />
          <label>Изображение (URL)</label>
          <input value={articleImage_url ?? ''} onChange={e => setArticleImage_url(e.target.value)} />
          <label>Описание</label>
          <textarea rows={10} value={articleText ?? ''} onChange={e => setArticleText(e.target.value)} />
        </section>

        <section>
          <h2>Атрибуты</h2>
          {currentEntityType === 'character' && (
            <div className="attribute-row">
              <label>Титулы (через запятую)</label>
              <input
                type="text"
                value={titlesInput}
                onChange={e => setTitlesInput(e.target.value)}
                placeholder="King, Hero, Lord of the Rings"
              />
              <button
                type="button"
                onClick={() => {
                  setTitlesInput('');
                  setAttributes(prev => {
                    const newAttrs = { ...prev };
                    delete newAttrs.titles;
                    return newAttrs;
                  });
                }}
              >
                Очистить
              </button>
            </div>
          )}
          {currentEntityType === 'character' && (
            <div className="attribute-row">
              <label>Пол</label>
              <select
                value={genderInput}
                onChange={e => setGenderInput(e.target.value)}
              >
                <option value="unknown">unknown</option>
                <option value="male">male</option>
                <option value="female">female</option>
              </select>
              <button
                type="button"
                onClick={() => setGenderInput('')}
              >
                Очистить
              </button>
            </div>
          )}
          {Object.entries(attributes)
            .filter(([key]) => key !== 'titles' && key !== 'gender')
            .map(([key, value]) => (
              <div key={key} className="attribute-row">
                <span className="attribute-key">{key}</span>
                <input
                  value={value === null ? '' : value}
                  onChange={e => {
                    const newValue = e.target.value === '' ? null : e.target.value;
                    setAttributes(prev => ({ ...prev, [key]: newValue }));
                  }}
                  placeholder="Значение"
                />
                <button type="button" onClick={() => clearAttributeValue(key)}>Очистить</button>
              </div>
            ))}
        </section>

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
              onAdd={(relationType, relation) => handleAddOutgoingRelation(relationType, relation)}
              currentEntityType={currentEntityType!}
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
              onAdd={(relationType, relation) => handleAddIncomingRelation(relationType, relation)}
              currentEntityType={currentEntityType!}
              onCancel={() => setShowAddIncomingForm(false)}
            />
          )}
        </section>

        <div className="edit-actions">
          <button type="submit" disabled={updateMutation.isPending}>
            {updateMutation.isPending ? 'Сохранение...' : 'Сохранить изменения'}
          </button>
          <button type="button" onClick={() => navigate(`/entity/${currentEntityType}/${slug}`)}>Отмена</button>
        </div>
      </form>
    </div>
  );
};

export default EditPage;