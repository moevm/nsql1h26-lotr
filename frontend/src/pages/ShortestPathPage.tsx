import { useState, useEffect, useRef } from 'react';
import { useDebounce } from '../hooks/useDebounce';
import FilterSection from '../components/FilterSection';
import { axiosInstance } from '../api/axios-instance';
import { Link } from 'react-router-dom';
import { useSearchParams } from 'react-router-dom';

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

const ShortestPathPage: React.FC = () => {
  const [nodeTypes, setNodeTypes] = useState<NodeType[]>([]);
  const [relationTypes, setRelationTypes] = useState<RelationType[]>([]);
  const [loadingMeta, setLoadingMeta] = useState(true);
  const [searchParams] = useSearchParams();
  const fromSlug = searchParams.get('from');

  // Поиск сущностей
  const fromSearchContainerRef = useRef<HTMLDivElement>(null);
  const toSearchContainerRef = useRef<HTMLDivElement>(null);
  const [fromQuery, setFromQuery] = useState('');
  const [fromResults, setFromResults] = useState<any[]>([]);
  const [fromEntity, setFromEntity] = useState<any>(null);
  const [toQuery, setToQuery] = useState('');
  const [toResults, setToResults] = useState<any[]>([]);
  const [toEntity, setToEntity] = useState<any>(null);
  const [isSearching, setIsSearching] = useState(false);

  // Фильтры
  const [selectedNodeTypes, setSelectedNodeTypes] = useState<string[]>([]);
  const [relationFilters, setRelationFilters] = useState<Record<string, string[]>>({});
  const [maxDepth, setMaxDepth] = useState(10);

  const [result, setResult] = useState<any>(null);
  const [loadingPath, setLoadingPath] = useState(false);
  const [error, setError] = useState('');

  const debouncedFrom = useDebounce(fromQuery, 300);
  const debouncedTo = useDebounce(toQuery, 300);

  // Загрузка метаданных
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

  useEffect(() => {
    if (fromSlug) {
      fetch(`/api/v1/pages/${fromSlug}`)
        .then(r => r.json())
        .then(data => {
          setFromEntity({ slug: data.slug, name: data.names?.[0], type: data.type });
        });
    }
  }, [fromSlug]);

  // Поиск сущностей (общая функция)
  const searchEntities = async (query: string, setResults: (data: any[]) => void) => {
    if (!query || query.length < 2) {
      setResults([]);
      return;
    }
    setIsSearching(true);
    try {
      const response = await fetch(`/api/v1/search/?q=${encodeURIComponent(query)}&limit=10`);
      const data = await response.json();
      setResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  useEffect(() => { searchEntities(debouncedFrom, setFromResults); }, [debouncedFrom]);
  useEffect(() => { searchEntities(debouncedTo, setToResults); }, [debouncedTo]);

  // Закрытие выпадающих списков
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (fromSearchContainerRef.current && !fromSearchContainerRef.current.contains(event.target as Node)) {
        setFromResults([]);
      }
      if (toSearchContainerRef.current && !toSearchContainerRef.current.contains(event.target as Node)) {
        setToResults([]);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleNodeTypeToggle = (type: string) => {
    setSelectedNodeTypes(prev => {
      const newSet = prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type];
      if (!newSet.includes(type)) {
        setRelationFilters(prevFilters => {
          const newFilters = { ...prevFilters };
          delete newFilters[type];
          return newFilters;
        });
      } else {
        setRelationFilters(prev => ({ ...prev, [type]: [] }));
      }
      return newSet;
    });
  };

  const handleRelationTypeToggle = (nodeType: string, relType: string) => {
    setRelationFilters(prev => ({
      ...prev,
      [nodeType]: prev[nodeType]?.includes(relType)
        ? prev[nodeType].filter(r => r !== relType)
        : [...(prev[nodeType] || []), relType]
    }));
  };

  const getRelationTypesForNodeType = (nodeType: string): RelationType[] => {
    return relationTypes.filter(rel =>
      rel.from.includes(nodeType) || rel.to.includes(nodeType)
    );
  };

  const handleFindPath = async () => {
    if (!fromEntity || !toEntity) {
      setError('Please select both "From" and "To" entities.');
      return;
    }
    setLoadingPath(true);
    setError('');
    setResult(null);
    try {
      const params = new URLSearchParams();
      params.append('from', fromEntity.slug);
      params.append('to', toEntity.slug);
      if (selectedNodeTypes.length > 0) {
        params.append('through_nodes', selectedNodeTypes.join(','));
      }
      const allSelectedRels = Object.values(relationFilters).flat();
      if (allSelectedRels.length > 0) {
        params.append('through_rels', allSelectedRels.join(','));
      }
      params.append('max_depth', maxDepth.toString());
      const response = await axiosInstance.get('/analytics/shortest-path/', { params });
      setResult(response.data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.error?.message || 'Failed to find path');
    } finally {
      setLoadingPath(false);
    }
  };

  if (loadingMeta) return <div className="loader">Loading...</div>;

  return (
    <div className="graph-page">
      <div className="graph-two-columns">
        <div className="graph-left">
          <h1 className="graph-title">Shortest Path</h1>

          <div className="graph-control-group">
            <label>From entity:</label>
            <div className="search-container" ref={fromSearchContainerRef}>
              <input
                type="text"
                value={fromQuery}
                onChange={e => setFromQuery(e.target.value)}
                placeholder="Start typing..."
                className="search-input"
              />
              {fromResults.length > 0 && (
                <ul className="search-results-dropdown">
                  {fromResults.map(res => (
                    <li key={res.slug} onClick={() => { setFromEntity(res); setFromQuery(''); setFromResults([]); }}>
                      {res.name} ({res.type})
                    </li>
                  ))}
                </ul>
              )}
            </div>
            {fromEntity && (
              <div className="selected-entity">
                Selected: <strong>{fromEntity.name}</strong> ({fromEntity.type})
                <button onClick={() => setFromEntity(null)}>✖</button>
              </div>
            )}
          </div>

          <div className="graph-control-group">
            <label>To entity:</label>
            <div className="search-container" ref={toSearchContainerRef}>
              <input
                type="text"
                value={toQuery}
                onChange={e => setToQuery(e.target.value)}
                placeholder="Start typing..."
                className="search-input"
              />
              {toResults.length > 0 && (
                <ul className="search-results-dropdown">
                  {toResults.map(res => (
                    <li key={res.slug} onClick={() => { setToEntity(res); setToQuery(''); setToResults([]); }}>
                      {res.name} ({res.type})
                    </li>
                  ))}
                </ul>
              )}
            </div>
            {toEntity && (
              <div className="selected-entity">
                Selected: <strong>{toEntity.name}</strong> ({toEntity.type})
                <button onClick={() => setToEntity(null)}>✖</button>
              </div>
            )}
          </div>

          <div className="graph-control-group">
            <label>Max depth:</label>
            <input
              type="number"
              value={maxDepth}
              onChange={e => setMaxDepth(parseInt(e.target.value) || 10)}
              min={1}
              max={50}
              className="max-depth-input"
            />
          </div>

          <div className="graph-control-group">
            <button
              className="build-graph-btn"
              onClick={handleFindPath}
              disabled={!fromEntity || !toEntity}
            >
              Find Path
            </button>
          </div>

          <div className="path-result-container">
            {loadingPath && <div className="loader">Finding path...</div>}
            {error && <div className="error-message">{error}</div>}
            {result && (
              <div className="path-result">
                {result.found ? (
                  <>
                    <p><strong>Path length:</strong> {result.length}</p>
                    <ol className="path-steps">
                      {result.path.slice(0, -1).map((step: any, idx: number) => {
                        const node = step.node;
                        const edge = step.edge_to_next;
                        const nextNode = result.path[idx + 1]?.node;
                        if (!edge || !nextNode) return null;
                        return (
                          <li key={idx}>
                            <Link to={`/pages/${node.slug}`} className="path-link">{node.name}</Link>
                            {' –('}{edge.type}{')→ '}
                            <Link to={`/pages/${nextNode.slug}`} className="path-link">{nextNode.name}</Link>
                          </li>
                        );
                      })}
                    </ol>
                  </>
                ) : (
                  <p>No path found between selected entities.</p>
                )}
              </div>
            )}
          </div>
        </div>

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

export default ShortestPathPage;