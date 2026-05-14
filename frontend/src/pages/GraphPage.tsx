import { useState, useEffect, useRef } from 'react';
import { useDebounce } from '../hooks/useDebounce';
import FilterSection from '../components/FilterSection';
import VisNetwork from '../components/VisNetwork';

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

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<any>(null);
  const [isSearching, setIsSearching] = useState(false);
  const debouncedQuery = useDebounce(searchQuery, 300);

  const [selectedNodeTypes, setSelectedNodeTypes] = useState<string[]>([]);
  const [relationFilters, setRelationFilters] = useState<Record<string, string[]>>({});
  const [depth, setDepth] = useState<1 | 2>(1);

  const [graphData, setGraphData] = useState<{ nodes: any[]; edges: any[] }>({ nodes: [], edges: [] });
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [graphError, setGraphError] = useState('');

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

  // Закрытие выпадающего списка при клике вне
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
    setGraphData({ nodes: [], edges: [] });
    setGraphError('');
  };

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
      [nodeType]: prev[nodeType].includes(relType)
        ? prev[nodeType].filter(r => r !== relType)
        : [...prev[nodeType], relType]
    }));
  };

  const getRelationTypesForNodeType = (nodeType: string): RelationType[] => {
    return relationTypes.filter(rel =>
      rel.from.includes(nodeType) || rel.to.includes(nodeType)
    );
  };

  const handleBuildGraph = async () => {
    if (!selectedEntity) {
      setGraphError('Please select an entity first.');
      return;
    }
    setLoadingGraph(true);
    setGraphError('');
    try {
      const params = new URLSearchParams();
      params.append('slug', selectedEntity.slug);
      params.append('depth', depth.toString());
      if (selectedNodeTypes.length > 0) params.append('through_nodes', selectedNodeTypes.join(','));
      const allSelectedRels = Object.values(relationFilters).flat();
      if (allSelectedRels.length > 0) params.append('through_rels', allSelectedRels.join(','));
      const response = await fetch(`/api/v1/analytics/neighbors/?${params.toString()}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      const nodes: any[] = [];
      const nodeMap = new Map();
      if (data.root_node) {
        nodes.push({ id: data.root_node.slug, label: data.root_node.name, type: data.root_node.type });
        nodeMap.set(data.root_node.slug, true);
      }
      (data.nodes || []).forEach((node: any) => {
        if (!nodeMap.has(node.slug)) {
          nodes.push({ id: node.slug, label: node.name, type: node.type });
          nodeMap.set(node.slug, true);
        }
      });

      const edges = (data.edges || []).map((edge: any) => ({
        from: edge.from,
        to: edge.to,
        label: edge.type,
      }));

      setGraphData({ nodes, edges });
    } catch (err: any) {
      setGraphError(err.message || 'Failed to build graph');
    } finally {
      setLoadingGraph(false);
    }
  };

  const options = {
    nodes: {
      shape: 'dot',
      size: 20,
      font: { size: 12, color: '#ffffff', face: 'Arial' },
      color: { background: '#8b5a2b', border: '#5a4a3a', highlight: { background: '#c7b198', border: '#8b5a2b' } },
    },
    edges: {
      arrows: { to: { enabled: true, scaleFactor: 0.5 } },
      color: { color: '#c7b198', highlight: '#f5e7d9' },
      font: { size: 8, color: '#ffffff', face: 'Arial', strokeWidth: 0, align: 'middle' },
      smooth: { type: 'cubicBezier', roundness: 0.2 },
    },
    physics: {
      enabled: true,
      stabilization: { iterations: 150 },
    },
    interaction: {
      zoomView: true,
      dragView: true,
      hover: true,
    },
    layout: {
      improvedLayout: true,
      hierarchical: false,
    },
  };

  if (loadingMeta) return <div className="loader">Loading graph builder...</div>;

  return (
    <div className="graph-page">
      <div className="graph-two-columns">
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
              <label><input type="radio" name="depth" checked={depth === 1} onChange={() => setDepth(1)} /> 1</label>
              <label><input type="radio" name="depth" checked={depth === 2} onChange={() => setDepth(2)} /> 2</label>
            </div>
          </div>

          <div className="graph-control-group">
            <button className="build-graph-btn" onClick={handleBuildGraph}>Build Graph</button>
          </div>

          <div className="graph-visualization-container">
            {loadingGraph && <div className="loader">Building graph...</div>}
            {graphError && <div className="error-message">{graphError}</div>}
            {!loadingGraph && graphData.nodes.length > 0 && (
              <VisNetwork nodes={graphData.nodes} edges={graphData.edges} options={options} />
            )}
            {!loadingGraph && !graphError && graphData.nodes.length === 0 && selectedEntity && (
              <p>No graph data. Try different filters.</p>
            )}
            {!selectedEntity && <p>Select an entity and click "Build Graph".</p>}
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

export default GraphPage;