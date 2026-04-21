import React, { createContext, useContext, useEffect, useState } from 'react';
import { useLogin, useRegister, useGetMe, useUpdateMe, useLogout } from '../api/generated/auth/auth';
import type { MeResponse, UpdateMeRequest, AuthResponse } from '../api/generated/models';
import { useQueryClient } from '@tanstack/react-query';

interface AuthContextType {
  user: MeResponse | null;
  login: (username: string, password: string) => Promise<boolean>;
  register: (username: string, email: string, password: string) => Promise<boolean>;
  updateUser: (data: UpdateMeRequest) => Promise<boolean>;
  logout: () => Promise<void>;
  isLoading: boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<MeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Мутации
  const loginMutation = useLogin();
  const registerMutation = useRegister();
  const updateMeMutation = useUpdateMe();
  const logoutMutation = useLogout();

  // Запрос текущего пользователя (выполняется, только если есть токен)
  const { data: meData, refetch: refetchMe } = useGetMe({
    query: {
      enabled: false,
      retry: false,
    },
  });

  // При монтировании проверяем наличие токена и загружаем пользователя
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      refetchMe()
        .then(({ data }) => {
          if (data) {
            // Приводим User к MeResponse
            const meData = data as unknown as MeResponse;
            setUser(meData);
          }
      }).catch(() => {
        // Токен невалиден – удаляем его
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }).finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, [refetchMe]);

  // Обновляем пользователя, когда данные из useGetMe приходят
  useEffect(() => {
    if (meData) {
      const me = meData as unknown as MeResponse;
      setUser(me);
    }
  }, [meData]);

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const result = await loginMutation.mutateAsync({ data: { username, password } });
      const authResult = result as unknown as AuthResponse;
      const { user, tokens } = authResult;
      if (!tokens?.access) {
        console.error('No access token in login response', authResult);
        return false;
      }
      localStorage.setItem('access_token', tokens.access);
      localStorage.setItem('refresh_token', tokens.refresh);
      const meUser: MeResponse = {
        ...user,
        likedPages: [],
      };
      setUser(meUser);
      await refreshUser();
      return true;
    } catch (error: any) {
      console.error('Login failed:', error);
      const serverError = error.response?.data;
      let message = 'Incorrect username or password';
      if (serverError?.error?.message) {
        message = serverError.error.message;
      } else if (serverError?.message) {
        message = serverError.message;
      }
      throw new Error(message);
    }
  };

  const register = async (username: string, email: string, password: string): Promise<boolean> => {
    try {
      const result = await registerMutation.mutateAsync({ data: { username, email, password } });
      const authResult = result as unknown as AuthResponse;
      const { user, tokens } = authResult;
      if (!tokens?.access) {
        console.error('No access token in register response', authResult);
        return false;
      }
      localStorage.setItem('access_token', tokens.access);
      localStorage.setItem('refresh_token', tokens.refresh);
      const meUser: MeResponse = {
        ...user,
        likedPages: [],
      };
      setUser(meUser);
      await refreshUser();
      return true;
    } catch (error: any) {
      console.error('Registration failed:', error);
      const serverError = error.response?.data;
      let message = 'Registration failed';
      if (serverError?.error?.message) {
        message = serverError.error.message;
      } else if (serverError?.message) {
        message = serverError.message;
      }
      throw new Error(message);
    }
  };

  const updateUser = async (data: UpdateMeRequest): Promise<boolean> => {
    try {
      const result = await updateMeMutation.mutateAsync({ data });
      setUser(result as unknown as MeResponse);
      return true;
    } catch (error) {
      console.error('Update failed:', error);
      return false;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        await logoutMutation.mutateAsync({ data: { refresh: refreshToken } });
      }
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      queryClient.clear(); // очищаем кеш React Query
    }
  };

  const refreshUser = async () => {
    const result = await refetchMe();
    if (result.data) {
      setUser(result.data as unknown as MeResponse);
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, register, updateUser, logout, isLoading, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};