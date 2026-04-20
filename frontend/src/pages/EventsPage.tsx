import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListEvents } from '../api/generated/events/events';
import FilterSection from '../components/FilterSection';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

const EventsFilters = () => (
  <>
    <h2 className="filters-main-title">Фильтры</h2>
    <div className="filter-card">
      <FilterSection title="Тип события">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Война</label>
          <label><input type="checkbox" disabled /> Битва</label>
          <label><input type="checkbox" disabled /> Совет</label>
        </div>
      </FilterSection>
    </div>
  </>
);

const EventsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const queryClient = useQueryClient();
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/events'] });
    };
  }, []);

  const { data, isLoading, error } = useListEvents({ page: 1, page_size: 20 });

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки</div>;

  const adaptedData = data?.results?.map(event => ({
    slug: event.slug,
    name: event.names?.[0] || 'Без имени',
  })) || [];

  const handleAddClick = () => {
    if (user) {
      navigate('/create/event');
    } else {
      setShowAuthModal(true);
    }
  };

  return (
    <>
      <GenericCatalogPage
        title="Events"
        entityType="event"
        data={adaptedData}
        headerActions={
          <button className="add-button" onClick={handleAddClick}>
            <FaPlus /> Add new event
          </button>
        }
      >
        <EventsFilters />
      </GenericCatalogPage>
      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
          onSuccess={() => {
            setShowAuthModal(false);
            navigate('/create/event');
          }}
        />
      )}
    </>
  );
};

export default EventsPage;