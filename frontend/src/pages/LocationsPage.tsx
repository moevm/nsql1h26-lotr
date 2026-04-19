import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListLocations } from '../api/generated/locations/locations';
import AddEntityModal from '../components/AddEntityModal';
import { FaPlus } from 'react-icons/fa';
import { useState } from 'react';
import FilterSection from '../components/FilterSection';

const LocationsFilters = () => (
  <>
    <h2 className="filters-main-title">Фильтры</h2>
    <div className="filter-card">
      <FilterSection title="Регион">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Эриадор</label>
          <label><input type="checkbox" disabled /> Гондор</label>
          <label><input type="checkbox" disabled /> Рохан</label>
          <label><input type="checkbox" disabled /> Мордор</label>
        </div>
      </FilterSection>
    </div>
    <div className="filter-card">
      <FilterSection title="Тип">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Город</label>
          <label><input type="checkbox" disabled /> Крепость</label>
          <label><input type="checkbox" disabled /> Лес</label>
          <label><input type="checkbox" disabled /> Горы</label>
        </div>
      </FilterSection>
    </div>
  </>
);

const LocationsPage: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Используем сгенерированный хук для получения списка локаций
  const { data, isLoading, error } = useListLocations({
    page: 1,
    page_size: 100,
  });

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки</div>;

  // Адаптируем данные
  const adaptedData = data?.results?.map(location => ({
    slug: location.slug,
    name: location.names?.[0] || 'Без имени',
  })) || [];

  return (
    <>
      <GenericCatalogPage
        title="Locations"
        entityType="location"
        data={adaptedData}
        headerActions={
          <button className="add-button" onClick={() => setIsModalOpen(true)}>
            <FaPlus /> Add new location
          </button>
        }
      >
        <LocationsFilters />
      </GenericCatalogPage>

      {isModalOpen && (
        <AddEntityModal
          title="локации"
          onClose={() => setIsModalOpen(false)}
          onSave={(formData) => {
            console.log('Сохранение локации:', formData);
            // Здесь позже будет вызов useCreateLocation
            setIsModalOpen(false);
          }}
        />
      )}
    </>
  );
};

export default LocationsPage;