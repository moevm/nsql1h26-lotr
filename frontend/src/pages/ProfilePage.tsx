// src/pages/ProfilePage.tsx
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { FaEdit, FaHeart, FaKey, FaEnvelope } from 'react-icons/fa';
import ChangeEmailModal from '../components/ChangeEmailModal';
import ChangePasswordModal from '../components/ChangePasswordModal';
import { useQueryClient } from '@tanstack/react-query';
import { useGetMe, useGetLikedPages } from '../api/generated/auth/auth';

const ProfilePage: React.FC = () => {
  const { user, isLoading: authLoading, logout } = useAuth();
  const navigate = useNavigate();
  const [isEmailModalOpen, setIsEmailModalOpen] = useState(false);
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const queryClient = useQueryClient();

  // Запрос профиля
  const { refetch: refetchMe } = useGetMe({ query: { enabled: false } });

  // Запрос лайкнутых страниц (с пагинацией)
  const [likedPage, setLikedPage] = useState(1);
  const { data: likedData, isLoading: likedLoading, refetch: refetchLiked } = useGetLikedPages({ page: likedPage, page_size: 10 });

  useEffect(() => {
    refetchMe();
    refetchLiked();
  }, []);

  useEffect(() => {
    refetchLiked();
  }, [likedPage]);

  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: ['/auth/me'] });
      queryClient.removeQueries({ queryKey: ['/auth/me/liked'] });
    };
  }, [queryClient]);

  useEffect(() => {
    if (!user && !authLoading) {
      navigate('/');
    }
  }, [user, authLoading, navigate]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (authLoading) {
    return <div className="loader">Loading profile...</div>;
  }

  if (!user) return null;

  const roleText = user.role === 'admin' ? 'Admin' : 'Viewer';
  const likedPages = likedData?.results || [];
  const totalLiked = likedData?.count || 0;
  const hasNext = likedData?.next !== null;
  const hasPrev = likedData?.previous !== null;

  const loadMore = () => {
    if (hasNext) setLikedPage(prev => prev + 1);
  };
  const loadPrev = () => {
    if (hasPrev) setLikedPage(prev => prev - 1);
  };

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
        <button className="logout-btn" onClick={handleLogout}>Log out</button>
      </div>

      {/* Правая колонка – Liked pages */}
      <div className="profile-liked-right">
        <h2 className="liked-title">
          <FaHeart /> Liked
        </h2>
        {likedLoading ? (
          <div className="loader">Loading liked pages...</div>
        ) : likedPages.length === 0 ? (
          <div className="liked-placeholder"><p>No liked pages</p></div>
        ) : (
          <>
            <ul className="liked-list">
              {likedPages.map((page) => (
                <li key={page.slug}>
                  <Link to={`/pages/${page.slug}`}>{page.name}</Link>
                </li>
              ))}
            </ul>
            <div className="pagination-container">
              <button className="pagination-btn" onClick={loadPrev} disabled={!hasPrev}>← Previous</button>
              <span className="pagination-info">Page {likedPage} (total: {Math.ceil(totalLiked / 10)})</span>
              <button className="pagination-btn" onClick={loadMore} disabled={!hasNext}>Next →</button>
            </div>
          </>
        )}
      </div>

      {/* Модальные окна */}
      {isEmailModalOpen && <ChangeEmailModal onClose={() => setIsEmailModalOpen(false)} onSuccess={() => setIsEmailModalOpen(false)} />}
      {isPasswordModalOpen && <ChangePasswordModal onClose={() => setIsPasswordModalOpen(false)} onSuccess={() => setIsPasswordModalOpen(false)} />}
    </div>
  );
};

export default ProfilePage;