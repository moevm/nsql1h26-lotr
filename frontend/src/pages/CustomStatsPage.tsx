// src/pages/CustomStatsPage.tsx
import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { axiosInstance } from '../api/axios-instance';
import FilterSection from '../components/FilterSection';

const entityTypes = [
  { value: 'character', label: 'Character' },
  { value: 'location', label: 'Location' },
  { value: 'event', label: 'Event' },
  { value: 'organization', label: 'Organization' },
  { value: 'item', label: 'Item' },
];

const attributesByEntity: Record<string, string[]> = {
  character: ['gender', 'race', 'is_alive', 'organization', 'timeline'],
  location: ['entity_type', 'is_destroyed'],
  event: ['entity_type', 'timeline'],
  organization: ['entity_type', 'is_dissolved'],
  item: ['entity_type', 'material'],
};

// Фильтры для каждого типа сущности
const filtersByEntity: Record<string, Array<{ key: string; label: string; type: 'text' | 'checkbox' | 'range'; options?: string[] }>> = {
  character: [
    { key: 'name', label: 'Name', type: 'text' },
    { key: 'titles', label: 'Titles', type: 'text' },
    { key: 'gender', label: 'Gender', type: 'checkbox', options: ['male', 'female', 'unknown'] },
    { key: 'is_alive', label: 'Is alive', type: 'checkbox', options: ['true', 'false'] },
    { key: 'birth_date', label: 'Birth date', type: 'range' },
    { key: 'death_date', label: 'Death date', type: 'range' },
    { key: 'hair', label: 'Hair', type: 'text' },
    { key: 'eyes', label: 'Eyes', type: 'text' },
    { key: 'height', label: 'Height', type: 'text' },
    { key: 'weapon', label: 'Weapon', type: 'text' },
    { key: 'clothing', label: 'Clothing', type: 'text' },
    { key: 'notable_for', label: 'Notable for', type: 'text' },
    { key: 'race', label: 'Race (slug)', type: 'text' },
    { key: 'organization', label: 'Organization (slug)', type: 'text' },
    { key: 'event', label: 'Event (slug)', type: 'text' },
    { key: 'item', label: 'Item (slug)', type: 'text' },
    { key: 'location', label: 'Location (slug)', type: 'text' },
  ],
  location: [
    { key: 'name', label: 'Name', type: 'text' },
    { key: 'entity_type', label: 'Location type', type: 'text' },
    { key: 'population', label: 'Population', type: 'text' },
    { key: 'creation_date', label: 'Creation date', type: 'range' },
    { key: 'destruction_date', label: 'Destruction date', type: 'range' },
    { key: 'notable_for', label: 'Notable for', type: 'text' },
    { key: 'is_destroyed', label: 'Is destroyed', type: 'checkbox', options: ['true', 'false'] },
    { key: 'character', label: 'Character (slug)', type: 'text' },
    { key: 'event', label: 'Event (slug)', type: 'text' },
    { key: 'organization', label: 'Organization (slug)', type: 'text' },
  ],
  event: [
    { key: 'name', label: 'Name', type: 'text' },
    { key: 'entity_type', label: 'Event type', type: 'text' },
    { key: 'start_date', label: 'Start date', type: 'range' },
    { key: 'end_date', label: 'End date', type: 'range' },
    { key: 'casualties', label: 'Casualties', type: 'text' },
    { key: 'notable_for', label: 'Notable for', type: 'text' },
    { key: 'character', label: 'Character (slug)', type: 'text' },
    { key: 'location', label: 'Location (slug)', type: 'text' },
    { key: 'organization', label: 'Organization (slug)', type: 'text' },
  ],
  organization: [
    { key: 'name', label: 'Name', type: 'text' },
    { key: 'entity_type', label: 'Organization type', type: 'text' },
    { key: 'founded_date', label: 'Founded date', type: 'range' },
    { key: 'dissolved_date', label: 'Dissolved date', type: 'range' },
    { key: 'clothing', label: 'Clothing', type: 'text' },
    { key: 'weaponry', label: 'Weaponry', type: 'text' },
    { key: 'purpose', label: 'Purpose', type: 'text' },
    { key: 'notable_for', label: 'Notable for', type: 'text' },
    { key: 'is_dissolved', label: 'Is dissolved', type: 'checkbox', options: ['true', 'false'] },
    { key: 'character', label: 'Character (slug)', type: 'text' },
    { key: 'location', label: 'Location (slug)', type: 'text' },
  ],
  item: [
    { key: 'name', label: 'Name', type: 'text' },
    { key: 'entity_type', label: 'Item type', type: 'text' },
    { key: 'material', label: 'Material', type: 'text' },
    { key: 'notable_for', label: 'Notable for', type: 'text' },
    { key: 'character', label: 'Character (slug)', type: 'text' },
  ],
};

// Определяем, является ли атрибут «связующим» (внешним ключом к другому типу сущности)
const isRelationshipAttr = (entityType: string, attr: string): boolean => {
  switch (entityType) {
    case 'character':
      return ['race', 'organization', 'timeline'].includes(attr);
    case 'location':
      return ['character', 'event', 'organization'].includes(attr);
    case 'event':
      return ['character', 'location', 'organization'].includes(attr);
    case 'organization':
      return ['character', 'location'].includes(attr);
    case 'item':
      return ['character'].includes(attr);
    default:
      return false;
  }
};

// Получение доступных атрибутов для группировки с учётом текущего attr
const getAvailableGroupByOptions = (entityType: string, attr: string, allAttrs: string[]): string[] => {
  let filtered = allAttrs.filter(a => a !== attr);
  // Если текущий attr является связующим, исключаем все остальные связующие атрибуты
  if (isRelationshipAttr(entityType, attr)) {
    filtered = filtered.filter(a => !isRelationshipAttr(entityType, a));
  }
  return filtered;
};

const renderFilter = (
  filter: any,
  localFilters: any,
  onLocalFilterChange: (key: string, value: any) => void
) => {
  switch (filter.type) {
    case 'text':
      return (
        <div className="filter-field">
          <input
            className="filter-text-input"
            type="text"
            value={localFilters[filter.key] || ''}
            onChange={(e) => onLocalFilterChange(filter.key, e.target.value || undefined)}
            placeholder="Enter..."
          />
        </div>
      );
    case 'checkbox':
      const selected = localFilters[filter.key] ? localFilters[filter.key].split(',') : [];
      return (
        <div className="filter-field">
          <div className="checkbox-group">
            {filter.options.map((opt: string) => (
              <label key={opt}>
                <input
                  type="checkbox"
                  value={opt}
                  checked={selected.includes(opt)}
                  onChange={(e) => {
                    let newSelected = [...selected];
                    if (e.target.checked) {
                      if (!newSelected.includes(opt)) newSelected.push(opt);
                    } else {
                      newSelected = newSelected.filter((v) => v !== opt);
                    }
                    const newValue = newSelected.length ? newSelected.join(',') : undefined;
                    onLocalFilterChange(filter.key, newValue);
                  }}
                />
                {opt}
              </label>
            ))}
          </div>
        </div>
      );
    case 'range':
      const fromKey = `${filter.key}_from`;
      const toKey = `${filter.key}_to`;
      return (
        <div className="filter-field">
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              className="filter-text-input"
              type="text"
              placeholder="From"
              value={localFilters[fromKey] || ''}
              onChange={(e) => onLocalFilterChange(fromKey, e.target.value || undefined)}
            />
            <input
              className="filter-text-input"
              type="text"
              placeholder="To"
              value={localFilters[toKey] || ''}
              onChange={(e) => onLocalFilterChange(toKey, e.target.value || undefined)}
            />
          </div>
        </div>
      );
    default:
      return null;
  }
};

const CustomStatsPage: React.FC = () => {
  const [entityType, setEntityType] = useState('character');
  const [attr, setAttr] = useState('');
  const [groupBy, setGroupBy] = useState('');
  const [localFilters, setLocalFilters] = useState<Record<string, any>>({});
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>({});
  const [fetchParams, setFetchParams] = useState<{
    entity_type: string;
    attr: string;
    group_by?: string;
    filters?: any;
  } | null>(null);

  const availableAttrs = attributesByEntity[entityType] || [];
  const availableFilters = filtersByEntity[entityType] || [];

  // Сброс при смене типа сущности
  useEffect(() => {
    setAttr('');
    setGroupBy('');
    setLocalFilters({});
    setActiveFilters({});
  }, [entityType]);

  // Автоматический сброс группировки, если выбранный атрибут становится недоступным
  useEffect(() => {
    if (!attr) return;
    const availableGroupBy = getAvailableGroupByOptions(entityType, attr, availableAttrs);
    if (groupBy && !availableGroupBy.includes(groupBy)) {
      setGroupBy('');
    }
  }, [attr, entityType, availableAttrs, groupBy]);

  const groupByOptions = getAvailableGroupByOptions(entityType, attr, availableAttrs);

  const handleApplyFilters = () => {
    setActiveFilters({ ...localFilters });
  };

  const handleResetFilters = () => {
    setLocalFilters({});
    setActiveFilters({});
  };

  const handleBuildChart = () => {
    if (!attr) return;
    setFetchParams({
      entity_type: entityType,
      attr,
      group_by: groupBy || undefined,
      filters: activeFilters,
    });
  };

  const { data, isLoading, error } = useQuery({
    queryKey: ['custom-stats', fetchParams],
    queryFn: async () => {
      if (!fetchParams) return null;
      const params: any = {
        entity_type: fetchParams.entity_type,
        attr: fetchParams.attr,
        top_n: 20,
      };
      if (fetchParams.group_by) params.group_by = fetchParams.group_by;
      Object.entries(fetchParams.filters || {}).forEach(([key, value]) => {
        if (value !== undefined && value !== '') params[key] = value;
      });
      const response = await axiosInstance.get('/analytics/custom/', { params });
      return response.data;
    },
    enabled: !!fetchParams,
  });

  const chartData = data?.data || [];
  const groups = data?.groups || [];
  const hasGrouping = groups.length > 0;
  const COLORS = ['#85603b', '#926d43', '#b08b5f', '#cfaa7a', '#eec995', '#fbdcb1', '#8b5a2b'];

  return (
    <div className="custom-stats-page">
      {/* Левая часть – основные параметры и график */}
      <div className="characters-list-container">
        <h1 className="custom-stats-title">Custom Statistics</h1>
        <div className="stats-controls">
          <div className="filter-stats-field">
            <label>Entity type</label>
            <select value={entityType} onChange={(e) => setEntityType(e.target.value)}>
              {entityTypes.map((et) => (
                <option key={et.value} value={et.value}>
                  {et.label}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-stats-field">
            <label>X-axis attribute</label>
            <select value={attr} onChange={(e) => setAttr(e.target.value)}>
              <option value="">Select...</option>
              {availableAttrs.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-stats-field">
            <label>Group by (optional)</label>
            <select value={groupBy} onChange={(e) => setGroupBy(e.target.value)}>
              <option value="">None</option>
              {groupByOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-stats-actions">
            <button className="build-chart-btn" onClick={handleBuildChart} disabled={!attr}>
              Build Chart
            </button>
          </div>
        </div>
        <div className="chart-stats-container">
          {isLoading && <div className="loader">Loading chart...</div>}
          {error && <div className="error">Failed to load data.</div>}
          {!isLoading && !error && chartData.length > 0 && (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#555" />
                <XAxis dataKey="x" angle={-45} textAnchor="end" height={80} tick={{ fill: '#f5e7d9' }} />
                <YAxis tick={{ fill: '#f5e7d9' }} />
                <Tooltip contentStyle={{ backgroundColor: '#2c2a28', border: 'none' }} />
                <Legend wrapperStyle={{ color: '#f5e7d9' }} />
                {hasGrouping ? (
                  groups.map((group, idx) => (
                    <Bar key={group} dataKey={group} stackId="stack" fill={COLORS[idx % COLORS.length]} />
                  ))
                ) : (
                  <Bar dataKey="value" fill="#8b5a2b" />
                )}
              </BarChart>
            </ResponsiveContainer>
          )}
          {!isLoading && !error && chartData.length === 0 && fetchParams && <p>No data for selected parameters.</p>}
        </div>
      </div>

      {/* Правая часть – фильтры */}
      <aside className="filters-sidebar">
        <h2 className="filters-main-title">Filters</h2>
        {availableFilters.map((filter) => (
          <FilterSection key={filter.key} title={filter.label}>
            {renderFilter(filter, localFilters, (key, value) =>
              setLocalFilters((prev) => ({ ...prev, [key]: value }))
            )}
          </FilterSection>
        ))}
        <div className="filter-actions">
          <button className="apply-filters-btn" onClick={handleApplyFilters}>
            Apply filters
          </button>
          <button className="reset-filters-btn" onClick={handleResetFilters}>
            Reset all
          </button>
        </div>
      </aside>
    </div>
  );
};

export default CustomStatsPage;