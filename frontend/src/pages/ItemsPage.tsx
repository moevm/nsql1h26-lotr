import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListItems } from '../api/generated/items/items';
import FilterSection from '../components/FilterSection';
import { useState } from 'react';
import { FaPlus } from 'react-icons/fa';
import AddEntityModal from '../components/AddEntityModal';

const ItemsFilters = () => (
  <>
    <h2 className="filters-main-title">Фильтры</h2>
    <div className="filter-card">
      <FilterSection title="Категория">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Оружие</label>
          <label><input type="checkbox" disabled /> Артефакты</label>
          <label><input type="checkbox" disabled /> Броня</label>
          <label><input type="checkbox" disabled /> Еда</label>
        </div>
      </FilterSection>
    </div>
    <div className="filter-card">
      <FilterSection title="Редкость">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Обычный</label>
          <label><input type="checkbox" disabled /> Легендарный</label>
        </div>
      </FilterSection>
    </div>
    <div className="filter-note">* Фильтры временно неактивны</div>
  </>
);

const ItemsPage: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { data, isLoading, error } = useListItems({ page: 1, page_size: 100 });

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки</div>;

  const adaptedData = data?.results?.map(item => ({
    slug: item.slug,
    name: item.name,
  })) || [];

  return (
    <>
      <GenericCatalogPage
        title="Items"
        entityType="item"
        data={adaptedData}
        headerActions={
          <button className="add-button" onClick={() => setIsModalOpen(true)}>
            <FaPlus /> Add new item
          </button>
        }
      >
        <ItemsFilters />
      </GenericCatalogPage>
      {isModalOpen && (
        <AddEntityModal
          title="предмета"
          onClose={() => setIsModalOpen(false)}
          onSave={() => setIsModalOpen(false)}
        />
      )}
    </>
  );
};

export default ItemsPage;