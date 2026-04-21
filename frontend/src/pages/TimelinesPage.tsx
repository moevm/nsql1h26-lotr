import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListTimelines } from '../api/generated/timelines/timelines';
import FilterSection from '../components/FilterSection';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';

const TimelineFilters: React.FC<{
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
        {renderTextFilter('', 'name', 'e.g., third age')}
      </FilterSection>
      <FilterSection title="Abbreviation">
        {renderTextFilter('', 'abbreviation')}
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
      <div className="filter-actions">
        <button className="apply-filters-btn" onClick={onApply}>Apply filters</button>
        <button className="reset-filters-btn" onClick={onReset}>Reset all</button>
      </div>
    </>
  );
};

const TimelinesPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingCreation, setPendingCreation] = useState(false);

  const [localFilters, setLocalFilters] = useState<Record<string, any>>({});
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>({});

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
  const { data, isLoading, error } = useListTimelines(queryParams);

  const queryClient = useQueryClient();
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/timelines'] });
    };
  }, []);

  const adaptedData = data?.results?.map((timeline: any) => {
    const previewItems: string[] = [];
    if (timeline.abbreviation?.trim()) previewItems.push(`Abbreviation: ${timeline.abbreviation}`);
    if (timeline.start_date?.trim()) previewItems.push(`Start: ${timeline.start_date}`);
    if (timeline.end_date?.trim()) previewItems.push(`End: ${timeline.end_date}`);
    const preview = previewItems.slice(0, 3);
    return {
      slug: timeline.slug,
      name: timeline.names?.[0] || 'Unknown',
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
    if (user.role === 'admin') navigate('/create/timeline');
    else alert('Only administrators can create new entities.');
  };

  useEffect(() => {
    if (pendingCreation && user) {
      if (user.role === 'admin') navigate('/create/timeline');
      else alert('Only administrators can create new entities.');
      setPendingCreation(false);
    }
  }, [user, pendingCreation, navigate]);

  if (isLoading) return <div className="loader">Loading...</div>;
  if (error) return <div className="error">Error loading data</div>;

  return (
    <>
      <GenericCatalogPage
        title="Timelines"
        entityType="timeline"
        data={adaptedData}
        headerActions={
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            {user?.role === 'admin' && (
              <button className="add-button" onClick={handleAddClick}>
                <FaPlus /> Add new timeline
              </button>
            )}
            <div className="sort-controls">
              <select value={localSortField} onChange={handleSortFieldChange}>
                <option value="name">Name</option>
                <option value="abbreviation">Abbreviation</option>
                <option value="start_date">Start date</option>
                <option value="end_date">End date</option>
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
        <TimelineFilters
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

export default TimelinesPage;