import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { FaEdit, FaHeart } from 'react-icons/fa';
import EditProfileModal from '../components/EditProfileModal';
import { getLikes } from '../utils/likes';

// Импорт всех моковых данных (для поиска сущностей по slug)
import { mockCharacters } from '../mocks/data/characters';
import { mockLocations } from '../mocks/data/locations';
import { mockEvents } from '../mocks/data/events';
import { mockItems } from '../mocks/data/items';
import { mockRaces } from '../mocks/data/races';
import { mockOrganizations } from '../mocks/data/organizations';
import { mockLanguages } from '../mocks/data/languages';
import { mockScripts } from '../mocks/data/scripts';
import { mockTimelines } from '../mocks/data/timelines';

interface LikedEntity {
  slug: string;
  name: string;
  type: string;
}

const ProfilePage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [likedEntities, setLikedEntities] = useState<LikedEntity[]>([]);

  // Редирект, если не авторизован
  useEffect(() => {
    if (!user) {
      navigate('/');
    }
  }, [user, navigate]);

  // Загрузка лайкнутых сущностей
  useEffect(() => {
    if (!user) return;
    const slugs = getLikes(user.username);
    if (slugs.length === 0) {
      setLikedEntities([]);
      return;
    }

    // Собираем все сущности из всех моков
    const allEntities: LikedEntity[] = [
      ...(mockCharacters.results?.map(e => ({ slug: e.slug, name: e.name, type: 'character' })) || []),
      ...(mockLocations.results?.map(e => ({ slug: e.slug, name: e.name, type: 'location' })) || []),
      ...(mockEvents.results?.map(e => ({ slug: e.slug, name: e.name, type: 'event' })) || []),
      ...(mockItems.results?.map(e => ({ slug: e.slug, name: e.name, type: 'item' })) || []),
      ...(mockRaces.results?.map(e => ({ slug: e.slug, name: e.name, type: 'race' })) || []),
      ...(mockOrganizations.results?.map(e => ({ slug: e.slug, name: e.name, type: 'organization' })) || []),
      ...(mockLanguages.results?.map(e => ({ slug: e.slug, name: e.name, type: 'language' })) || []),
      ...(mockScripts.results?.map(e => ({ slug: e.slug, name: e.name, type: 'script' })) || []),
      ...(mockTimelines.results?.map(e => ({ slug: e.slug, name: e.name, type: 'timeline' })) || []),
    ];

    const liked = slugs
      .map(slug => allEntities.find(e => e.slug === slug))
      .filter((e): e is LikedEntity => e !== undefined);
    setLikedEntities(liked);
  }, [user]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (!user) return null; // пока идёт редирект

  return (
    <div className="profile-page-container">
      {/* Левая колонка – карточка профиля */}
      <div className="profile-card-left">
        <div className="profile-avatar">
          <img src="/images/default-avatar.png" alt="Avatar" />
        </div>
        <div className="profile-username">{user.username}</div>
        <div className="profile-role">Статус: user</div>
        <button className="edit-profile-btn" onClick={() => setIsEditModalOpen(true)}>
          <FaEdit /> Edit profile
        </button>
        <button className="logout-btn" onClick={handleLogout}>
          Log out
        </button>
      </div>

      {/* Правая колонка – Liked */}
      <div className="profile-liked-right">
        <h2 className="liked-title">
          <FaHeart /> Liked
        </h2>
        {likedEntities.length === 0 ? (
          <div className="liked-placeholder">
            <p>Нет понравившихся страниц</p>
          </div>
        ) : (
          <ul className="liked-list">
            {likedEntities.map(entity => (
              <li key={entity.slug}>
                <Link to={`/entity/${entity.type}/${entity.slug}`}>
                  {entity.name}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Модальное окно редактирования профиля */}
      {isEditModalOpen && (
        <EditProfileModal
          onClose={() => setIsEditModalOpen(false)}
          onSuccess={() => setIsEditModalOpen(false)}
        />
      )}
    </div>
  );
};

export default ProfilePage;