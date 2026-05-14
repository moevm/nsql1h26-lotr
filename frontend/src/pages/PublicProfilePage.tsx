import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { FaHeart } from 'react-icons/fa';
import { useGetUserProfile, useGetUserLikedPages } from '../api/generated/users/users';

const PublicProfilePage: React.FC = () => {
  const { username } = useParams<{ username: string }>();
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const { data: profile, isLoading: profileLoading, error: profileError } = useGetUserProfile(username!);
  const { data: likedData, isLoading: likedLoading } = useGetUserLikedPages(username!, { page, page_size: pageSize });

  if (profileLoading) return <div className="loader">Loading profile...</div>;
  if (profileError) return <div className="error">User not found.</div>;
  if (!profile) return null;

  const likedPages = likedData?.results || [];
  const totalLiked = likedData?.count || 0;
  const hasPrev = likedData?.previous !== null;
  const hasNext = likedData?.next !== null;
  const handlePrevPage = () => { if (hasPrev) setPage(p => p - 1); };
  const handleNextPage = () => { if (hasNext) setPage(p => p + 1); };

  return (
    <>
      <div className="profile-page-container">
        <div className="profile-card-left">
          <div className="profile-avatar">
            <img src={profile.avatar_url || '/images/default-avatar.png'} alt="Avatar" />
          </div>
          <div className="profile-username">{profile.username}</div>
          <div className="profile-role">Created at: {new Date(profile.created_at).toLocaleDateString()}</div>
          <div className="profile-comments">Comments: {profile.comments_count || 0}</div>
        </div>
        <div className="profile-liked-right">
          <h2 className="liked-title">
            <FaHeart /> Liked
          </h2>
          {likedPages.length === 0 ? (
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
                <button className="pagination-btn" onClick={handlePrevPage} disabled={!hasPrev}>← Previous</button>
                <span className="pagination-info">Page {page} (total: {Math.ceil(totalLiked / pageSize)})</span>
                <button className="pagination-btn" onClick={handleNextPage} disabled={!hasNext}>Next →</button>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default PublicProfilePage;