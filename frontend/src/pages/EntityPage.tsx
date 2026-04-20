import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { FaHeart, FaRegHeart, FaEdit } from 'react-icons/fa';
import { MdOutlineFileDownload, MdOutlineFileUpload } from 'react-icons/md';
import { SiRelay } from 'react-icons/si';
import { useGetPage, useLikePage, useUnlikePage } from '../api/generated/pages/pages';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import AuthModal from '../components/AuthModal';

const EntityPage: React.FC = () => {
  const { type, slug } = useParams<{ type: string; slug: string }>();
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useGetPage(slug!);
  const likeMutation = useLikePage();
  const unlikeMutation = useUnlikePage();

  const [liked, setLiked] = useState(false);
  const [likesCount, setLikesCount] = useState(0);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showAuthModalForEdit, setShowAuthModalForEdit] = useState(false);

  // При загрузке данных устанавливаем начальные значения лайков
  useEffect(() => {
    if (data) {
      setLiked(data.isLiked || false);
      setLikesCount(data.likesCount || 0);
    }
  }, [data]);

  // Очистка кэша при размонтировании (опционально)
  useEffect(() => {
    return () => {
      queryClient.removeQueries({ queryKey: [`/pages/${slug}`] });
    };
  }, [slug, queryClient]);

  const handleLike = async () => {
    if (!user) {
      setShowAuthModal(true);
      return;
    }
    if (!data) return;

    try {
      if (liked) {
        const result = await unlikeMutation.mutateAsync({ slug: slug! });
        setLiked(result.isLiked);
        setLikesCount(result.likesCount);
      } else {
        const result = await likeMutation.mutateAsync({ slug: slug! });
        setLiked(result.isLiked);
        setLikesCount(result.likesCount);
      }
      // Обновляем данные пользователя в контексте
      await refreshUser();
      // Инвалидируем кэш страницы
      await queryClient.invalidateQueries({ queryKey: [`/pages/${slug}`] });
    } catch (err) {
      console.error('Like/unlike failed:', err);
    }
  };

  if (isLoading) return <div className="loader">Загрузка...</div>;
  if (error) return <div className="error">Ошибка загрузки страницы</div>;
  if (!data) return <div className="error">Страница не найдена</div>;

  const mainName = data.names?.[0] || 'Без имени';
  const article = data.article || { text: '', imageUrl: '', createdAt: null, updatedAt: null };

  const formatDate = (isoString: string | null) => {
    if (!isoString) return 'Дата неизвестна';
    return new Date(isoString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const createdAt = formatDate(article.createdAt);
  const updatedAt = formatDate(article.updatedAt);

  const renderRelationList = (
    relations: Record<string, any[]> | undefined,
    direction: 'outgoing' | 'incoming'
  ) => {
    const entries = Object.entries(relations || {});
    if (entries.length === 0) return <p>Нет связей</p>;

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

  const outgoingRelations = data.relations?.outgoing || {};
  const incomingRelations = data.relations?.incoming || {};

  return (
    <div className="entity-page">
      <div className="entity-two-columns">
        {/* Левая колонка */}
        <div className="entity-left">
          <div className="entity-left-header">
            <h1 className="entity-title">{mainName}</h1>
            <div className="entity-actions">
              <button className="icon-btn" title="Экспорт">
                <MdOutlineFileDownload />
              </button>
              <button className="icon-btn" title="Импорт">
                <MdOutlineFileUpload />
              </button>
              <span className="entity-dates">
                Создана: {createdAt} | Обновлена: {updatedAt}
              </span>
            </div>
          </div>

          <div className="article-text">
            <p>{article.text || 'Описание отсутствует'}</p>
          </div>

          <details className="relations-section">
            <summary>Исходящие связи</summary>
            {renderRelationList(outgoingRelations, 'outgoing')}
          </details>

          <details className="relations-section">
            <summary>Входящие связи</summary>
            {renderRelationList(incomingRelations, 'incoming')}
          </details>

          <div className="comments-section">
            <h3>Комментарии</h3>
            <div className="comment-input">
              <input type="text" placeholder="Написать комментарий..." disabled />
              <button disabled>Отправить</button>
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
              {liked ? <FaHeart /> : <FaRegHeart />} {likesCount}
            </button>
            <button
              className="icon-btn"
              onClick={() => {
                if (user) {
                  navigate(`/edit/${type}/${slug}`);
                } else {
                  setShowAuthModalForEdit(true);
                }
              }}
            >
              <FaEdit />
            </button>
            <button className="icon-btn" disabled>
              <SiRelay />
            </button>
          </div>

          <div className="entity-card">
            <img
              src={article.imageUrl || '/images/default-avatar.png'}
              alt={mainName}
              className="entity-image"
            />
            <div className="entity-attributes">
              <h3>{mainName}</h3>
              <table className="attr-table">
                <tbody>
                  {Object.entries(data.attributes || {})
                    .filter(([_, value]) => {
                      if (value == null) return false;
                      if (value === '') return false;
                      if (Array.isArray(value) && value.length === 0) return false;
                      return true;
                    })
                    .map(([key, value]) => (
                      <tr key={key}>
                        <td className="attr-key">{key.replace(/_/g, ' ')}</td>
                        <td className="attr-value">{value as string}</td>
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
          onClose={() => setShowAuthModal(false)}
          onSuccess={() => setShowAuthModal(false)}
        />
      )}
      {showAuthModalForEdit && (
        <AuthModal
          onClose={() => setShowAuthModalForEdit(false)}
          onSuccess={() => {
            setShowAuthModalForEdit(false);
            navigate(`/edit/${type}/${slug}`);
          }}
        />
      )}
    </div>
  );
};

export default EntityPage;