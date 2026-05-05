import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { FaEdit, FaHeart, FaKey, FaEnvelope } from 'react-icons/fa';
import ChangeEmailModal from '../components/ChangeEmailModal';
import ChangePasswordModal from '../components/ChangePasswordModal';
import { useQueryClient } from '@tanstack/react-query';
import { useGetMe } from '../api/generated/auth/auth';

const ProfilePage: React.FC = () => {
  const { user, isLoading, logout } = useAuth();
  const navigate = useNavigate();
  const [isEmailModalOpen, setIsEmailModalOpen] = useState(false);
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const queryClient = useQueryClient();

  const { refetch } = useGetMe({
    query: { enabled: false }
  });

  useEffect(() => {
    refetch(); // выполняем запрос при монтировании страницы
  }, [refetch]);

  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/auth/me'] });
    };
  }, [queryClient]);

  useEffect(() => {
    if (!user) {
      navigate('/');
    }
  }, [user, navigate]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (isLoading) {
    return <div className="loader">Loading profile...</div>;
  }

  if (!user) return null;

  const roleText = user.role === 'admin' ? 'Admin' : 'Viewer';

  return (
    <div className="profile-page-container">
      {/* Левая колонка – карточка профиля */}
      <div className="profile-card-left">
        <div className="profile-avatar">
          <img src={user.avatar_url || '/images/default-avatar.png'} alt="Avatar" />
        </div>
        <div className="profile-username">{user.username}</div>
        <div className="profile-role">Role: {roleText}</div>
        <div>
          <button className="edit-profile-btn" onClick={() => setIsEmailModalOpen(true)}>
            <FaEnvelope /> Change Email
          </button>
          <button className="edit-profile-btn" onClick={() => setIsPasswordModalOpen(true)}>
            <FaKey /> Change Password
          </button>
        </div>
        <button className="logout-btn" onClick={handleLogout}>
          Log out
        </button>
      </div>

      {/* Правая колонка – Liked pages */}
      <div className="profile-liked-right">
        <h2 className="liked-title">
          <FaHeart /> Liked
        </h2>
        {!user.likedPages || user.likedPages.length === 0 ? (
          <div className="liked-placeholder">
            <p>No liked pages</p>
          </div>
        ) : (
          <ul className="liked-list">
            {user.likedPages.map((page) => (
              <li key={page.slug}>
                <Link to={`/pages/${page.slug}`}>
                  {page.name}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Модальные окна */}
      {isEmailModalOpen && (
        <ChangeEmailModal
          onClose={() => setIsEmailModalOpen(false)}
          onSuccess={() => setIsEmailModalOpen(false)}
        />
      )}
      {isPasswordModalOpen && (
        <ChangePasswordModal
          onClose={() => setIsPasswordModalOpen(false)}
          onSuccess={() => setIsPasswordModalOpen(false)}
        />
      )}
    </div>
  );
};

export default ProfilePage;