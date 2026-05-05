// src/pages/EntityPage.tsx
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
import ErrorModal from '../components/ErrorModal';

// Интерфейсы для сгруппированных связей
interface GroupedRelationItem {
  linkedEntity: {
    slug: string;
    type: string;
    name: string;
    imageUrl: string;
  };
  properties: Record<string, any>;
}

interface RelationGroup {
  relationType: string;
  items: GroupedRelationItem[];
}

interface EntityTypeRelations {
  outgoing: RelationGroup[];
  incoming: RelationGroup[];
}

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
  const [errorModalOpen, setErrorModalOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [errorStatusCode, setErrorStatusCode] = useState<number | undefined>(undefined);
  const [pendingEdit, setPendingEdit] = useState(false);
  const [pendingLike, setPendingLike] = useState(false);

  useEffect(() => {
    if (data) {
      setLiked(pageData?.is_liked || false);
      setlikes_count(pageData?.likes_count || 0);
    }
  }, [data]);

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
      await refreshUser();
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
      setErrorMessage('Only administrators can delete pages.');
      setErrorModalOpen(true);
      return;
    }
    const confirmed = window.confirm('Are you sure you want to delete this page? This action is irreversible.');
    if (!confirmed) return;
    try {
      await deleteMutation.mutateAsync({ slug: slug! });
      navigate(`/${type}s`);
    } catch (err: any) {
      console.error('Delete failed:', err);
      const statusCode = err.response?.status;
      setErrorStatusCode(statusCode);
      setErrorMessage('Error deleting page');
      setErrorModalOpen(true);
    }
  };

  const handleEditClick = () => {
    if (!user) {
      setShowAuthModal(true);
      setPendingEdit(true);
      return;
    }
    if (user.role === 'admin') {
      navigate(`/edit/${slug}`);
    } else {
      setErrorMessage('Only administrators can edit pages');
      setErrorModalOpen(true);
    }
  };

  useEffect(() => {
    if (pendingEdit && user) {
      if (user.role === 'admin') {
        navigate(`/edit/${slug}`);
      } else {
        setErrorMessage('Only administrators can edit pages');
        setErrorModalOpen(true);
      }
      setPendingEdit(false);
    }
  }, [user, pendingEdit, navigate, type, slug]);

  useEffect(() => {
    if (pendingLike && user) {
      handleLike();
      setPendingLike(false);
    }
  }, [user, pendingLike]);

  if (isLoading) return <div className="loader">Loading...</div>;
  if (error) {
    const axiosError = error as any;
    let errMsg = 'Error loading page';
    if (axiosError.response?.status === 404) {
      errMsg = 'Page not found';
    } else if (axiosError.response?.data?.error?.message) {
      errMsg = axiosError.response.data.error.message;
    } else if (axiosError.message) {
      errMsg = axiosError.message;
    }
    setErrorMessage(errMsg);
    setErrorModalOpen(true);
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

  // Группировка связей по типу сущности
  const outgoingRelations = pageData?.relations?.outgoing || {};
  const incomingRelations = pageData?.relations?.incoming || {};
  const relationsByEntityType: Record<string, EntityTypeRelations> = {};

  // Обработка исходящих связей
  for (const [relType, items] of Object.entries(outgoingRelations)) {
    for (const item of items as any[]) {
      const target = item.target;
      if (!target?.type) continue;
      const entityType = target.type;
      if (!relationsByEntityType[entityType]) {
        relationsByEntityType[entityType] = { outgoing: [], incoming: [] };
      }
      let group = relationsByEntityType[entityType].outgoing.find(g => g.relationType === relType);
      if (!group) {
        group = { relationType: relType, items: [] };
        relationsByEntityType[entityType].outgoing.push(group);
      }
      group.items.push({
        linkedEntity: target,
        properties: item.properties || {},
      });
    }
  }
  // Обработка входящих связей
  for (const [relType, items] of Object.entries(incomingRelations)) {
    for (const item of items as any[]) {
      const from = item.from;
      if (!from?.type) continue;
      const entityType = from.type;
      if (!relationsByEntityType[entityType]) {
        relationsByEntityType[entityType] = { outgoing: [], incoming: [] };
      }
      let group = relationsByEntityType[entityType].incoming.find(g => g.relationType === relType);
      if (!group) {
        group = { relationType: relType, items: [] };
        relationsByEntityType[entityType].incoming.push(group);
      }
      group.items.push({
        linkedEntity: from,
        properties: item.properties || {},
      });
    }
  }

  // Рендер таблицы для одного типа сущности (сворачиваемая)
  const renderRelationDetails = (entityType: string, data: EntityTypeRelations) => {
    const hasOutgoing = data.outgoing.length > 0;
    const hasIncoming = data.incoming.length > 0;
    if (!hasOutgoing && !hasIncoming) return null;

    const typeLabel = entityType.charAt(0).toUpperCase() + entityType.slice(1) + 's';

    return (
      <details key={entityType} className="relation-entity-details">
        <summary>
          <span className="entity-summary-title">{typeLabel}</span>
        </summary>
        <div className="relation-table-container">
          <table className="relation-table">
            <thead>
              <tr>
                <th>Direction</th>
                <th>Relation Type</th>
                <th>Linked Entity</th>
              </tr>
            </thead>
            <tbody>
              {hasOutgoing && (
                <>
                  {data.outgoing.map((group, idx) =>
                    group.items.map((item, itemIdx) => (
                      <tr key={`out-${entityType}-${group.relationType}-${itemIdx}`}>
                        {idx === 0 && itemIdx === 0 && (
                          <td rowSpan={data.outgoing.reduce((sum, g) => sum + g.items.length, 0)} className="direction-cell">
                            Outgoing
                          </td>
                        )}
                        <td>{group.relationType.replace(/_/g, ' ')}</td>
                        <td>
                          <Link to={`/entity/${item.linkedEntity.type}/${item.linkedEntity.slug}`}>
                            {item.linkedEntity.name}
                          </Link>
                          {Object.keys(item.properties).length > 0 && (
                            <span className="props">
                              &nbsp;({Object.entries(item.properties).map(([k, v]) => `${k}: ${v}`).join(', ')})
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </>
              )}
              {hasIncoming && (
                <>
                  {data.incoming.map((group, idx) =>
                    group.items.map((item, itemIdx) => (
                      <tr key={`in-${entityType}-${group.relationType}-${itemIdx}`}>
                        {idx === 0 && itemIdx === 0 && (
                          <td rowSpan={data.incoming.reduce((sum, g) => sum + g.items.length, 0)} className="direction-cell">
                            Incoming
                          </td>
                        )}
                        <td>{group.relationType.replace(/_/g, ' ')}</td>
                        <td>
                          <Link to={`/pages/${item.linkedEntity.slug}`}>
                            {item.linkedEntity.name}
                          </Link>
                          {Object.keys(item.properties).length > 0 && (
                            <span className="props">
                              &nbsp;({Object.entries(item.properties).map(([k, v]) => `${k}: ${v}`).join(', ')})
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </>
              )}
            </tbody>
          </table>
        </div>
      </details>
    );
  };

  return (
    <div className="entity-page">
      <div className="entity-two-columns">
        {/* Левая колонка */}
        <div className="entity-left">
          <div className="entity-left-header">
            <h1 className="entity-title">{mainName}</h1>
            <div className="entity-actions">
              <button className="icon-btn" title="Export"><MdOutlineFileDownload /></button>
              <button className="icon-btn" title="Import"><MdOutlineFileUpload /></button>
              <span className="entity-dates">Created: {created_at} | Updated: {updated_at}</span>
              {user?.role === 'admin' && (
                <button className="delete-btn" title="Delete" onClick={handleDelete}>Delete page</button>
              )}
            </div>
          </div>

          <div className="article-text">
            <p>{article.text || 'Description missing'}</p>
          </div>

          {/* Раскрывающиеся блоки для каждого типа сущности */}
          <div className="relations-grouped">
            {Object.entries(relationsByEntityType).map(([entityType, relData]) => renderRelationDetails(entityType, relData))}
            {Object.keys(relationsByEntityType).length === 0 && <p>No relations found.</p>}
          </div>

          <div className="comments-section">
            <h3>Comments</h3>
            <div className="comment-input">
              <input type="text" placeholder="Write a comment..." disabled />
              <button disabled>Send</button>
            </div>
            <div className="todo"><p>Комментарии появятся на следующей итерации</p></div>
          </div>
        </div>

        {/* Правая колонка без изменений */}
        <div className="entity-right">
          <div className="entity-right-actions">
            <button className={`like-btn ${liked ? 'liked' : ''}`} onClick={handleLike}>
              {liked ? <FaHeart /> : <FaRegHeart />} {likes_count}
            </button>
            {user?.role === 'admin' && (
              <button className="icon-btn" onClick={handleEditClick}><FaEdit /></button>
            )}
            <button className="icon-btn" disabled><SiRelay /></button>
          </div>
          <div className="entity-card">
            <img src={article.image_url || '/images/default-avatar.png'} alt={mainName} className="entity-image" />
            <div className="entity-attributes">
              <h3>{mainName}</h3>
              <table className="attr-table">
                <tbody>
                  {pageData.names && pageData.names.length > 0 && (
                    <tr><td className="attr-key">Names</td><td className="attr-value">{pageData.names.join(', ')}</td></tr>
                  )}
                  <tr><td className="attr-key">Type</td><td className="attr-value">{pageData.type}</td></tr>
                  {Object.entries(pageData.attributes || {})
                    .filter(([_, value]) => value != null && value !== '' && !(Array.isArray(value) && value.length === 0))
                    .map(([key, value]) => (
                      <tr key={key}>
                        <td className="attr-key">{key.replace(/_/g, ' ')}</td>
                        <td className="attr-value">{Array.isArray(value) ? value.join(', ') : value as string}</td>
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
          onClose={() => { setShowAuthModal(false); setPendingEdit(false); setPendingLike(false); }}
          onSuccess={() => setShowAuthModal(false)}
        />
      )}
      <div className="edit-page">
        {errorModalOpen && (
          <ErrorModal message={errorMessage} statusCode={errorStatusCode} onClose={() => setErrorModalOpen(false)} />
        )}
      </div>
    </div>
  );
};

export default EntityPage;