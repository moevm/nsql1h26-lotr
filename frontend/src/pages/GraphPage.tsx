import { useState, useEffect, useRef } from 'react';
import { useDebounce } from '../hooks/useDebounce';
import FilterSection from '../components/FilterSection';

interface NodeType {
  type: string;
  label: string;
  pluralLabel: string;
}

interface RelationType {
  type: string;
  label: string;
  from: string[];
  to: string[];
}

const GraphPage: React.FC = () => {
  const [nodeTypes, setNodeTypes] = useState<NodeType[]>([]);
  const [relationTypes, setRelationTypes] = useState<RelationType[]>([]);
  const [loadingMeta, setLoadingMeta] = useState(true);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Выбранная сущность
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<any>(null);
  const [isSearching, setIsSearching] = useState(false);
  const debouncedQuery = useDebounce(searchQuery, 300);

  // Фильтры
  const [selectedNodeTypes, setSelectedNodeTypes] = useState<string[]>([]);
  // Для каждого типа узла храним выбранные типы связей
  const [relationFilters, setRelationFilters] = useState<Record<string, string[]>>({});
  const [depth, setDepth] = useState<1 | 2>(1);

  useEffect(() => {
    Promise.all([
      fetch('/api/v1/meta/node-types').then(r => r.json()),
      fetch('/api/v1/meta/relation-types').then(r => r.json())
    ]).then(([nodeData, relData]) => {
      setNodeTypes(nodeData);
      setRelationTypes(relData);
      setLoadingMeta(false);
    }).catch(err => {
      console.error('Failed to load meta data', err);
      setLoadingMeta(false);
    });
  }, []);

  // Поиск сущности
  useEffect(() => {
    if (!debouncedQuery || debouncedQuery.length < 2) {
      setSearchResults([]);
      return;
    }
    setIsSearching(true);
    fetch(`/api/v1/search/?q=${encodeURIComponent(debouncedQuery)}&limit=10`)
      .then(r => r.json())
      .then(data => {
        setSearchResults(data);
        setIsSearching(false);
      });
  }, [debouncedQuery]);

  // Закрытие выпадающего списка поиска при клике вне
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setSearchResults([]);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectEntity = (entity: any) => {
    setSelectedEntity(entity);
    setSearchQuery('');
    setSearchResults([]);
  };

  const handleNodeTypeToggle = (type: string) => {
    setSelectedNodeTypes(prev => {
      const newSet = prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type];
      // Если тип убран, удаляем и его фильтры связей
      if (!newSet.includes(type)) {
        setRelationFilters(prevFilters => {
          const newFilters = { ...prevFilters };
          delete newFilters[type];
          return newFilters;
        });
      } else {
        // Если добавлен, инициализируем пустым массивом
        setRelationFilters(prev => ({ ...prev, [type]: [] }));
      }
      return newSet;
    });
  };

  const handleRelationTypeToggle = (nodeType: string, relType: string) => {
    setRelationFilters(prev => ({
      ...prev,
      [nodeType]: prev[nodeType].includes(relType)
        ? prev[nodeType].filter(r => r !== relType)
        : [...prev[nodeType], relType]
    }));
  };

  // Получение доступных типов связей для конкретного типа узла
  const getRelationTypesForNodeType = (nodeType: string): RelationType[] => {
    return relationTypes.filter(rel =>
      rel.from.includes(nodeType) || rel.to.includes(nodeType)
    );
  };

  const handleBuildGraph = () => {
    const params = {
      entity: selectedEntity,
      nodeTypes: selectedNodeTypes,
      relationFilters,
      depth,
    };
    console.log('Build graph with params:', params);
    // Здесь будет запрос к бэкенду и отрисовка графа
  };

  if (loadingMeta) return <div className="loader">Loading graph builder...</div>;

  return (
    <div className="graph-page">

      <div className="graph-two-columns">
        {/* Левая колонка: выбор сущности, глубина, кнопка и поле для графа */}
        <div className="graph-left">
          <h1 className="graph-title">Graph of nearest neighbors</h1>
          <div className="graph-control-group">
            <label>Entity:</label>
            <div className="search-container" ref={searchContainerRef}>
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Start typing entity name..."
                className="search-input"
              />
              {searchResults.length > 0 && (
                <ul className="search-results-dropdown">
                  {searchResults.map(res => (
                    <li key={res.slug} onClick={() => handleSelectEntity(res)}>
                      {res.name} ({res.type})
                    </li>
                  ))}
                </ul>
              )}
              {isSearching && <div className="search-loading">Loading...</div>}
            </div>
            {selectedEntity && (
              <div className="selected-entity">
                Selected: <b>{selectedEntity.name}</b> ({selectedEntity.type})
                <button onClick={() => setSelectedEntity(null)}>✖</button>
              </div>
            )}
          </div>

          <div className="graph-control-group">
            <label>Depth:</label>
            <div className="radio-group-horizontal">
              <label>
                <input
                  type="radio"
                  name="depth"
                  checked={depth === 1}
                  onChange={() => setDepth(1)}
                />
                1
              </label>
              <label>
                <input
                  type="radio"
                  name="depth"
                  checked={depth === 2}
                  onChange={() => setDepth(2)}
                />
                2
              </label>
            </div>
          </div>

          <div className="graph-control-group">
            <button className="build-graph-btn" onClick={handleBuildGraph}>
              Build Graph
            </button>
          </div>

          <div className="graph-visualization-placeholder">
            <p>Graph will appear here after clicking "Build Graph".</p>
          </div>
        </div>

        {/* Правая колонка: фильтры */}
        <aside className="filters-sidebar">
          <h2 className="filters-main-title">Filters</h2>
          <FilterSection title="Node types">
            <div className="filter-field">
              <div className="checkbox-group-vertical">
                {nodeTypes.map(nt => (
                  <label key={nt.type}>
                    <input
                      type="checkbox"
                      checked={selectedNodeTypes.includes(nt.type)}
                      onChange={() => handleNodeTypeToggle(nt.type)}
                    />
                    {nt.label}
                  </label>
                ))}
              </div>
            </div>
          </FilterSection>

          {selectedNodeTypes.map(nodeType => (
            <FilterSection key={nodeType} title={`Relation types for ${nodeType}`}>
              <div className="filter-field">
                <div className="checkbox-group-vertical">
                  {getRelationTypesForNodeType(nodeType).map(rel => (
                    <label key={rel.type}>
                      <input
                        type="checkbox"
                        checked={relationFilters[nodeType]?.includes(rel.type) || false}
                        onChange={() => handleRelationTypeToggle(nodeType, rel.type)}
                      />
                      {rel.label}
                    </label>
                  ))}
                </div>
              </div>
            </FilterSection>
          ))}
        </aside>
      </div>
    </div>
  );
};

export default GraphPage;