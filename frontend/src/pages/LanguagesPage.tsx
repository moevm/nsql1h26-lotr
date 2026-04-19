import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListLanguages } from '../api/generated/languages/languages';
import FilterSection from '../components/FilterSection';
import { useState } from 'react';
import { FaPlus } from 'react-icons/fa';
import AddEntityModal from '../components/AddEntityModal';

const LanguagesFilters = () => (
  <>
    <h2 className="filters-main-title">Фильтры</h2>
    <div className="filter-card">
      <FilterSection title="Языковая семья">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Эльфийские</label>
          <label><input type="checkbox" disabled /> Гномьи</label>
          <label><input type="checkbox" disabled /> Людские</label>
        </div>
      </FilterSection>
    </div>
  </>
);

const LanguagesPage: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { data, isLoading, error } = useListLanguages({ page: 1, page_size: 100 });

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки</div>;

  const adaptedData = data?.results?.map(lang => ({
    slug: lang.slug,
    name: lang.name,
  })) || [];

  return (
    <>
      <GenericCatalogPage
        title="Languages"
        entityType="language"
        data={adaptedData}
        headerActions={
          <button className="add-button" onClick={() => setIsModalOpen(true)}>
            <FaPlus /> Add new language
          </button>
        }
      >
        <LanguagesFilters />
      </GenericCatalogPage>
      {isModalOpen && (
        <AddEntityModal
          title="языка"
          onClose={() => setIsModalOpen(false)}
          onSave={() => setIsModalOpen(false)}
        />
      )}
    </>
  );
};

export default LanguagesPage;