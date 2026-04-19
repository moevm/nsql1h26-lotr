import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListRaces } from '../api/generated/races/races';
import FilterSection from '../components/FilterSection';
import { useState } from 'react';
import { FaPlus } from 'react-icons/fa';
import AddEntityModal from '../components/AddEntityModal';

const RacesFilters = () => (
  <>
    <h2 className="filters-main-title">Фильтры</h2>
    <div className="filter-card">
      <FilterSection title="Продолжительность жизни">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Бессмертные</label>
          <label><input type="checkbox" disabled /> 100-200 лет</label>
          <label><input type="checkbox" disabled /> 70-100 лет</label>
        </div>
      </FilterSection>
    </div>
    <div className="filter-card">
      <FilterSection title="Отличительные черты">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Маленький рост</label>
          <label><input type="checkbox" disabled /> Бородатые</label>
        </div>
      </FilterSection>
    </div>
  </>
);

const RacesPage: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { data, isLoading, error } = useListRaces({ page: 1, page_size: 100 });

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки</div>;

  const adaptedData = data?.results?.map(race => ({
    slug: race.slug,
    name: race.name,
  })) || [];

  return (
    <>
      <GenericCatalogPage
        title="Races"
        entityType="race"
        data={adaptedData}
        headerActions={
          <button className="add-button" onClick={() => setIsModalOpen(true)}>
            <FaPlus /> Add new race
          </button>
        }
      >
        <RacesFilters />
      </GenericCatalogPage>
      {isModalOpen && (
        <AddEntityModal
          title="расы"
          onClose={() => setIsModalOpen(false)}
          onSave={() => setIsModalOpen(false)}
        />
      )}
    </>
  );
};

export default RacesPage;