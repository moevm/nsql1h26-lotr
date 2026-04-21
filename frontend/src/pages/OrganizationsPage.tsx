import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListOrganizations } from '../api/generated/organizations/organizations';
import FilterSection from '../components/FilterSection';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';

const OrganizationFilters: React.FC<{
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

  const handleFoundedDateChange = (eraVal: string, yearVal: string) => {
    const combined = eraVal && yearVal ? `${eraVal} ${yearVal}` : (eraVal || yearVal || undefined);
    onLocalFilterChange('founded_date', combined);
  };
  const handleDissolvedDateChange = (eraVal: string, yearVal: string) => {
    const combined = eraVal && yearVal ? `${eraVal} ${yearVal}` : (eraVal || yearVal || undefined);
    onLocalFilterChange('dissolved_date', combined);
  };

  const isDissolvedTrue = localFilters.is_dissolved === true;
  const isDissolvedFalse = localFilters.is_dissolved === false;
  const handleIsDissolvedChange = (value: boolean, checked: boolean) => {
    if (checked) onLocalFilterChange('is_dissolved', value);
    else onLocalFilterChange('is_dissolved', undefined);
  };

  return (
    <>
      <h2 className="filters-main-title">Filters</h2>
      <FilterSection title="Name">
        {renderTextFilter('', 'name', 'e.g., fellowship')}
      </FilterSection>
      <FilterSection title="Organization type">
        {renderTextFilter('', 'entity_type')}
      </FilterSection>
      <FilterSection title="Foundation date">
        <div className="filter-field">
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              className="filter-text-input"
              type="text"
              placeholder="Timeline (TA, SA...)"
              value={(localFilters.founded_date || '').split(' ')[0] || ''}
              onChange={(e) => {
                const yearPart = (localFilters.founded_date || '').split(' ')[1] || '';
                handleFoundedDateChange(e.target.value, yearPart);
              }}
            />
            <input
              className="filter-text-input"
              type="text"
              placeholder="Year"
              value={(localFilters.founded_date || '').split(' ')[1] || ''}
              onChange={(e) => {
                const eraPart = (localFilters.founded_date || '').split(' ')[0] || '';
                handleFoundedDateChange(eraPart, e.target.value);
              }}
            />
          </div>
        </div>
      </FilterSection>
      <FilterSection title="Dissolution date">
        <div className="filter-field">
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              className="filter-text-input"
              type="text"
              placeholder="Timeline (TA, SA...)"
              value={(localFilters.dissolved_date || '').split(' ')[0] || ''}
              onChange={(e) => {
                const yearPart = (localFilters.dissolved_date || '').split(' ')[1] || '';
                handleDissolvedDateChange(e.target.value, yearPart);
              }}
            />
            <input
              className="filter-text-input"
              type="text"
              placeholder="Year"
              value={(localFilters.dissolved_date || '').split(' ')[1] || ''}
              onChange={(e) => {
                const eraPart = (localFilters.dissolved_date || '').split(' ')[0] || '';
                handleDissolvedDateChange(eraPart, e.target.value);
              }}
            />
          </div>
        </div>
      </FilterSection>
      <FilterSection title="Clothing">
        {renderTextFilter('', 'clothing')}
      </FilterSection>
      <FilterSection title="Weaponry">
        {renderTextFilter('', 'weaponry')}
      </FilterSection>
      <FilterSection title="Purpose">
        {renderTextFilter('', 'purpose')}
      </FilterSection>
      <FilterSection title="Notable for">
        {renderTextFilter('', 'notable_for')}
      </FilterSection>
      <FilterSection title="Dissolution status">
        <div className="filter-field">
          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={isDissolvedTrue}
                onChange={(e) => handleIsDissolvedChange(true, e.target.checked)}
              /> Dissolved
            </label>
            <label>
              <input
                type="checkbox"
                checked={isDissolvedFalse}
                onChange={(e) => handleIsDissolvedChange(false, e.target.checked)}
              /> Active
            </label>
          </div>
        </div>
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

const OrganizationsPage: React.FC = () => {
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
  const { data, isLoading, error } = useListOrganizations(queryParams);

  const queryClient = useQueryClient();
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/organizations'] });
    };
  }, []);

  const adaptedData = data?.results?.map((org: any) => {
    const previewItems: string[] = [];
    if (org.entity_type?.trim()) previewItems.push(`Type: ${org.entity_type}`);
    if (org.purpose?.trim()) previewItems.push(`Purpose: ${org.purpose}`);
    if (org.notable_for?.trim()) previewItems.push(`Notable for: ${org.notable_for}`);
    const preview = previewItems.slice(0, 3);
    return {
      slug: org.slug,
      name: org.names?.[0] || 'Unknown',
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
    if (user.role === 'admin') navigate('/create/organization');
    else alert('Only administrators can create new entities.');
  };

  useEffect(() => {
    if (pendingCreation && user) {
      if (user.role === 'admin') navigate('/create/organization');
      else alert('Only administrators can create new entities.');
      setPendingCreation(false);
    }
  }, [user, pendingCreation, navigate]);

  if (isLoading) return <div className="loader">Loading...</div>;
  if (error) return <div className="error">Error loading data</div>;

  return (
    <>
      <GenericCatalogPage
        title="Organizations"
        entityType="organization"
        data={adaptedData}
        headerActions={
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            {user?.role === 'admin' && (
              <button className="add-button" onClick={handleAddClick}>
                <FaPlus /> Add new organization
              </button>
            )}
            <div className="sort-controls">
              <select value={localSortField} onChange={handleSortFieldChange}>
                <option value="name">Name</option>
                <option value="entity_type">Organization type</option>
                <option value="founded_date">Foundation date</option>
                <option value="dissolved_date">Dissolution date</option>
                <option value="purpose">Purpose</option>
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
        <OrganizationFilters
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

export default OrganizationsPage;