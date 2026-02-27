import { useState, useEffect } from 'react'
import { useProject } from '@/hooks/use-project'
import { api } from '@/lib/api'
import type { SiteAudit } from '@/lib/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { BarChart3, TrendingUp, FileText, Globe, Search, Target, Sparkles } from 'lucide-react'

interface PipelineStats {
  audits: number
  keywords: number
  competitors: number
  briefs: number
  drafts: number
  published: number
  latestAuditScore: number | null
}

export default function ReportsPage() {
  const { currentProject } = useProject()
  const [stats, setStats] = useState<PipelineStats>({
    audits: 0, keywords: 0, competitors: 0, briefs: 0, drafts: 0, published: 0, latestAuditScore: null,
  })
  const [audits, setAudits] = useState<SiteAudit[]>([])

  useEffect(() => {
    if (currentProject) loadStats()
  }, [currentProject])

  async function loadStats() {
    if (!currentProject) return
    try {
      const [auditData, kwData, compData, briefData, contentData] = await Promise.allSettled([
        api.getAudits(currentProject.id),
        api.getKeywordResearches(currentProject.id),
        api.getCompetitorAnalyses(currentProject.id),
        api.getBriefs(currentProject.id),
        api.getContentDrafts(currentProject.id),
      ])

      const auditList = auditData.status === 'fulfilled' ? auditData.value : []
      const kwList = kwData.status === 'fulfilled' ? kwData.value : []
      const compList = compData.status === 'fulfilled' ? compData.value : []
      const briefList = briefData.status === 'fulfilled' ? briefData.value : []
      const contentList = contentData.status === 'fulfilled' ? contentData.value : []

      setAudits(auditList)
      setStats({
        audits: auditList.length,
        keywords: kwList.length,
        competitors: compList.length,
        briefs: briefList.length,
        drafts: contentList.length,
        published: contentList.filter((d: { status: string }) => d.status === 'published').length,
        latestAuditScore: auditList.length > 0 ? auditList[0].health_score : null,
      })
    } catch { /* ignore */ }
  }

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Select a project to view reports</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Reports</h1>
        <p className="text-muted-foreground">Pipeline overview and analytics for {currentProject.name}</p>
      </div>

      {/* Pipeline Overview */}
      <div className="grid gap-4 grid-cols-2 sm:grid-cols-4 lg:grid-cols-7">
        <StatCard icon={Globe} label="Audits" value={stats.audits} />
        <StatCard icon={Search} label="Keywords" value={stats.keywords} />
        <StatCard icon={Target} label="Competitors" value={stats.competitors} />
        <StatCard icon={FileText} label="Briefs" value={stats.briefs} />
        <StatCard icon={Sparkles} label="Drafts" value={stats.drafts} />
        <StatCard icon={TrendingUp} label="Published" value={stats.published} />
        <Card>
          <CardContent className="pt-6 text-center">
            <BarChart3 className="h-5 w-5 mx-auto text-muted-foreground mb-1" />
            <p className="text-2xl font-bold">{stats.latestAuditScore ?? '--'}</p>
            <p className="text-[10px] text-muted-foreground">Health Score</p>
          </CardContent>
        </Card>
      </div>

      {/* Pipeline Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Progress</CardTitle>
          <CardDescription>Track your SEO workflow completion</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { step: 1, label: 'Site Audit', done: stats.audits > 0, count: stats.audits },
              { step: 2, label: 'Keyword Research', done: stats.keywords > 0, count: stats.keywords },
              { step: 3, label: 'Competitor Analysis', done: stats.competitors > 0, count: stats.competitors },
              { step: 4, label: 'Content Brief', done: stats.briefs > 0, count: stats.briefs },
              { step: 5, label: 'Content Writing', done: stats.drafts > 0, count: stats.drafts },
              { step: 6, label: 'Optimization', done: false, count: 0 },
              { step: 7, label: 'Rank Tracking', done: false, count: 0 },
            ].map((item) => (
              <div key={item.step} className="flex items-center gap-4">
                <span className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${
                  item.done ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                }`}>
                  {item.step}
                </span>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{item.label}</span>
                    <span className="text-xs text-muted-foreground">{item.count} {item.count === 1 ? 'run' : 'runs'}</span>
                  </div>
                  <div className="mt-1 h-1.5 rounded-full bg-muted overflow-hidden">
                    <div className={`h-full rounded-full transition-all ${item.done ? 'bg-primary w-full' : 'w-0'}`} />
                  </div>
                </div>
                {item.done && <Badge variant="outline" className="text-[10px] text-green-600 border-green-300">Done</Badge>}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Audits */}
      {audits.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Audits</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {audits.slice(0, 5).map((audit) => (
                <div key={audit.id} className="flex items-center justify-between rounded-lg border p-3">
                  <div>
                    <p className="text-sm font-medium">{audit.url}</p>
                    <p className="text-xs text-muted-foreground">{new Date(audit.created_at).toLocaleDateString()}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {audit.health_score != null && (
                      <span className={`text-lg font-bold ${audit.health_score >= 80 ? 'text-green-600' : audit.health_score >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {audit.health_score}
                      </span>
                    )}
                    <Badge variant={audit.status === 'completed' ? 'outline' : 'secondary'} className="text-[10px]">
                      {audit.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function StatCard({ icon: Icon, label, value }: { icon: React.ComponentType<{ className?: string }>; label: string; value: number }) {
  return (
    <Card>
      <CardContent className="pt-6 text-center">
        <Icon className="h-5 w-5 mx-auto text-muted-foreground mb-1" />
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-[10px] text-muted-foreground">{label}</p>
      </CardContent>
    </Card>
  )
}
