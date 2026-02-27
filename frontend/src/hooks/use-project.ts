import { create } from 'zustand'
import type { Project } from '@/lib/types'
import { api } from '@/lib/api'

interface ProjectState {
  projects: Project[]
  currentProject: Project | null
  isLoading: boolean
  loadProjects: () => Promise<void>
  setCurrentProject: (project: Project | null) => void
  createProject: (data: { name: string; domain: string; description?: string; business_type?: string }) => Promise<Project>
}

export const useProject = create<ProjectState>((set, get) => ({
  projects: [],
  currentProject: null,
  isLoading: false,

  loadProjects: async () => {
    set({ isLoading: true })
    try {
      const projects = await api.getProjects()
      const current = get().currentProject
      set({
        projects,
        currentProject: current && projects.find((p) => p.id === current.id) ? current : projects[0] || null,
        isLoading: false,
      })
    } catch {
      set({ isLoading: false })
    }
  },

  setCurrentProject: (project) => {
    set({ currentProject: project })
    if (project) {
      localStorage.setItem('current_project_id', project.id)
    } else {
      localStorage.removeItem('current_project_id')
    }
  },

  createProject: async (data) => {
    const project = await api.createProject(data)
    set((state) => ({
      projects: [...state.projects, project],
      currentProject: project,
    }))
    localStorage.setItem('current_project_id', project.id)
    return project
  },
}))
