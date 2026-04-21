import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListEvents } from '../api/generated/events/events';
import FilterSection from '../components/FilterSection';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';

// Компонент фильтров для событий
const EventFilters: React.FC<{
  localFilters: any;
  onLocalFilterChange: (key: string, value: any) => void;
  onApply: () => void;
  onReset: () => void;
}> = ({ localFilters, onLocalFilterChange, onApply, onReset }) => {
  const renderTextFilter = (label: string, key: string, placeholder?: string) => (
    <div className="filter-field">
      <label>{label}</label>
      <input
        className="filter-text-input"
        type="text"
        value={localFilters[key] || ''}
        onChange={(e) => onLocalFilterChange(key, e.target.value || undefined)}
        placeholder={placeholder || `Enter...`}
      />
    </div>
  );

  const handleStartDateChange = (eraVal: string, yearVal: string) => {
    const combined = eraVal && yearVal ? `${eraVal} ${yearVal}` : (eraVal || yearVal || undefined);
    onLocalFilterChange('start_date', combined);
  };
  const handleEndDateChange = (eraVal: string, yearVal: string) => {
    const combined = eraVal && yearVal ? `${eraVal} ${yearVal}` : (eraVal || yearVal || undefined);
    onLocalFilterChange('end_date', combined);
  };

  return (
    <>
      <h2 className="filters-main-title">Filters</h2>
      <FilterSection title="Name">
        {renderTextFilter('', 'name', 'e.g., war')}
      </FilterSection>
      <FilterSection title="Event type">
        {renderTextFilter('', 'entity_type')}
      </FilterSection>
      <FilterSection title="Start date">
        <div className="filter-field">
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              className="filter-text-input"
              type="text"
              placeholder="Timeline (TA, SA...)"
              value={(localFilters.start_date || '').split(' ')[0] || ''}
              onChange={(e) => {
                const yearPart = (localFilters.start_date || '').split(' ')[1] || '';
                handleStartDateChange(e.target.value, yearPart);
              }}
            />
            <input
              className="filter-text-input"
              type="text"
              placeholder="Year"
              value={(localFilters.start_date || '').split(' ')[1] || ''}
              onChange={(e) => {
                const eraPart = (localFilters.start_date || '').split(' ')[0] || '';
                handleStartDateChange(eraPart, e.target.value);
              }}
            />
          </div>
        </div>
      </FilterSection>
      <FilterSection title="End date">
        <div className="filter-field">
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              className="filter-text-input"
              type="text"
              placeholder="Timeline (TA, SA...)"
              value={(localFilters.end_date || '').split(' ')[0] || ''}
              onChange={(e) => {
                const yearPart = (localFilters.end_date || '').split(' ')[1] || '';
                handleEndDateChange(e.target.value, yearPart);
              }}
            />
            <input
              className="filter-text-input"
              type="text"
              placeholder="Year"
              value={(localFilters.end_date || '').split(' ')[1] || ''}
              onChange={(e) => {
                const eraPart = (localFilters.end_date || '').split(' ')[0] || '';
                handleEndDateChange(eraPart, e.target.value);
              }}
            />
          </div>
        </div>
      </FilterSection>
      <FilterSection title="Casualties">
        {renderTextFilter('', 'casualties')}
      </FilterSection>
      <FilterSection title="Notable for">
        {renderTextFilter('', 'notable_for')}
      </FilterSection>
      <FilterSection title="Related character (slug)">
        {renderTextFilter('', 'character')}
      </FilterSection>
      <FilterSection title="Related location (slug)">
        {renderTextFilter('', 'location')}
      </FilterSection>
      <div className="filter-actions">
        <button className="apply-filters-btn" onClick={onApply}>Apply filters</button>
        <button className="reset-filters-btn" onClick={onReset}>Reset all</button>
      </div>
    </>
  );
};

const EventsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingCreation, setPendingCreation] = useState(false);

  // Фильтры: локальные и активные
  const [localFilters, setLocalFilters] = useState<Record<string, any>>({});
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>({});

  // Сортировка: локальная и активная
  const [localSortField, setLocalSortField] = useState('name');
  const [localSortOrder, setLocalSortOrder] = useState('asc');
  const [activeSortField, setActiveSortField] = useState('name');
  const [activeSortOrder, setActiveSortOrder] = useState('asc');

  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Параметры запроса
  const queryParams = {
    ...activeFilters,
    page,
    page_size: pageSize,
    sort: activeSortField,
    order: activeSortOrder,
  };
  const { data, isLoading, error } = useListEvents(queryParams);

  const queryClient = useQueryClient();
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/events'] });
    };
  }, []);

  // Адаптация данных для карточек (превью)
  const adaptedData = data?.results?.map((event: any) => {
    const previewItems: string[] = [];
    if (event.start_date?.trim()) previewItems.push(`Start: ${event.start_date}`);
    if (event.end_date?.trim()) previewItems.push(`End: ${event.end_date}`);
    if (event.notable_for?.trim()) previewItems.push(`Notable for: ${event.notable_for}`);
    const preview = previewItems.slice(0, 3);
    return {
      slug: event.slug,
      name: event.names?.[0] || 'Unknown',
      preview,
    };
  }) || [];

  const totalCount = data?.count || 0;
  const hasPrev = data?.previous !== null;
  const hasNext = data?.next !== null;
  const handlePrevPage = () => { if (hasPrev) setPage(p => p - 1); };
  const handleNextPage = () => { if (hasNext) setPage(p => p + 1); };

  const handleLocalFilterChange = (key: string, value: any) => {
    setLocalFilters(prev => ({ ...prev, [key]: value }));
  };

  // Применение фильтров и сортировки
  const applyFiltersAndSort = () => {
    setActiveFilters({ ...localFilters });
    setActiveSortField(localSortField);
    setActiveSortOrder(localSortOrder);
    setPage(1);
  };

  // Сброс всего (фильтры + сортировка)
  const resetAll = () => {
    setLocalFilters({});
    setActiveFilters({});
    setLocalSortField('name');
    setLocalSortOrder('asc');
    setActiveSortField('name');
    setActiveSortOrder('asc');
    setPage(1);
  };

  const handleSortFieldChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLocalSortField(e.target.value);
  };

  const handleSortOrderToggle = () => {
    setLocalSortOrder(prev => (prev === 'asc' ? 'desc' : 'asc'));
  };

  const handleAddClick = () => {
    if (!user) {
      setShowAuthModal(true);
      setPendingCreation(true);
      return;
    }
    if (user.role === 'admin') navigate('/create/event');
    else alert('Only administrators can create new entities.');
  };

  useEffect(() => {
    if (pendingCreation && user) {
      if (user.role === 'admin') navigate('/create/event');
      else alert('Only administrators can create new entities.');
      setPendingCreation(false);
    }
  }, [user, pendingCreation, navigate]);

  if (isLoading) return <div className="loader">Loading...</div>;
  if (error) return <div className="error">Error loading data</div>;

  return (
    <>
      <GenericCatalogPage
        title="Events"
        entityType="event"
        data={adaptedData}
        headerActions={
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            {user?.role === 'admin' && (
              <button className="add-button" onClick={handleAddClick}>
                <FaPlus /> Add new event
              </button>
            )}
            <div className="sort-controls">
              <select value={localSortField} onChange={handleSortFieldChange}>
                <option value="name">Name</option>
                <option value="entity_type">Event type</option>
                <option value="start_date">Start date</option>
                <option value="end_date">End date</option>
                <option value="casualties">Casualties</option>
                <option value="notable_for">Notable for</option>
              </select>
              <button className="sort-order-btn" onClick={handleSortOrderToggle}>
                {localSortOrder === 'asc' ? '↑' : '↓'}
              </button>
              <button className="apply-sort-btn" onClick={applyFiltersAndSort}>
                Apply
              </button>
            </div>
          </div>
        }
      >
        <EventFilters
          localFilters={localFilters}
          onLocalFilterChange={handleLocalFilterChange}
          onApply={applyFiltersAndSort}
          onReset={resetAll}
        />
      </GenericCatalogPage>
      <div className="pagination-container">
        <button className="pagination-btn" onClick={handlePrevPage} disabled={!hasPrev}>← Previous</button>
        <span className="pagination-info">Page {page} (total: {Math.ceil(totalCount / pageSize)})</span>
        <button className="pagination-btn" onClick={handleNextPage} disabled={!hasNext}>Next →</button>
      </div>
      {showAuthModal && (
        <AuthModal
          onClose={() => { setShowAuthModal(false); setPendingCreation(false); }}
          onSuccess={() => setShowAuthModal(false)}
        />
      )}
    </>
  );
};

export default EventsPage;