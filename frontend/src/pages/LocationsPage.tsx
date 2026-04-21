import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListLocations } from '../api/generated/locations/locations';
import FilterSection from '../components/FilterSection';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';

const LocationFilters: React.FC<{
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

  const isDestroyedTrue = localFilters.is_destroyed === true;
  const isDestroyedFalse = localFilters.is_destroyed === false;
  const handleIsDestroyedChange = (value: boolean, checked: boolean) => {
    if (checked) onLocalFilterChange('is_destroyed', value);
    else onLocalFilterChange('is_destroyed', undefined);
  };

  const handleCreationDateChange = (eraVal: string, yearVal: string) => {
    const combined = eraVal && yearVal ? `${eraVal} ${yearVal}` : (eraVal || yearVal || undefined);
    onLocalFilterChange('creation_date', combined);
  };
  const handleDestructionDateChange = (eraVal: string, yearVal: string) => {
    const combined = eraVal && yearVal ? `${eraVal} ${yearVal}` : (eraVal || yearVal || undefined);
    onLocalFilterChange('destruction_date', combined);
  };

  return (
    <>
      <h2 className="filters-main-title">Filters</h2>
      <FilterSection title="Name">
        {renderTextFilter('', 'name', 'e.g., gondor')}
      </FilterSection>
      <FilterSection title="Location type">
        {renderTextFilter('', 'entity_type')}
      </FilterSection>
      <FilterSection title="Population">
        {renderTextFilter('', 'population')}
      </FilterSection>
      <FilterSection title="Creation date">
        <div className="filter-field">
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              className="filter-text-input"
              type="text"
              placeholder="Timeline (TA, SA...)"
              value={(localFilters.creation_date || '').split(' ')[0] || ''}
              onChange={(e) => {
                const yearPart = (localFilters.creation_date || '').split(' ')[1] || '';
                handleCreationDateChange(e.target.value, yearPart);
              }}
            />
            <input
              className="filter-text-input"
              type="text"
              placeholder="Year"
              value={(localFilters.creation_date || '').split(' ')[1] || ''}
              onChange={(e) => {
                const eraPart = (localFilters.creation_date || '').split(' ')[0] || '';
                handleCreationDateChange(eraPart, e.target.value);
              }}
            />
          </div>
        </div>
      </FilterSection>
      <FilterSection title="Destruction date">
        <div className="filter-field">
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              className="filter-text-input"
              type="text"
              placeholder="Timeline (TA, SA...)"
              value={(localFilters.destruction_date || '').split(' ')[0] || ''}
              onChange={(e) => {
                const yearPart = (localFilters.destruction_date || '').split(' ')[1] || '';
                handleDestructionDateChange(e.target.value, yearPart);
              }}
            />
            <input
              className="filter-text-input"
              type="text"
              placeholder="Year"
              value={(localFilters.destruction_date || '').split(' ')[1] || ''}
              onChange={(e) => {
                const eraPart = (localFilters.destruction_date || '').split(' ')[0] || '';
                handleDestructionDateChange(eraPart, e.target.value);
              }}
            />
          </div>
        </div>
      </FilterSection>
      <FilterSection title="Notable for">
        {renderTextFilter('', 'notable_for')}
      </FilterSection>
      <FilterSection title="Destruction status">
        <div className="filter-field">
          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={isDestroyedTrue}
                onChange={(e) => handleIsDestroyedChange(true, e.target.checked)}
              /> Destroyed
            </label>
            <label>
              <input
                type="checkbox"
                checked={isDestroyedFalse}
                onChange={(e) => handleIsDestroyedChange(false, e.target.checked)}
              /> Not destroyed
            </label>
          </div>
        </div>
      </FilterSection>
      <FilterSection title="Related character (slug)">
        {renderTextFilter('', 'character')}
      </FilterSection>
      <FilterSection title="Related event (slug)">
        {renderTextFilter('', 'event')}
      </FilterSection>
      <FilterSection title="Related organization (slug)">
        {renderTextFilter('', 'organization')}
      </FilterSection>
      <div className="filter-actions">
        <button className="apply-filters-btn" onClick={onApply}>Apply filters</button>
        <button className="reset-filters-btn" onClick={onReset}>Reset all</button>
      </div>
    </>
  );
};

const LocationsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingCreation, setPendingCreation] = useState(false);

  // Фильтры
  const [localFilters, setLocalFilters] = useState<Record<string, any>>({});
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>({});

  // Сортировка
  const [localSortField, setLocalSortField] = useState('name');
  const [localSortOrder, setLocalSortOrder] = useState('asc');
  const [activeSortField, setActiveSortField] = useState('name');
  const [activeSortOrder, setActiveSortOrder] = useState('asc');

  const [page, setPage] = useState(1);
  const pageSize = 20;

  const queryParams = {
    ...activeFilters,
    page,
    page_size: pageSize,
    sort: activeSortField,
    order: activeSortOrder,
  };
  const { data, isLoading, error } = useListLocations(queryParams);

  const queryClient = useQueryClient();
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/locations'] });
    };
  }, []);

  const adaptedData = data?.results?.map((location: any) => {
    const previewItems: string[] = [];
    if (location.population?.trim()) previewItems.push(`Population: ${location.population}`);
    if (location.creation_date?.trim()) previewItems.push(`Creation date: ${location.creation_date}`);
    if (location.notable_for?.trim()) previewItems.push(`Notable for: ${location.notable_for}`);
    const preview = previewItems.slice(0, 3);
    return {
      slug: location.slug,
      name: location.names?.[0] || 'Unknown',
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

  const applyFiltersAndSort = () => {
    setActiveFilters({ ...localFilters });
    setActiveSortField(localSortField);
    setActiveSortOrder(localSortOrder);
    setPage(1);
  };

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
    if (user.role === 'admin') navigate('/create/location');
    else alert('Only administrators can create new entities.');
  };

  useEffect(() => {
    if (pendingCreation && user) {
      if (user.role === 'admin') navigate('/create/location');
      else alert('Only administrators can create new entities.');
      setPendingCreation(false);
    }
  }, [user, pendingCreation, navigate]);

  if (isLoading) return <div className="loader">Loading...</div>;
  if (error) return <div className="error">Error loading data</div>;

  return (
    <>
      <GenericCatalogPage
        title="Locations"
        entityType="location"
        data={adaptedData}
        headerActions={
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            {user?.role === 'admin' && (
              <button className="add-button" onClick={handleAddClick}>
                <FaPlus /> Add new location
              </button>
            )}
            <div className="sort-controls">
              <select value={localSortField} onChange={handleSortFieldChange}>
                <option value="name">Name</option>
                <option value="entity_type">Location type</option>
                <option value="population">Population</option>
                <option value="creation_date">Creation date</option>
                <option value="destruction_date">Destruction date</option>
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
        <LocationFilters
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

export default LocationsPage;