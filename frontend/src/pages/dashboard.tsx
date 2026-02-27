import { useState, useEffect } from 'react'
import { useProject } from '@/hooks/use-project'
import { useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Plus, Globe, Search, Target, BookOpen, PenTool, Sparkles, TrendingUp, Activity,
  ArrowRight, HeartPulse, FileText, Radar, BarChart3,
} from 'lucide-react'
import { PIPELINE_STEPS } from '@/lib/types'

const stepIcons = [Globe, Search, Target, BookOpen, PenTool, Sparkles, TrendingUp]
const stepPaths = ['/', '/audit', '/keywords', '/competitors', '/brief', '/write', '/optimize', '/track']

interface DashboardStats {
  health_score: number | null
  keyword_count: number
  total_drafts: number
  published_drafts: number
  audit_count: number
  recent_audits: { id: string; url: string; status: string; health_score: number | null; created_at: string }[]
}

function StatCard({
  icon: Icon,
  label,
  value,
  subtitle,
  color = 'text-foreground',
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string | number
  subtitle: string
  color?: string
}) {
  return (
    <Card className="relative overflow-hidden">
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
            <p className={`text-3xl font-bold tracking-tight ${color}`}>{value}</p>
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
            <Icon className="h-5 w-5 text-muted-foreground" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  const { currentProject, projects } = useProject()
  const navigate = useNavigate()
  const [stats, setStats] = useState<DashboardStats | null>(null)

  useEffect(() => {
    if (currentProject) {
      api.getDashboardStats(currentProject.id).then(setStats).catch(() => {})
    }
  }, [currentProject])

  if (!currentProject) {
    return (
      <div className="flex flex-col items-center justify-center gap-6 py-20">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
          <Plus className="h-8 w-8 text-muted-foreground" />
        </div>
        <div className="text-center">
          <h2 className="text-2xl font-semibold">No project selected</h2>
          <p className="mt-2 text-muted-foreground">
            {projects.length === 0
              ? 'Create your first project to get started'
              : 'Select a project from the header dropdown'}
          </p>
        </div>
        {projects.length === 0 && (
          <Button onClick={() => navigate('/projects/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Create Project
          </Button>
        )}
      </div>
    )
  }

  const healthScore = stats?.health_score
  const healthColor =
    healthScore == null ? 'text-muted-foreground' :
    healthScore >= 70 ? 'text-green-600' :
    healthScore >= 50 ? 'text-yellow-600' : 'text-red-600'

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">{currentProject.name}</h1>
        <p className="text-muted-foreground">{currentProject.domain}</p>
      </div>

      {/* Stat Cards — consistent 4-column grid */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={HeartPulse}
          label="Health Score"
          value={healthScore ?? '--'}
          subtitle={healthScore != null ? 'From latest audit' : 'Run an audit'}
          color={healthColor}
        />
        <StatCard
          icon={Radar}
          label="Keywords"
          value={stats?.keyword_count ?? 0}
          subtitle="Tracked keywords"
        />
        <StatCard
          icon={FileText}
          label="Content"
          value={stats?.total_drafts ?? 0}
          subtitle={`${stats?.published_drafts ?? 0} published`}
        />
        <StatCard
          icon={BarChart3}
          label="Audits"
          value={stats?.audit_count ?? 0}
          subtitle="Total site audits"
        />
      </div>

      {/* SEO Pipeline — horizontal step flow */}
      <div>
        <h2 className="mb-4 text-lg font-semibold">SEO Pipeline</h2>
        <div className="grid gap-3 grid-cols-2 md:grid-cols-4 lg:grid-cols-7">
          {PIPELINE_STEPS.map((s, i) => {
            const Icon = stepIcons[i]
            return (
              <Card
                key={s.step}
                className="cursor-pointer transition-colors hover:bg-accent/50 group"
                onClick={() => navigate(stepPaths[s.step])}
              >
                <CardContent className="p-4 flex flex-col items-center text-center gap-2">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-muted group-hover:bg-primary/10 transition-colors">
                    <Icon className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-muted-foreground">Step {s.step}</p>
                    <p className="text-sm font-semibold">{s.label}</p>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Recent Audits */}
      {stats?.recent_audits && stats.recent_audits.length > 0 && (
        <div>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Activity className="h-4 w-4" /> Recent Audits
            </h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/audit')}>
              View all <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </div>
          <div className="space-y-2">
            {stats.recent_audits.map((a) => (
              <Card key={a.id} className="cursor-pointer hover:bg-accent/50 transition-colors" onClick={() => navigate('/audit')}>
                <CardContent className="py-3 px-4">
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-0">
                      <Globe className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <span className="text-sm font-medium truncate">{a.url}</span>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      {a.health_score != null && (
                        <span className={`text-sm font-bold tabular-nums ${a.health_score >= 70 ? 'text-green-600' : a.health_score >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                          {a.health_score}
                        </span>
                      )}
                      <Badge variant={a.status === 'completed' ? 'outline' : 'secondary'} className="text-[10px]">
                        {a.status}
                      </Badge>
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {new Date(a.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
