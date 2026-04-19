import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListEvents } from '../api/generated/events/events';
import FilterSection from '../components/FilterSection';
import { useState } from 'react';
import { FaPlus } from 'react-icons/fa';
import AddEntityModal from '../components/AddEntityModal';

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
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { data, isLoading, error } = useListEvents({ page: 1, page_size: 100 });

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки</div>;

  const adaptedData = data?.results?.map(event => ({
    slug: event.slug,
    name: event.names?.[0] || 'Без имени',
  })) || [];

  return (
    <>
      <GenericCatalogPage
        title="Events"
        entityType="event"
        data={adaptedData}
        headerActions={
          <button className="add-button" onClick={() => setIsModalOpen(true)}>
            <FaPlus /> Add new event
          </button>
        }
      >
        <EventsFilters />
      </GenericCatalogPage>
      {isModalOpen && (
        <AddEntityModal
          title="события"
          onClose={() => setIsModalOpen(false)}
          onSave={() => setIsModalOpen(false)}
        />
      )}
    </>
  );
};

export default EventsPage;