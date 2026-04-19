export const getLikes = (username: string): string[] => {
  const key = `likes_${username}`;
  const stored = localStorage.getItem(key);
  return stored ? JSON.parse(stored) : [];
};

export const addLike = (username: string, entitySlug: string): void => {
  const likes = getLikes(username);
  if (!likes.includes(entitySlug)) {
    likes.push(entitySlug);
    localStorage.setItem(`likes_${username}`, JSON.stringify(likes));
  }
};

export const removeLike = (username: string, entitySlug: string): void => {
  const likes = getLikes(username);
  const updated = likes.filter(slug => slug !== entitySlug);
  localStorage.setItem(`likes_${username}`, JSON.stringify(updated));
};

export const isLiked = (username: string, entitySlug: string): boolean => {
  return getLikes(username).includes(entitySlug);
};