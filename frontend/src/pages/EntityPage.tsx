import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { FaHeart, FaRegHeart, FaEdit } from 'react-icons/fa';
import { MdOutlineFileDownload, MdOutlineFileUpload } from 'react-icons/md';
import { SiRelay } from 'react-icons/si';
import { useGetPage, useLikePage, useUnlikePage, useDeletePage } from '../api/generated/pages/pages';
import type { LikeStateResponse } from '../api/generated/models';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import AuthModal from '../components/AuthModal';

const EntityPage: React.FC = () => {
  const { type, slug } = useParams<{ type: string; slug: string }>();
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useGetPage(slug!);
  const pageData = data as any;
  const likeMutation = useLikePage();
  const unlikeMutation = useUnlikePage();
  const deleteMutation = useDeletePage();

  const [liked, setLiked] = useState(false);
  const [likes_count, setlikes_count] = useState(0);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [pendingEdit, setPendingEdit] = useState(false);
  const [pendingLike, setPendingLike] = useState(false);

  // При загрузке данных устанавливаем начальные значения лайков
  useEffect(() => {
    if (data) {
      setLiked(pageData?.is_liked || false);
      setlikes_count(pageData?.likes_count || 0);
    }
  }, [data]);

  // Очистка кэша при размонтировании
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: [`/pages/${slug}`] });
    };
  }, [slug, queryClient]);

  const handleLike = async () => {
    if (!user) {
      setShowAuthModal(true);
      setPendingLike(true);
      return;
    }
    if (!data) return;

    try {
      let result: LikeStateResponse;
      if (liked) {
        const response = await unlikeMutation.mutateAsync({ slug: slug! });
        result = response as unknown as LikeStateResponse;
        setLiked(result.is_liked);
        setlikes_count(result.likes_count);
      } else {
        const response = await likeMutation.mutateAsync({ slug: slug! });
        result = response as unknown as LikeStateResponse;
        setLiked(result.is_liked);
        setlikes_count(result.likes_count);
      }
      // Обновляем данные пользователя в контексте
      await refreshUser();
      // Инвалидируем кэш страницы
      await queryClient.invalidateQueries({ queryKey: [`/pages/${slug}`] });
    } catch (err) {
      console.error('Like/unlike failed:', err);
    }
  };

  const handleDelete = async () => {
    if (!user) {
      setShowAuthModal(true);
      return;
    }
    if (user.role !== 'admin') {
      alert('Only administrators can delete pages.');
      return;
    }
    const confirmed = window.confirm('Are you sure you want to delete this page? This action is irreversible.');
    if (!confirmed) return;
    try {
      await deleteMutation.mutateAsync({ slug: slug! });
      // После успешного удаления перенаправляем на список
      navigate(`/${type}s`);
    } catch (err) {
      console.error('Delete failed:', err);
      alert('Error deleting page.');
    }
  };

  // Обработчик редактирования
  const handleEditClick = () => {
    if (!user) {
      setShowAuthModal(true);
      setPendingEdit(true);
      return;
    }
    if (user.role === 'admin') {
      navigate(`/edit/${type}/${slug}`);
    } else {
      alert('Only administrators can edit pages.');
    }
  };

  // Следим за изменением user после открытия модалки
  useEffect(() => {
    if (pendingEdit && user) {
      if (user.role === 'admin') {
        navigate(`/edit/${type}/${slug}`);
      } else {
        alert('Only administrators can edit pages.');
      }
      setPendingEdit(false);
    }
  }, [user, pendingEdit, navigate, type, slug]);

  // Аналогично для лайка
  useEffect(() => {
    if (pendingLike && user) {
      handleLike(); // повторно вызываем лайк
      setPendingLike(false);
    }
  }, [user, pendingLike]);

  if (isLoading) return <div className="loader">Loading...</div>;
  if (error) {
    // Извлекаем статус и сообщение из ошибки Axios
    const axiosError = error as any;
    let errorMessage = 'Error loading page';
    if (axiosError.response?.status === 404) {
      errorMessage = 'Page not found';
    } else if (axiosError.response?.data?.error?.message) {
      errorMessage = axiosError.response.data.error.message;
    } else if (axiosError.message) {
      errorMessage = axiosError.message;
    }
    alert(errorMessage);
  }
  if (!data) return <div className="error">Page not found</div>;

  const mainName = pageData?.names?.[0] || 'Unnamed';
  const article = pageData?.article || { text: '', image_url: '', created_at: null, updated_at: null };

  const formatDate = (isoString: string | null) => {
    if (!isoString) return 'Date unknown';
    return new Date(isoString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const created_at = formatDate(article.created_at);
  const updated_at = formatDate(article.updated_at);

  const renderRelationList = (
    relations: Record<string, any[]> | undefined,
    direction: 'outgoing' | 'incoming'
  ) => {
    const entries = Object.entries(relations || {});
    if (entries.length === 0) return <p>No relations</p>;

    return (
      <div className="relations-group">
        {entries.map(([relType, items]) => (
          <div key={relType} className="relation-type">
            <h4>{relType.replace(/_/g, ' ')}</h4>
            <ul>
              {items.map((item, idx) => {
                const target = direction === 'outgoing' ? item.target : item.from;
                if (!target) return null;
                const props = item.properties || {};
                const propsStr = Object.entries(props)
                  .map(([k, v]) => `${k}: ${v}`)
                  .join(', ');
                return (
                  <li key={idx}>
                    <Link to={`/entity/${target.type}/${target.slug}`}>
                      {target.name}
                    </Link>
                    {propsStr && <span className="props"> ({propsStr})</span>}
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
    );
  };

  const outgoingRelations = pageData?.relations?.outgoing || {};
  const incomingRelations = pageData?.relations?.incoming || {};

  return (
    <div className="entity-page">
      <div className="entity-two-columns">
        {/* Левая колонка */}
        <div className="entity-left">
          <div className="entity-left-header">
            <h1 className="entity-title">{mainName}</h1>
            <div className="entity-actions">
              <button className="icon-btn" title="Export">
                <MdOutlineFileDownload />
              </button>
              <button className="icon-btn" title="Import">
                <MdOutlineFileUpload />
              </button>
              <span className="entity-dates">
                Created: {created_at} | Updated: {updated_at}
              </span>
              {user?.role === 'admin' && (
                <button className="delete-btn" title="Delete" onClick={handleDelete}>
                  Delete page
                </button>
              )}
            </div>
          </div>

          <div className="article-text">
            <p>{article.text || 'Description missing'}</p>
          </div>

          <details className="relations-section">
            <summary>Outgoing relations</summary>
            {renderRelationList(outgoingRelations, 'outgoing')}
          </details>

          <details className="relations-section">
            <summary>Incoming relations</summary>
            {renderRelationList(incomingRelations, 'incoming')}
          </details>

          <div className="comments-section">
            <h3>Comments</h3>
            <div className="comment-input">
              <input type="text" placeholder="Write a comment..." disabled />
              <button disabled>Send</button>
            </div>
            <div className="todo">
              <p>Комментарии появятся на следующей итерации</p>
            </div>
          </div>
        </div>

        {/* Правая колонка */}
        <div className="entity-right">
          <div className="entity-right-actions">
            <button
              className={`like-btn ${liked ? 'liked' : ''}`}
              onClick={handleLike}
            >
              {liked ? <FaHeart /> : <FaRegHeart />} {likes_count}
            </button>
            {user?.role === 'admin' && (
              <button className="icon-btn" onClick={handleEditClick}>
                <FaEdit />
              </button>
            )}
            <button className="icon-btn" disabled>
              <SiRelay />
            </button>
          </div>

          <div className="entity-card">
            <img
              src={article.image_url || '/images/default-avatar.png'}
              alt={mainName}
              className="entity-image"
            />
            <div className="entity-attributes">
              <h3>{mainName}</h3>
              <table className="attr-table">
                <tbody>
                  {/* Строка для всех имён */}
                  {pageData.names && pageData.names.length > 0 && (
                    <tr>
                      <td className="attr-key">Names</td>
                      <td className="attr-value">{pageData.names.join(', ')}</td>
                    </tr>
                  )}
                  {Object.entries(pageData.attributes || {})
                    .filter(([_, value]) => {
                      if (value == null) return false;
                      if (value === '') return false;
                      if (Array.isArray(value) && value.length === 0) return false;
                      return true;
                    })
                    .map(([key, value]) => (
                      <tr key={key}>
                        <td className="attr-key">{key.replace(/_/g, ' ')}</td>
                        <td className="attr-value">
                          {Array.isArray(value) ? value.join(', ') : value as string}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {showAuthModal && (
        <AuthModal
          onClose={() => {
            setShowAuthModal(false);
            setPendingEdit(false);
            setPendingLike(false);
          }}
          onSuccess={() => {
            setShowAuthModal(false);
          }}
        />
      )}
    </div>
  );
};

export default EntityPage;