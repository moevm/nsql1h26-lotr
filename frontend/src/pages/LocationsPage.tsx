import GenericCatalogPage from '../components/GenericCatalogPage';
import { useNavigate } from 'react-router-dom';
import { useListLocations } from '../api/generated/locations/locations';
import { FaPlus } from 'react-icons/fa';
import { useState } from 'react';
import FilterSection from '../components/FilterSection';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

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
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const queryClient = useQueryClient();
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/locations'] });
    };
  }, []);

  const { data, isLoading, error } = useListLocations({
    page: 1,
    page_size: 20,
  });

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки</div>;

  // Адаптируем данные
  const adaptedData = data?.results?.map(location => ({
    slug: location.slug,
    name: location.names?.[0] || 'Без имени',
  })) || [];

  const handleAddClick = () => {
    if (user) {
      navigate('/create/location');
    } else {
      setShowAuthModal(true);
    }
  };

  return (
    <>
      <GenericCatalogPage
        title="Locations"
        entityType="location"
        data={adaptedData}
        headerActions={
          <button className="add-button" onClick={handleAddClick}>
            <FaPlus /> Add new location
          </button>
        }
      >
        <LocationsFilters />
      </GenericCatalogPage>

      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
          onSuccess={() => {
            setShowAuthModal(false);
            navigate('/create/location');
          }}
        />
      )}
    </>
  );
};

export default LocationsPage;