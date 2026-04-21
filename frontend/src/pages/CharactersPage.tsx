import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListCharacters } from '../api/generated/characters/characters';
import FilterSection from '../components/FilterSection';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';

// Компонент фильтров (принимает filters и функции)
const CharacterFilters: React.FC<{
  localFilters: any;
  onLocalFilterChange: (key: string, value: any) => void;
  onApply: () => void;
  onReset: () => void;
}> = ({ localFilters, onLocalFilterChange, onApply, onReset }) => {
  // Вспомогательная функция для текстового поля
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

  // Фильтр gender (чекбоксы)
  const genderOptions = ['male', 'female', 'unknown'];
  const selectedGenders = localFilters.gender ? localFilters.gender.split(',') : [];
  const handleGenderChange = (value: string, checked: boolean) => {
    let newSelected = [...selectedGenders];
    if (checked) {
      if (!newSelected.includes(value)) newSelected.push(value);
    } else {
      newSelected = newSelected.filter(v => v !== value);
    }
    const newValue = newSelected.length ? newSelected.join(',') : undefined;
    onLocalFilterChange('gender', newValue);
  };

  // Фильтр is_alive (чекбоксы)
  const isAliveTrue = localFilters.is_alive === true;
  const isAliveFalse = localFilters.is_alive === false;
  const handleIsAliveChange = (value: boolean, checked: boolean) => {
    if (checked) {
      onLocalFilterChange('is_alive', value);
    } else {
      onLocalFilterChange('is_alive', undefined);
    }
  };

  return (
    <>
      <h2 className="filters-main-title">Filters</h2>
      {/* Каждый фильтр в своём аккордеоне */}
      <FilterSection title="Name">
        {renderTextFilter('', 'name')}
      </FilterSection>
      <FilterSection title="Titles">
        {renderTextFilter('', 'titles')}
      </FilterSection>
      <FilterSection title="Gender">
        <div className="filter-field">
          <div className="checkbox-group">
            {genderOptions.map(opt => (
              <label key={opt}>
                <input
                  type="checkbox"
                  value={opt}
                  checked={selectedGenders.includes(opt)}
                  onChange={(e) => handleGenderChange(opt, e.target.checked)}
                /> {opt}
              </label>
            ))}
          </div>
        </div>
      </FilterSection>
      <FilterSection title="Is alive">
        <div className="filter-field">
          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={isAliveTrue}
                onChange={(e) => handleIsAliveChange(true, e.target.checked)}
              /> Alive
            </label>
            <label>
              <input
                type="checkbox"
                checked={isAliveFalse}
                onChange={(e) => handleIsAliveChange(false, e.target.checked)}
              /> Died
            </label>
          </div>
        </div>
      </FilterSection>
      <FilterSection title="Birth date">
        <div className="filter-field">
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              className="filter-text-input"
              type="text"
              placeholder="Timeline (TA, SA...)"
              value={(localFilters.birth_date || '').split(' ')[0] || ''}
              onChange={(e) => {
                const yearPart = (localFilters.birth_date || '').split(' ')[1] || '';
                const newEra = e.target.value;
                const combined = newEra && yearPart ? `${newEra} ${yearPart}` : (newEra || yearPart || undefined);
                onLocalFilterChange('birth_date', combined);
              }}
            />
            <input
              className="filter-text-input"
              type="text"
              placeholder="year"
              value={(localFilters.birth_date || '').split(' ')[1] || ''}
              onChange={(e) => {
                const eraPart = (localFilters.birth_date || '').split(' ')[0] || '';
                const newYear = e.target.value;
                const combined = eraPart && newYear ? `${eraPart} ${newYear}` : (eraPart || newYear || undefined);
                onLocalFilterChange('birth_date', combined);
              }}
            />
          </div>
        </div>
      </FilterSection>
      <FilterSection title="Death date">
        <div className="filter-field">
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              className="filter-text-input"
              type="text"
              placeholder="Timeline (TA, SA...)"
              value={(localFilters.death_date || '').split(' ')[0] || ''}
              onChange={(e) => {
                const yearPart = (localFilters.death_date || '').split(' ')[1] || '';
                const newEra = e.target.value;
                const combined = newEra && yearPart ? `${newEra} ${yearPart}` : (newEra || yearPart || undefined);
                onLocalFilterChange('death_date', combined);
              }}
            />
            <input
              className="filter-text-input"
              type="text"
              placeholder="year"
              value={(localFilters.death_date || '').split(' ')[1] || ''}
              onChange={(e) => {
                const eraPart = (localFilters.death_date || '').split(' ')[0] || '';
                const newYear = e.target.value;
                const combined = eraPart && newYear ? `${eraPart} ${newYear}` : (eraPart || newYear || undefined);
                onLocalFilterChange('death_date', combined);
              }}
            />
          </div>
        </div>
      </FilterSection>
      <FilterSection title="Hair">
        {renderTextFilter('', 'hair')}
      </FilterSection>
      <FilterSection title="Eyes">
        {renderTextFilter('', 'eyes')}
      </FilterSection>
      <FilterSection title="Height">
        {renderTextFilter('', 'height')}
      </FilterSection>
      <FilterSection title="Weapon">
        {renderTextFilter('', 'weapon')}
      </FilterSection>
      <FilterSection title="Clothing">
        {renderTextFilter('', 'clothing')}
      </FilterSection>
      <FilterSection title="Notable for">
        {renderTextFilter('', 'notable_for')}
      </FilterSection>
      <FilterSection title="Race (slug)">
        {renderTextFilter('', 'race')}
      </FilterSection>
      <FilterSection title="Organization (slug)">
        {renderTextFilter('', 'organization')}
      </FilterSection>
      <FilterSection title="Event (slug)">
        {renderTextFilter('', 'event')}
      </FilterSection>
      <FilterSection title="Item (slug)">
        {renderTextFilter('', 'item')}
      </FilterSection>
      <FilterSection title="Location (slug)">
        {renderTextFilter('', 'location')}
      </FilterSection>
      <div className="filter-actions">
        <button className="apply-filters-btn" onClick={onApply}>Apply filters</button>
        <button className="reset-filters-btn" onClick={onReset}>Reset all</button>
      </div>
    </>
  );
};

const CharactersPage: React.FC = () => {
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
  const { data, isLoading, error } = useListCharacters(queryParams);

  const queryClient = useQueryClient();
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/characters'] });
    };
  }, []);

  const adaptedData = data?.results?.map(character => {
    const previewItems: string[] = [];
    if (character.notable_for?.trim()) previewItems.push(`Notable for: ${character.notable_for}`);
    if (character.gender?.trim()) previewItems.push(`Gender: ${character.gender}`);
    if (character.birth_date?.trim()) previewItems.push(`Birth date: ${character.birth_date}`);
    const preview = previewItems.slice(0, 3);
    return {
      slug: character.slug,
      name: character.names?.[0] || 'Unknown',
      preview,
    };
  }) || [];

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

  // Пагинация
  const totalCount = data?.count || 0;
  const hasPrev = data?.previous !== null;
  const hasNext = data?.next !== null;
  const handlePrevPage = () => { if (hasPrev) setPage(p => p - 1); };
  const handleNextPage = () => { if (hasNext) setPage(p => p + 1); };

  // Кнопка добавления
  const handleAddClick = () => {
    if (!user) {
      setShowAuthModal(true);
      setPendingCreation(true);
      return;
    }
    if (user.role === 'admin') navigate('/create/character');
    else alert('Only administrators can create new entities');
  };
  useEffect(() => {
    if (pendingCreation && user) {
      if (user.role === 'admin') navigate('/create/character');
      else alert('Only administrators can create new entities');
      setPendingCreation(false);
    }
  }, [user, pendingCreation, navigate]);

  if (isLoading) return <div className="loader">Loading...</div>;
  if (error) return <div className="error">Loading error</div>;

  return (
    <>
      <GenericCatalogPage
        title="Characters"
        entityType="character"
        data={adaptedData}
        headerActions={
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            {user?.role === 'admin' && (
              <button className="add-button" onClick={handleAddClick}>
                <FaPlus /> Add new character
              </button>
            )}
            <div className="sort-controls">
              <select value={localSortField} onChange={handleSortFieldChange}>
                <option value="name">Name</option>
                <option value="titles">Titles</option>
                <option value="gender">Gender</option>
                <option value="birth_date">Birth date</option>
                <option value="death_date">Death date</option>
                <option value="hair">Hair</option>
                <option value="eyes">Eyes</option>
                <option value="height">Height</option>
                <option value="weapon">Weapon</option>
                <option value="clothing">Clothing</option>
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
        <CharacterFilters
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

export default CharactersPage;