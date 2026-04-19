import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListCharacters } from '../api/generated/characters/characters';
import FilterSection from '../components/FilterSection';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';

const CharactersFilters = () => (
  <>
    <h2 className="filters-main-title">Filters</h2>
    <div className="filter-card">
      <FilterSection title="Раса">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Человек</label>
          <label><input type="checkbox" disabled /> Эльф</label>
          <label><input type="checkbox" disabled /> Хоббит</label>
          <label><input type="checkbox" disabled /> Гном</label>
          <label><input type="checkbox" disabled /> Майар</label>
        </div>
      </FilterSection>
    </div>
    <div className="filter-card">
      <FilterSection title="Пол">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Мужской</label>
          <label><input type="checkbox" disabled /> Женский</label>
        </div>
      </FilterSection>
    </div>
    <div className="filter-card">
      <FilterSection title="Локация">
        <div className="filter-placeholder">
          <label><input type="checkbox" disabled /> Шир</label>
          <label><input type="checkbox" disabled /> Гондор</label>
          <label><input type="checkbox" disabled /> Ривенделл</label>
          <label><input type="checkbox" disabled /> Лотлориэн</label>
        </div>
      </FilterSection>
    </div>
    <div className="filter-note">* Фильтры временно неактивны</div>
  </>
);

const CharactersPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showAuthModal, setShowAuthModal] = useState(false);

  const { data, isLoading, error } = useListCharacters({
    page: 1,
    page_size: 100,
  });

  // Адаптируем данные для GenericCatalogPage
  const adaptedData = data?.results?.map(character => ({
    slug: character.slug,
    name: character.names?.[0] || 'Без имени', // первый элемент массива names
  })) || [];

  console.log('data from API:', data);
  console.log('adaptedData:', adaptedData);

  const handleAddClick = () => {
    if (user) {
      navigate('/create/character');
    } else {
      setShowAuthModal(true);
    }
  };

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки</div>;
  
  return (
    <>
      <GenericCatalogPage
        title="Characters"
        entityType="character"
        data={adaptedData}
        headerActions={
          <button className="add-button" onClick={handleAddClick}>
            <FaPlus /> Add new character
          </button>
        }
      >
        <CharactersFilters />
      </GenericCatalogPage>
      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
          onSuccess={() => {
            setShowAuthModal(false);
            navigate('/create/character');
          }}
        />
      )}
    </>
  );
};

export default CharactersPage;