import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { FaEdit, FaHeart } from 'react-icons/fa';
import EditProfileModal from '../components/EditProfileModal';

const ProfilePage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // Редирект, если не авторизован
  useEffect(() => {
    if (!user) {
      navigate('/');
    }
  }, [user, navigate]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (!user) return null;

  // Отображаем роль
  const roleText = user.role === 'admin' ? 'Admin' : 'Viewer';

  return (
    <div className="profile-page-container">
      {/* Левая колонка – карточка профиля */}
      <div className="profile-card-left">
        <div className="profile-avatar">
          <img src={user.avatarUrl || '/images/default-avatar.png'} alt="Avatar" />
        </div>
        <div className="profile-username">{user.username}</div>
        <div className="profile-role">Role: {roleText}</div>
        <button className="edit-profile-btn" onClick={() => setIsEditModalOpen(true)}>
          <FaEdit /> Edit profile
        </button>
        <button className="logout-btn" onClick={handleLogout}>
          Log out
        </button>
      </div>

      {/* Правая колонка – Liked pages*/}
      <div className="profile-liked-right">
        <h2 className="liked-title">
          <FaHeart /> Liked
        </h2>
        {!user.likedPages || user.likedPages.length === 0 ? (
          <div className="liked-placeholder">
            <p>Нет понравившихся страниц</p>
          </div>
        ) : (
          <ul className="liked-list">
            {user.likedPages.map((page) => (
              <li key={page.slug}>
                <Link to={`/entity/${page.type}/${page.slug}`}>
                  {page.name}
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