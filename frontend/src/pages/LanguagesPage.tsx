import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListLanguages } from '../api/generated/languages/languages';
import FilterSection from '../components/FilterSection';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';

const LanguageFilters: React.FC<{
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

  return (
    <>
      <h2 className="filters-main-title">Filters</h2>
      <FilterSection title="Name">
        {renderTextFilter('', 'name', 'e.g., quenya')}
      </FilterSection>
      <FilterSection title="Family">
        {renderTextFilter('', 'family')}
      </FilterSection>
      <div className="filter-actions">
        <button className="apply-filters-btn" onClick={onApply}>Apply filters</button>
        <button className="reset-filters-btn" onClick={onReset}>Reset all</button>
      </div>
    </>
  );
};

const LanguagesPage: React.FC = () => {
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
  const { data, isLoading, error } = useListLanguages(queryParams);

  const queryClient = useQueryClient();
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/languages'] });
    };
  }, []);

  const adaptedData = data?.results?.map((lang: any) => {
    const previewItems: string[] = [];
    if (lang.family?.trim()) previewItems.push(`Family: ${lang.family}`);
    const preview = previewItems.slice(0, 3);
    return {
      slug: lang.slug,
      name: lang.names?.[0] || 'Unknown',
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
    if (user.role === 'admin') navigate('/create/language');
    else alert('Only administrators can create new entities.');
  };

  useEffect(() => {
    if (pendingCreation && user) {
      if (user.role === 'admin') navigate('/create/language');
      else alert('Only administrators can create new entities.');
      setPendingCreation(false);
    }
  }, [user, pendingCreation, navigate]);

  if (isLoading) return <div className="loader">Loading...</div>;
  if (error) return <div className="error">Error loading data</div>;

  return (
    <>
      <GenericCatalogPage
        title="Languages"
        entityType="language"
        data={adaptedData}
        headerActions={
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            {user?.role === 'admin' && (
              <button className="add-button" onClick={handleAddClick}>
                <FaPlus /> Add new language
              </button>
            )}
            <div className="sort-controls">
              <select value={localSortField} onChange={handleSortFieldChange}>
                <option value="name">Name</option>
                <option value="family">Family</option>
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
        <LanguageFilters
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

export default LanguagesPage;