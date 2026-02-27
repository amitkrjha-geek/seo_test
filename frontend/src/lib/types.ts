export type UserRole = 'admin' | 'strategist' | 'writer' | 'client'

export interface User {
  id: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface Project {
  id: string
  name: string
  domain: string
  description: string | null
  business_type: string
  is_active: boolean
  owner_id: string
  created_at: string
  updated_at: string
}

export interface ProjectMember {
  id: string
  project_id: string
  user_id: string
  role: string
  user_email: string
  user_name: string
}

export interface BrandPersona {
  id: string
  project_id: string
  brand_name: string
  tagline: string
  voice_tone: string
  writing_style: string
  target_audience: string
  brand_values: string[]
  dos: string
  donts: string
  sample_content: string
  industry_keywords: string[]
}

export interface ProjectApiKey {
  id: string
  project_id: string
  provider: string
  label: string
  masked_key: string
  created_at: string
}

export interface SiteAudit {
  id: string
  project_id: string
  url: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  health_score: number | null
  results_json: Record<string, unknown> | null
  created_at: string
}

export interface AuditIssue {
  id: string
  audit_id: string
  category: string
  severity: 'critical' | 'warning' | 'info' | 'pass'
  title: string
  description: string
  recommendation: string
}

export interface KeywordResearch {
  id: string
  project_id: string
  seed_keyword: string
  status: string
  created_at: string
}

export interface Keyword {
  id: string
  research_id: string
  keyword: string
  source: string
  search_volume: number | null
  difficulty: number | null
  intent: string | null
  cluster: string | null
}

export interface ContentBrief {
  id: string
  project_id: string
  target_keyword: string
  content_type: string
  status: string
  outline: Record<string, unknown> | null
  serp_insights: Record<string, unknown> | null
  created_at: string
}

export interface ContentDraft {
  id: string
  project_id: string
  brief_id: string | null
  title: string
  body: string
  content_html: string
  target_keyword: string
  meta_title: string
  meta_description: string
  llm_provider: string
  seo_score: number | null
  word_count: number
  status: string
  created_at: string
  updated_at: string
}

// Strategy
export interface ContentPillar {
  id: string
  project_id: string
  name: string
  description: string
  keywords: string[]
  color: string
  created_at: string
}

export interface TopicCluster {
  id: string
  pillar_id: string
  project_id: string
  topic: string
  subtopics: string[]
  status: string
  priority: string
  created_at: string
}

// Past Articles
export interface PastArticle {
  id: string
  project_id: string
  url: string
  title: string
  word_count: number
  publish_date: string | null
  seo_score: number | null
  needs_refresh: boolean
  refresh_suggestions: string[]
  crawled_at: string
}

// Calendar
export type CalendarItemStatus = 'idea' | 'planned' | 'writing' | 'review' | 'scheduled' | 'published'

export interface CalendarItem {
  id: string
  project_id: string
  draft_id: string | null
  title: string
  target_keyword: string
  pillar_id: string | null
  scheduled_date: string | null
  status: CalendarItemStatus
  assignee_id: string | null
  notes: string
  color: string
  created_at: string
}

export interface RecurringSlot {
  id: string
  project_id: string
  day_of_week: number
  time: string
  pillar_id: string | null
  label: string
  is_active: boolean
}

// Publishing
export type PublishingPlatform = 'wordpress' | 'strapi'

export interface PublishingConnection {
  id: string
  project_id: string
  platform: PublishingPlatform
  site_url: string
  is_active: boolean
  last_synced_at: string | null
  created_at: string
}

export interface PublishLog {
  id: string
  draft_id: string
  connection_id: string
  platform: PublishingPlatform
  external_id: string
  external_url: string
  status: 'success' | 'failed'
  error_message: string
  published_at: string
}

export type PipelineStep = 1 | 2 | 3 | 4 | 5 | 6 | 7

export const PIPELINE_STEPS: { step: PipelineStep; label: string; description: string }[] = [
  { step: 1, label: 'Audit', description: 'Site health audit' },
  { step: 2, label: 'Keywords', description: 'Keyword research' },
  { step: 3, label: 'Competitors', description: 'Competitor analysis' },
  { step: 4, label: 'Brief', description: 'Content brief' },
  { step: 5, label: 'Write', description: 'AI content writing' },
  { step: 6, label: 'Optimize', description: 'Content optimization' },
  { step: 7, label: 'Track', description: 'Rank tracking' },
]
