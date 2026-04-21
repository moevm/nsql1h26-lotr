import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import GenericCatalogPage from '../components/GenericCatalogPage';
import { useListCharacters } from '../api/generated/characters/characters';
import FilterSection from '../components/FilterSection';
import { FaPlus } from 'react-icons/fa';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';

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
  const [pendingCreation, setPendingCreation] = useState(false);
  const [page, setPage] = useState(1);
  const page_size = 20;
  const queryClient = useQueryClient();
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/characters'] });
    };
  }, []);

  const { data, isLoading, error } = useListCharacters({
    page,
    page_size: page_size,
  });

  // Адаптируем данные
  const response = data as any;
  const adaptedData = response?.results?.map((character: any) => {
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

  const totalCount = response?.count || 0;
  const hasPrev = response?.previous !== null;
  const hasNext = response?.next !== null;

  const handlePrevPage = () => {
    if (hasPrev) setPage(p => p - 1);
  };
  const handleNextPage = () => {
    if (hasNext) setPage(p => p + 1);
  };

  const handleAddClick = () => {
    if (!user) {
      setShowAuthModal(true);
      setPendingCreation(true);
      return;
    }
    if (user.role === 'admin') {
      navigate('/create/character');
    } else {
      alert('Только администраторы могут создавать новые сущности.');
    }
  };

  useEffect(() => {
    if (pendingCreation && user) {
      if (user.role === 'admin') {
        navigate('/create/character');
      } else {
        alert('Только администраторы могут создавать новые сущности.');
      }
      setPendingCreation(false);
    }
  }, [user, pendingCreation, navigate]);

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
          ← Previous
        </button>
        <span className="pagination-info">
          Page {page} (total: {Math.ceil(totalCount / page_size)})
        </span>
        <button
          className="pagination-btn"
          onClick={handleNextPage}
          disabled={!hasNext || isLoading}
        >
          Next →
        </button>
      </div>

      {showAuthModal && (
        <AuthModal
          onClose={() => {
            setShowAuthModal(false);
            setPendingCreation(false);
          }}
          onSuccess={() => {
            setShowAuthModal(false);
          }}
        />
      )}
    </>
  );
};

export default CharactersPage;