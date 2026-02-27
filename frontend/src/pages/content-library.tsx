import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProject } from '@/hooks/use-project'
import { api } from '@/lib/api'
import type { ContentDraft } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { FileText, Search, PenTool, Clock, BarChart3 } from 'lucide-react'

const statusColors: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  draft: 'secondary',
  writing: 'secondary',
  review: 'default',
  approved: 'outline',
  published: 'outline',
  failed: 'destructive',
}

export default function ContentLibraryPage() {
  const { currentProject } = useProject()
  const navigate = useNavigate()
  const [drafts, setDrafts] = useState<ContentDraft[]>([])
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  useEffect(() => {
    if (currentProject) loadDrafts()
  }, [currentProject])

  async function loadDrafts() {
    if (!currentProject) return
    try {
      const data = await api.getContentDrafts(currentProject.id)
      setDrafts(data)
    } catch { /* ignore */ }
  }

  let filtered = drafts
  if (search) filtered = filtered.filter((d) => d.title.toLowerCase().includes(search.toLowerCase()))
  if (statusFilter !== 'all') filtered = filtered.filter((d) => d.status === statusFilter)

  const statuses = [...new Set(drafts.map((d) => d.status))]

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Select a project to view content</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Content Library</h1>
          <p className="text-muted-foreground">All content drafts for {currentProject.name}</p>
        </div>
        <Button onClick={() => navigate('/write')} className="w-full sm:w-auto">
          <PenTool className="h-4 w-4 mr-2" /> New Content
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-2xl font-bold">{drafts.length}</p>
                <p className="text-xs text-muted-foreground">Total Drafts</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Clock className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-2xl font-bold">{drafts.filter((d) => d.status === 'draft' || d.status === 'writing').length}</p>
                <p className="text-xs text-muted-foreground">In Progress</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <BarChart3 className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-2xl font-bold">{drafts.filter((d) => d.status === 'published').length}</p>
                <p className="text-xs text-muted-foreground">Published</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <BarChart3 className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-2xl font-bold">
                  {drafts.length > 0 ? Math.round(drafts.reduce((sum, d) => sum + (d.seo_score || 0), 0) / drafts.length) : 0}
                </p>
                <p className="text-xs text-muted-foreground">Avg SEO Score</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 sm:max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search content..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10" />
        </div>
        <select className="border rounded-md px-3 py-2 text-sm bg-background" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">All statuses</option>
          {statuses.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {/* Content List */}
      {filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="h-12 w-12 mx-auto text-muted-foreground/40 mb-4" />
            <h3 className="font-medium text-lg mb-1">No content yet</h3>
            <p className="text-sm text-muted-foreground mb-4">Create your first piece of content using the AI writer</p>
            <Button onClick={() => navigate('/write')}>
              <PenTool className="h-4 w-4 mr-2" /> Write Content
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((draft) => (
            <Card key={draft.id} className="cursor-pointer hover:bg-accent/50 transition-colors" onClick={() => navigate('/write')}>
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 min-w-0">
                    <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                    <div className="min-w-0">
                      <h3 className="font-medium text-sm truncate">{draft.title || 'Untitled'}</h3>
                      <p className="text-xs text-muted-foreground">
                        {draft.llm_provider} · {new Date(draft.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    {draft.seo_score != null && (
                      <span className={`text-sm font-medium ${draft.seo_score >= 70 ? 'text-green-600' : draft.seo_score >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {draft.seo_score}/100
                      </span>
                    )}
                    <Badge variant={statusColors[draft.status] || 'secondary'} className="text-[10px]">
                      {draft.status}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
