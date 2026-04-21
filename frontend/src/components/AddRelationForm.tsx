import { useEffect, useState } from 'react';
import { useDebounce } from '../hooks/useDebounce';

interface AddRelationFormProps {
  direction: 'outgoing' | 'incoming';
  onAdd: (relationType: string, relation: any) => void;
  currentEntityType: string;
  onCancel: () => void;
}

const AddRelationForm: React.FC<AddRelationFormProps> = ({ direction, onAdd, currentEntityType, onCancel }) => {
  const [nodeTypes, setNodeTypes] = useState<{ type: string; label: string }[]>([]);
  const [relationTypes, setRelationTypes] = useState<any[]>([]);
  const [selectedTargetType, setSelectedTargetType] = useState('');
  const [selectedRelationType, setSelectedRelationType] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const debouncedQuery = useDebounce(searchQuery, 300);

  useEffect(() => {
    fetch('/api/v1/meta/node-types').then(r => r.json()).then(setNodeTypes);
    fetch('/api/v1/meta/relation-types').then(r => r.json()).then(setRelationTypes);
  }, []);

  // Фильтрация типов связей в зависимости от направления
  const availableRelationTypes = relationTypes.filter(rel => {
    if (direction === 'outgoing') {
      return rel.from.includes(currentEntityType) && rel.to.includes(selectedTargetType);
    } else {
      return rel.from.includes(selectedTargetType) && rel.to.includes(currentEntityType);
    }
  });

  useEffect(() => {
    if (!debouncedQuery || debouncedQuery.length < 2 || !selectedTargetType) {
      setSearchResults([]);
      return;
    }
    setIsLoading(true);
    fetch(`/api/v1/search/?q=${encodeURIComponent(debouncedQuery)}&types=${selectedTargetType}&limit=10`)
      .then(r => r.json())
      .then(data => {
        setSearchResults(data);
        setIsLoading(false);
      });
  }, [debouncedQuery, selectedTargetType]);

  const handleSubmit = () => {
    if (!selectedRelationType || !selectedTarget) return;
    const newRelation = {
      [direction === 'outgoing' ? 'target' : 'from']: {
        slug: selectedTarget.slug,
        type: selectedTarget.type,
        name: selectedTarget.name,
        image_url: selectedTarget.image_url || '',
      },
      properties: {},
    };
    onAdd(selectedRelationType, newRelation);
  };

  return (
    <div className="add-relation-form">
      <h4>Add {direction === 'outgoing' ? 'outgoing' : 'incoming'} relation</h4>
      <div>
        <label>Target entity type:</label>
        <select value={selectedTargetType} onChange={e => setSelectedTargetType(e.target.value)}>
          <option value="">Select...</option>
          {nodeTypes.map(nt => <option key={nt.type} value={nt.type}>{nt.label}</option>)}
        </select>
      </div>
      {selectedTargetType && (
        <div>
          <label>Relation type:</label>
          <select value={selectedRelationType} onChange={e => setSelectedRelationType(e.target.value)}>
            <option value="">Select...</option>
            {availableRelationTypes.map(rel => <option key={rel.type} value={rel.type}>{rel.label}</option>)}
          </select>
        </div>
      )}
      {selectedRelationType && (
        <div>
          <label>Entity search:</label>
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Enter name..."
          />
          {isLoading && <div>Loading...</div>}
          {searchResults.length > 0 && (
            <ul className="search-results">
              {searchResults.map(res => (
                <li key={res.slug} onClick={() => setSelectedTarget(res)}>
                  {res.name} ({res.type})
                </li>
              ))}
            </ul>
          )}
          {selectedTarget && <div>Selected: {selectedTarget.name}</div>}
        </div>
      )}
      <div className="form-actions">
        <button type="button" onClick={handleSubmit} disabled={!selectedTarget || selectedTargetType !== selectedTarget.type}>
          Add
        </button>
        <button type="button" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  );
};

export default AddRelationForm;