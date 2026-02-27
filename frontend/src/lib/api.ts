const API_BASE = '/api/v1'

class ApiClient {
  private accessToken: string | null = null

  setToken(token: string | null) {
    this.accessToken = token
    if (token) {
      localStorage.setItem('access_token', token)
    } else {
      localStorage.removeItem('access_token')
    }
  }

  getToken(): string | null {
    if (!this.accessToken) {
      this.accessToken = localStorage.getItem('access_token')
    }
    return this.accessToken
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken()
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    })

    if (res.status === 401) {
      const refreshed = await this.tryRefresh()
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.accessToken}`
        const retry = await fetch(`${API_BASE}${path}`, { ...options, headers })
        if (!retry.ok) {
          const err = await retry.json().catch(() => ({ detail: 'Request failed' }))
          throw new ApiError(retry.status, err.detail || 'Request failed')
        }
        return retry.json()
      }
      this.clearAuth()
      window.location.href = '/login'
      throw new ApiError(401, 'Session expired')
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Request failed' }))
      throw new ApiError(res.status, err.detail || 'Request failed')
    }

    if (res.status === 204) return undefined as T
    return res.json()
  }

  private async tryRefresh(): Promise<boolean> {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) return false

    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
      if (!res.ok) return false
      const data = await res.json()
      this.setToken(data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      return true
    } catch {
      return false
    }
  }

  clearAuth() {
    this.accessToken = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  // Auth
  async register(email: string, password: string, full_name: string) {
    return this.request<{ access_token: string; refresh_token: string; token_type: string }>(
      '/auth/register',
      { method: 'POST', body: JSON.stringify({ email, password, full_name }) }
    )
  }

  async login(email: string, password: string) {
    return this.request<{ access_token: string; refresh_token: string; token_type: string }>(
      '/auth/login',
      { method: 'POST', body: JSON.stringify({ email, password }) }
    )
  }

  async getMe() {
    return this.request<import('./types').User>('/auth/me')
  }

  async updateMe(data: { full_name?: string; email?: string }) {
    return this.request<import('./types').User>('/auth/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  // Projects
  async getProjects() {
    return this.request<import('./types').Project[]>('/projects')
  }

  async createProject(data: { name: string; domain: string; description?: string; business_type?: string }) {
    return this.request<import('./types').Project>('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getProject(id: string) {
    return this.request<import('./types').Project>(`/projects/${id}`)
  }

  async updateProject(id: string, data: Partial<{ name: string; domain: string; description: string; business_type: string }>) {
    return this.request<import('./types').Project>(`/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteProject(id: string) {
    return this.request<void>(`/projects/${id}`, { method: 'DELETE' })
  }

  // Project Members
  async getProjectMembers(projectId: string) {
    return this.request<import('./types').ProjectMember[]>(`/projects/${projectId}/members`)
  }

  async addProjectMember(projectId: string, data: { user_id: string; role: string }) {
    return this.request<import('./types').ProjectMember>(`/projects/${projectId}/members`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Brand Persona
  async getBrandPersona(projectId: string) {
    return this.request<import('./types').BrandPersona>(`/projects/${projectId}/persona`)
  }

  async updateBrandPersona(projectId: string, data: Partial<import('./types').BrandPersona>) {
    return this.request<import('./types').BrandPersona>(`/projects/${projectId}/persona`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  // Project API Keys
  async getProjectApiKeys(projectId: string) {
    return this.request<import('./types').ProjectApiKey[]>(`/projects/${projectId}/api-keys`)
  }

  async upsertProjectApiKey(projectId: string, data: { provider: string; api_key: string; label?: string }) {
    return this.request<import('./types').ProjectApiKey>(`/projects/${projectId}/api-keys`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async deleteProjectApiKey(projectId: string, provider: string) {
    return this.request<void>(`/projects/${projectId}/api-keys/${provider}`, { method: 'DELETE' })
  }

  async testProjectApiKey(projectId: string, provider: string) {
    return this.request<{ ok: boolean; provider: string }>(
      `/projects/${projectId}/api-keys/${provider}/test`,
      { method: 'POST' }
    )
  }

  // Audits (Step 1)
  async getAudits(projectId: string) {
    return this.request<import('./types').SiteAudit[]>(`/audits?project_id=${projectId}`)
  }

  async createAudit(projectId: string, url: string) {
    return this.request<{ id: string; status: string }>('/audits', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, url }),
    })
  }

  async getAudit(auditId: string) {
    return this.request<import('./types').SiteAudit & { issues?: import('./types').AuditIssue[] }>(`/audits/${auditId}`)
  }

  async getAuditIssues(auditId: string) {
    return this.request<import('./types').AuditIssue[]>(`/audits/${auditId}/issues`)
  }

  // Keywords (Step 2)
  async getKeywordResearches(projectId: string) {
    return this.request<import('./types').KeywordResearch[]>(`/keywords?project_id=${projectId}`)
  }

  async createKeywordResearch(projectId: string, seedKeyword: string) {
    return this.request<{ id: string; status: string }>('/keywords', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, seed_keyword: seedKeyword }),
    })
  }

  async getKeywordResearch(researchId: string) {
    return this.request<import('./types').KeywordResearch & { keywords?: import('./types').Keyword[] }>(`/keywords/${researchId}`)
  }

  // Competitors (Step 3)
  async getCompetitorAnalyses(projectId: string) {
    return this.request<{ id: string; target_keyword: string; status: string; created_at: string }[]>(`/competitors?project_id=${projectId}`)
  }

  async createCompetitorAnalysis(projectId: string, targetKeyword: string, ownUrl?: string) {
    return this.request<{ id: string; status: string }>('/competitors', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, target_keyword: targetKeyword, own_url: ownUrl }),
    })
  }

  async getCompetitorAnalysis(analysisId: string) {
    return this.request<Record<string, unknown>>(`/competitors/${analysisId}`)
  }

  // Briefs (Step 4)
  async getBriefs(projectId: string) {
    return this.request<{ id: string; target_keyword: string; status: string; created_at: string }[]>(`/briefs?project_id=${projectId}`)
  }

  async createBrief(projectId: string, targetKeyword: string, llmProvider?: string) {
    return this.request<{ id: string; status: string }>('/briefs', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, target_keyword: targetKeyword, llm_provider: llmProvider || 'anthropic' }),
    })
  }

  async getBrief(briefId: string) {
    return this.request<import('./types').ContentBrief>(`/briefs/${briefId}`)
  }

  // Content / Write (Step 5)
  async getContentDrafts(projectId: string) {
    return this.request<import('./types').ContentDraft[]>(`/content?project_id=${projectId}`)
  }

  async createContentDraft(projectId: string, data: { keyword: string; brief_id?: string; provider?: string }) {
    return this.request<{ id: string; status: string }>('/content', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, ...data }),
    })
  }

  async getContentDraft(draftId: string) {
    return this.request<import('./types').ContentDraft>(`/content/${draftId}`)
  }

  async updateContentDraft(draftId: string, data: { body?: string; title?: string; content_html?: string; meta_title?: string; meta_description?: string }) {
    return this.request<import('./types').ContentDraft>(`/content/${draftId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  // Strategy
  async getPillars(projectId: string) {
    return this.request<import('./types').ContentPillar[]>(`/strategy/pillars?project_id=${projectId}`)
  }

  async createPillar(data: { project_id: string; name: string; description?: string; keywords?: string[]; color?: string }) {
    return this.request<import('./types').ContentPillar>('/strategy/pillars', { method: 'POST', body: JSON.stringify(data) })
  }

  async updatePillar(id: string, data: Partial<{ name: string; description: string; keywords: string[]; color: string }>) {
    return this.request<import('./types').ContentPillar>(`/strategy/pillars/${id}`, { method: 'PUT', body: JSON.stringify(data) })
  }

  async deletePillar(id: string) {
    return this.request<void>(`/strategy/pillars/${id}`, { method: 'DELETE' })
  }

  async getClusters(projectId: string, pillarId?: string) {
    const q = pillarId ? `&pillar_id=${pillarId}` : ''
    return this.request<import('./types').TopicCluster[]>(`/strategy/clusters?project_id=${projectId}${q}`)
  }

  async createCluster(data: { project_id: string; pillar_id: string; topic: string; subtopics?: string[]; priority?: string }) {
    return this.request<import('./types').TopicCluster>('/strategy/clusters', { method: 'POST', body: JSON.stringify(data) })
  }

  async deleteCluster(id: string) {
    return this.request<void>(`/strategy/clusters/${id}`, { method: 'DELETE' })
  }

  async getAiRecommendations(projectId: string) {
    return this.request<{ pillars: { name: string; description: string; topics: string[] }[] }>(`/strategy/ai-recommend?project_id=${projectId}`, { method: 'POST' })
  }

  // Past Articles
  async getPastArticles(projectId: string) {
    return this.request<import('./types').PastArticle[]>(`/past-articles?project_id=${projectId}`)
  }

  async importPastArticle(projectId: string, url: string) {
    return this.request<import('./types').PastArticle>('/past-articles/import', { method: 'POST', body: JSON.stringify({ project_id: projectId, url }) })
  }

  async deletePastArticle(id: string) {
    return this.request<void>(`/past-articles/${id}`, { method: 'DELETE' })
  }

  // Calendar
  async getCalendarItems(projectId: string, year?: number, month?: number) {
    const params = new URLSearchParams({ project_id: projectId })
    if (year) params.set('year', String(year))
    if (month) params.set('month', String(month))
    return this.request<import('./types').CalendarItem[]>(`/calendar?${params}`)
  }

  async createCalendarItem(data: Partial<import('./types').CalendarItem> & { project_id: string }) {
    return this.request<import('./types').CalendarItem>('/calendar/items', { method: 'POST', body: JSON.stringify(data) })
  }

  async updateCalendarItem(id: string, data: Partial<import('./types').CalendarItem>) {
    return this.request<import('./types').CalendarItem>(`/calendar/items/${id}`, { method: 'PUT', body: JSON.stringify(data) })
  }

  async deleteCalendarItem(id: string) {
    return this.request<void>(`/calendar/items/${id}`, { method: 'DELETE' })
  }

  async rescheduleCalendarItem(id: string, date: string) {
    return this.request<import('./types').CalendarItem>(`/calendar/items/${id}/reschedule`, { method: 'PUT', body: JSON.stringify({ scheduled_date: date }) })
  }

  // Publishing
  async getPublishingConnections(projectId: string) {
    return this.request<import('./types').PublishingConnection[]>(`/publishing/connections?project_id=${projectId}`)
  }

  async createPublishingConnection(data: { project_id: string; platform: string; site_url: string; username?: string; password?: string; token?: string }) {
    return this.request<import('./types').PublishingConnection>('/publishing/connections', { method: 'POST', body: JSON.stringify(data) })
  }

  async deletePublishingConnection(id: string) {
    return this.request<void>(`/publishing/connections/${id}`, { method: 'DELETE' })
  }

  async testPublishingConnection(id: string) {
    return this.request<{ success: boolean; message: string }>(`/publishing/connections/${id}/test`, { method: 'POST' })
  }

  async publishDraft(draftId: string, connectionId: string) {
    return this.request<import('./types').PublishLog>('/publishing/publish', { method: 'POST', body: JSON.stringify({ draft_id: draftId, connection_id: connectionId }) })
  }

  async getPublishHistory(draftId: string) {
    return this.request<import('./types').PublishLog[]>(`/publishing/history/${draftId}`)
  }

  // Optimization (Step 6)
  async analyzeContent(data: { content: string; keyword: string; project_id?: string }) {
    return this.request<Record<string, unknown>>('/optimization/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getOptimization(optimizationId: string) {
    return this.request<Record<string, unknown>>(`/optimization/${optimizationId}`)
  }

  // Tracking (Step 7)
  async checkRankings(projectId: string, keywords: string[]) {
    return this.request<Record<string, unknown>>('/tracking/rankings', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, keywords }),
    })
  }

  async checkCoreWebVitals(projectId: string, url: string) {
    return this.request<Record<string, unknown>>('/tracking/cwv', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, url }),
    })
  }

  async getRankHistory(projectId: string, keyword: string) {
    return this.request<Record<string, unknown>[]>(`/tracking/history?project_id=${projectId}&keyword=${encodeURIComponent(keyword)}`)
  }

  // Dashboard
  async getDashboardStats(projectId: string) {
    return this.request<{
      health_score: number | null
      keyword_count: number
      total_drafts: number
      published_drafts: number
      audit_count: number
      recent_audits: { id: string; url: string; status: string; health_score: number | null; created_at: string }[]
    }>(`/dashboard/stats?project_id=${projectId}`)
  }

  // LLM
  async getLLMProviders() {
    return this.request<{ providers: string[] }>('/llm/providers')
  }

  async chatLLM(data: { project_id: string; provider?: string; system_prompt?: string; user_prompt: string }) {
    return this.request<{ response: string; provider: string; model: string }>('/llm/chat', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // SSE helper for streaming endpoints
  streamSSE(path: string, onMessage: (data: unknown) => void, onDone?: () => void) {
    const token = this.getToken()
    const controller = new AbortController()

    fetch(`${API_BASE}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      signal: controller.signal,
    }).then(async (res) => {
      if (!res.ok || !res.body) return
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const raw = line.slice(6)
            if (raw === '[DONE]') {
              onDone?.()
              return
            }
            try {
              onMessage(JSON.parse(raw))
            } catch {
              onMessage(raw)
            }
          }
        }
      }
      onDone?.()
    })

    return () => controller.abort()
  }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

export const api = new ApiClient()
