import { create } from 'zustand'
import type { User } from '@/lib/types'
import { api } from '@/lib/api'

interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, full_name: string) => Promise<void>
  logout: () => void
  loadUser: () => Promise<void>
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email, password) => {
    const res = await api.login(email, password)
    api.setToken(res.access_token)
    localStorage.setItem('refresh_token', res.refresh_token)
    const user = await api.getMe()
    set({ user, isAuthenticated: true, isLoading: false })
  },

  register: async (email, password, full_name) => {
    const res = await api.register(email, password, full_name)
    api.setToken(res.access_token)
    localStorage.setItem('refresh_token', res.refresh_token)
    const user = await api.getMe()
    set({ user, isAuthenticated: true, isLoading: false })
  },

  logout: () => {
    api.clearAuth()
    set({ user: null, isAuthenticated: false, isLoading: false })
  },

  loadUser: async () => {
    try {
      if (!api.getToken()) {
        set({ isLoading: false })
        return
      }
      const user = await api.getMe()
      set({ user, isAuthenticated: true, isLoading: false })
    } catch {
      api.clearAuth()
      set({ user: null, isAuthenticated: false, isLoading: false })
    }
  },
}))
