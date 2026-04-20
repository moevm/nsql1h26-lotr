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
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading, error } = useListCharacters({
    page,
    page_size: pageSize,
  });

  // Адаптируем данные
  const adaptedData = data?.results?.map(character => {
    const previewItems: string[] = [];
    if (character.notable_for && character.notable_for.trim() !== '') {
      previewItems.push(`Notable for: ${character.notable_for}`);
    }
    if (character.gender && character.gender.trim() !== '') {
      previewItems.push(`Gender: ${character.gender}`);
    }
    if (character.birth_date && character.birth_date.trim() !== '') {
      previewItems.push(`Birth date: ${character.birth_date}`);
    }
    const preview = previewItems.slice(0, 3);
    return {
      slug: character.slug,
      name: character.names?.[0] || 'Без имени',
      preview,
    };
  }) || [];

  const totalCount = data?.count || 0;
  const hasPrev = data?.previous !== null;
  const hasNext = data?.next !== null;

  const handlePrevPage = () => {
    if (hasPrev) setPage(p => p - 1);
  };
  const handleNextPage = () => {
    if (hasNext) setPage(p => p + 1);
  };

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

      <div className="pagination-container">
        <button
          className="pagination-btn"
          onClick={handlePrevPage}
          disabled={!hasPrev || isLoading}
        >
          ← Назад
        </button>
        <span className="pagination-info">
          Страница {page} (всего: {Math.ceil(totalCount / pageSize)})
        </span>
        <button
          className="pagination-btn"
          onClick={handleNextPage}
          disabled={!hasNext || isLoading}
        >
          Вперёд →
        </button>
      </div>

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