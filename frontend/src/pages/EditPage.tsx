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
          properties: {},
        })) as RelationItem[],
      }));
      setIncomingGroups(inGroups);
    }
  }, [pageData]);

  // Обработчики для групп связей
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
      alert('At least one name must be specified');
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

    // Формируем исходящие связи
    const outgoingObj: Record<string, any[]> = {};
    outgoingGroups.forEach(group => {
      if (group.relationType && group.items.length) {
        outgoingObj[group.relationType] = group.items.map(item => {
          return {
            slug: item.target?.slug || '',
            properties: {},
          };
        });
      }
    });

    // Формируем входящие связи
    const incomingObj: Record<string, any[]> = {};
    incomingGroups.forEach(group => {
      if (group.relationType && group.items.length) {
        incomingObj[group.relationType] = group.items.map(item => {
          return {
            slug: item.from?.slug || '',
            properties: {},
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
      let errorMsg = 'Update failed.';
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

  if (isLoading) return <div>loading...</div>;
  if (error) return <div>Loading error</div>;
  if (!page) return <div>Page not found</div>;

  return (
    <div className="edit-page">
      <h1>Editing: {pageData.names[0]}</h1>
      <form onSubmit={handleSubmit}>
        <section className="basic-info">
          <h2>Basic info</h2>
          <label>Names (comma separated)</label>
          <input value={namesInput || ''} onChange={e => setNamesInput(e.target.value)} />
          <label>Image (URL)</label>
          <input value={articleImage_url ?? ''} onChange={e => setArticleImage_url(e.target.value)} />
          <label>Description</label>
          <textarea rows={10} value={articleText ?? ''} onChange={e => setArticleText(e.target.value)} />
        </section>

        <section>
          <h2>Attributes</h2>
          {currentEntityType === 'character' && (
            <div className="attribute-row">
              <label>Titles (separated by commas)</label>
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
                Clear
              </button>
            </div>
          )}
          {currentEntityType === 'character' && (
            <div className="attribute-row">
              <label>Gender</label>
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
                Clear
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
                  placeholder="Value"
                />
                <button type="button" onClick={() => clearAttributeValue(key)}>Clear</button>
              </div>
            ))}
        </section>

        {/* Исходящие связи */}
        <section>
          <h2>Outgoing relations</h2>
          {outgoingGroups.map((group, gIdx) => (
            <div key={gIdx} className="relation-group">
              <div className="relation-group-header">
                <label>Relation type:</label>
                <input
                  value={group.relationType ?? ''}
                  onChange={e => updateOutgoingGroupType(gIdx, e.target.value)}
                  placeholder="for example, friend_of"
                />
                <button type="button" onClick={() => removeOutgoingGroup(gIdx)}>Удалить группу</button>
              </div>
              {group.items.map((item, iIdx) => (
                <div key={iIdx} className="relation-item">
                  <div className="relation-field">
                    <label>target slug:</label>
                    <input
                      value={item.target?.slug ?? ''}
                      onChange={e => updateOutgoingItem(gIdx, iIdx, 'target.slug', e.target.value)}
                      placeholder="slug"
                    />
                  </div>
                  <div className="relation-field">
                    <label>target type:</label>
                    <input
                      value={item.target?.type ?? ''}
                      onChange={e => updateOutgoingItem(gIdx, iIdx, 'target.type', e.target.value)}
                      placeholder="character, location..."
                    />
                  </div>
                  <div className="relation-field">
                    <label>target name:</label>
                    <input
                      value={item.target?.name ?? ''}
                      onChange={e => updateOutgoingItem(gIdx, iIdx, 'target.name', e.target.value)}
                      placeholder="Name"
                    />
                  </div>
                  <div className="relation-field">
                    <label>target image_url:</label>
                    <input
                      value={item.target?.image_url ?? ''}
                      onChange={e => updateOutgoingItem(gIdx, iIdx, 'target.image_url', e.target.value)}
                      placeholder="image URL"
                    />
                  </div>
                  <button type="button" onClick={() => removeOutgoingItem(gIdx, iIdx)}>Delete relation</button>
                </div>
              ))}
              <button type="button" onClick={() => addOutgoingItem(gIdx)}>+ Add relationship of this type</button>
            </div>
          ))}
          <button type="button" onClick={() => setShowAddOutgoingForm(true)}>+ Add new outgoing relation</button>
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
          <h2>Incoming relation</h2>
          {incomingGroups.map((group, gIdx) => (
            <div key={gIdx} className="relation-group">
              <div className="relation-group-header">
                <label>Relation type:</label>
                <input
                  value={group.relationType ?? ''}
                  onChange={e => updateIncomingGroupType(gIdx, e.target.value)}
                  placeholder="for example, member_of"
                />
                <button type="button" onClick={() => removeIncomingGroup(gIdx)}>Удалить группу</button>
              </div>
              {group.items.map((item, iIdx) => (
                <div key={iIdx} className="relation-item">
                  <div className="relation-field">
                    <label>source slug:</label>
                    <input
                      value={item.from?.slug ?? ''}
                      onChange={e => updateIncomingItem(gIdx, iIdx, 'from.slug', e.target.value)}
                      placeholder="slug"
                    />
                  </div>
                  <div className="relation-field">
                    <label>source typeа:</label>
                    <input
                      value={item.from?.type ?? ''}
                      onChange={e => updateIncomingItem(gIdx, iIdx, 'from.type', e.target.value)}
                      placeholder="character, location..."
                    />
                  </div>
                  <div className="relation-field">
                    <label>source name:</label>
                    <input
                      value={item.from?.name ?? ''}
                      onChange={e => updateIncomingItem(gIdx, iIdx, 'from.name', e.target.value)}
                      placeholder="Name"
                    />
                  </div>
                  <div className="relation-field">
                    <label>source image_url:</label>
                    <input
                      value={item.from?.image_url ?? ''}
                      onChange={e => updateIncomingItem(gIdx, iIdx, 'from.image_url', e.target.value)}
                      placeholder="image URL"
                    />
                  </div>
                  <button type="button" onClick={() => removeIncomingItem(gIdx, iIdx)}>Delete relation</button>
                </div>
              ))}
              <button type="button" onClick={() => addIncomingItem(gIdx)}>+ Add relationship of this type</button>
            </div>
          ))}
          <button type="button" onClick={() => setShowAddIncomingForm(true)}>+ Add new incoming relation</button>
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
            {updateMutation.isPending ? 'Saving...' : 'Save changes'}
          </button>
          <button type="button" onClick={() => navigate(`/entity/${currentEntityType}/${slug}`)}>Cancel</button>
        </div>
      </form>
    </div>
  );
};

export default EditPage;