import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { useGetPage, useUpdatePage } from '../api/generated/pages/pages';
import type { PageResponse, PageUpdateRequest } from '../api/generated/models';
import AddRelationForm from '../components/AddRelationForm';

interface RelationItem {
  target?: {
    slug: string;
    type: string;
    name: string;
    imageUrl: string;
  };
  from?: {
    slug: string;
    type: string;
    name: string;
    imageUrl: string;
  };
  properties: Record<string, any>;
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
  const updateMutation = useUpdatePage();

  const [names, setNames] = useState<string[]>([]);
  const [articleText, setArticleText] = useState('');
  const [articleImageUrl, setArticleImageUrl] = useState('');
  const [attributes, setAttributes] = useState<Record<string, any>>({});
  const [outgoingGroups, setOutgoingGroups] = useState<RelationGroup[]>([]);
  const [incomingGroups, setIncomingGroups] = useState<RelationGroup[]>([]);
  const [showAddOutgoingForm, setShowAddOutgoingForm] = useState(false);
  const [showAddIncomingForm, setShowAddIncomingForm] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (page) {
      setNames(page.names || []);
      setArticleText(page.article?.text || '');
      setArticleImageUrl(page.article?.imageUrl || '');
      setAttributes(page.attributes || {});

      const outGroups = Object.entries(page.relations?.outgoing || {}).map(([relType, items]) => ({
        relationType: relType,
        items: items as RelationItem[],
      }));
      setOutgoingGroups(outGroups);

      const inGroups = Object.entries(page.relations?.incoming || {}).map(([relType, items]) => ({
        relationType: relType,
        items: items.map(item => ({
          from: item.from,
          properties: item.properties,
        })) as RelationItem[],
      }));
      setIncomingGroups(inGroups);
    }
  }, [page]);

  // Обработчики для групп связей
  const updateOutgoingGroupType = (groupIndex: number, newType: string) => {
    setOutgoingGroups(prev => prev.map((g, i) => i === groupIndex ? { ...g, relationType: newType } : g));
  };
  const addOutgoingItem = (groupIndex: number) => {
    setOutgoingGroups(prev => prev.map((g, i) => i === groupIndex ? {
      ...g,
      items: [...g.items, { target: { slug: '', type: '', name: '', imageUrl: '' }, properties: {} }]
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
        newItems[itemIndex].target![targetField] = value;
      } else if (field === 'properties') {
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
      items: [...g.items, { from: { slug: '', type: '', name: '', imageUrl: '' }, properties: {} }]
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
        newItems[itemIndex].from![fromField] = value;
      } else if (field === 'properties') {
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

  const addAttribute = () => {
    const newKey = prompt('Введите название атрибута');
    if (newKey && !attributes[newKey]) {
      setAttributes(prev => ({ ...prev, [newKey]: '' }));
    }
  };
  const removeAttribute = (key: string) => {
    const newAttributes = { ...attributes };
    delete newAttributes[key];
    setAttributes(newAttributes);
  };
  const updateAttributeKey = (oldKey: string, newKey: string) => {
    if (newKey === oldKey || !newKey) return;
    const newAttributes = { ...attributes };
    newAttributes[newKey] = newAttributes[oldKey];
    delete newAttributes[oldKey];
    setAttributes(newAttributes);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');

    // Очищаем атрибуты от null/undefined и пустых строк
    const cleanedAttributes = Object.fromEntries(
      Object.entries(attributes).filter(([_, v]) => v != null && v !== '')
    );

    const outgoingObj: Record<string, any[]> = {};
    outgoingGroups.forEach(group => {
      if (group.relationType && group.items.length) {
        outgoingObj[group.relationType] = group.items.map(item => ({
          slug: item.target?.slug || '',
          properties: item.properties || {},
        }));
      }
    });

    const incomingObj: Record<string, any[]> = {};
    incomingGroups.forEach(group => {
      if (group.relationType && group.items.length) {
        incomingObj[group.relationType] = group.items.map(item => ({
          slug: item.from?.slug || '',
          properties: item.properties || {},
        }));
      }
    });

    const updateData: PageUpdateRequest = {
      names,
      article: {
        text: articleText,
        imageUrl: articleImageUrl,
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
      setErrorMessage(serverError?.error?.message || 'Ошибка сохранения. Проверьте данные.');
    }
  };

  if (isLoading) return <div>Загрузка...</div>;
  if (error) return <div>Ошибка загрузки</div>;
  if (!page) return <div>Страница не найдена</div>;

  return (
    <div className="edit-page">
      <h1>Редактирование: {page.names[0]}</h1>
      {errorMessage && <div className="error-message">{errorMessage}</div>}
      <form onSubmit={handleSubmit}>
        {/* Основная информация */}
        <section className="basic-info">
          <h2>Основная информация</h2>
          <label>Название (первое имя)</label>
          <input value={names[0] || ''} onChange={e => setNames([e.target.value, ...names.slice(1)])} />
          <label>Изображение (URL)</label>
          <input value={articleImageUrl ?? ''} onChange={e => setArticleImageUrl(e.target.value)} />
          <label>Описание</label>
          <textarea rows={10} value={articleText ?? ''} onChange={e => setArticleText(e.target.value)} />
        </section>

        {/* Атрибуты */}
        <section>
          <h2>Атрибуты</h2>
          {Object.entries(attributes).map(([key, value]) => (
            <div key={key} className="attribute-row">
              <input
                value={key}
                onChange={e => updateAttributeKey(key, e.target.value)}
                placeholder="Название атрибута"
              />
              <input
                value={value ?? ''}
                onChange={e => setAttributes(prev => ({ ...prev, [key]: e.target.value }))}
                placeholder="Значение"
              />
              <button type="button" onClick={() => removeAttribute(key)}>Удалить</button>
            </div>
          ))}
          <button type="button" onClick={addAttribute}>+ Добавить атрибут</button>
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
                    <label>imageUrl цели:</label>
                    <input
                      value={item.target?.imageUrl ?? ''}
                      onChange={e => updateOutgoingItem(gIdx, iIdx, 'target.imageUrl', e.target.value)}
                      placeholder="URL изображения"
                    />
                  </div>
                  <div className="relation-field">
                    <label>Свойства (JSON):</label>
                    <textarea
                      rows={2}
                      value={JSON.stringify(item.properties, null, 2)}
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
                    <label>imageUrl источника:</label>
                    <input
                      value={item.from?.imageUrl ?? ''}
                      onChange={e => updateIncomingItem(gIdx, iIdx, 'from.imageUrl', e.target.value)}
                      placeholder="URL изображения"
                    />
                  </div>
                  <div className="relation-field">
                    <label>Свойства (JSON):</label>
                    <textarea
                      rows={2}
                      value={JSON.stringify(item.properties, null, 2)}
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