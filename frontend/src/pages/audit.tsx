import { useState, useEffect } from 'react'
import { useProject } from '@/hooks/use-project'
import { api } from '@/lib/api'
import type { SiteAudit, AuditIssue } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Globe, Play, RefreshCw, AlertTriangle, AlertCircle, Info, CheckCircle2 } from 'lucide-react'

function ScoreGauge({ score }: { score: number }) {
  const color = score >= 80 ? 'text-green-500' : score >= 50 ? 'text-yellow-500' : 'text-red-500'
  const bg = score >= 80 ? 'bg-green-500/10' : score >= 50 ? 'bg-yellow-500/10' : 'bg-red-500/10'
  return (
    <div className={`flex flex-col items-center justify-center rounded-full h-36 w-36 ${bg}`}>
      <span className={`text-4xl font-bold ${color}`}>{score}</span>
      <span className="text-xs text-muted-foreground mt-1">/ 100</span>
    </div>
  )
}

const severityConfig = {
  critical: { icon: AlertCircle, color: 'text-red-600', bg: 'bg-red-50', badge: 'destructive' as const },
  warning: { icon: AlertTriangle, color: 'text-yellow-600', bg: 'bg-yellow-50', badge: 'secondary' as const },
  info: { icon: Info, color: 'text-blue-600', bg: 'bg-blue-50', badge: 'outline' as const },
  pass: { icon: CheckCircle2, color: 'text-green-600', bg: 'bg-green-50', badge: 'outline' as const },
}

export default function AuditPage() {
  const { currentProject } = useProject()
  const [url, setUrl] = useState('')
  const [audits, setAudits] = useState<SiteAudit[]>([])
  const [selectedAudit, setSelectedAudit] = useState<(SiteAudit & { issues?: AuditIssue[] }) | null>(null)
  const [issues, setIssues] = useState<AuditIssue[]>([])
  const [isRunning, setIsRunning] = useState(false)
  const [severityFilter, setSeverityFilter] = useState<string>('all')

  useEffect(() => {
    if (currentProject) {
      setUrl(currentProject.domain ? `https://${currentProject.domain}` : '')
      loadAudits()
    }
  }, [currentProject])

  async function loadAudits() {
    if (!currentProject) return
    try {
      const data = await api.getAudits(currentProject.id)
      setAudits(data)
    } catch { /* ignore */ }
  }

  async function runAudit() {
    if (!currentProject || !url) return
    setIsRunning(true)
    try {
      const { id } = await api.createAudit(currentProject.id, url)
      // Poll for completion
      const poll = setInterval(async () => {
        try {
          const audit = await api.getAudit(id)
          if (audit.status === 'completed' || audit.status === 'failed') {
            clearInterval(poll)
            setIsRunning(false)
            setSelectedAudit(audit)
            if (audit.status === 'completed') {
              const issueData = await api.getAuditIssues(id)
              setIssues(issueData)
            }
            loadAudits()
          }
        } catch {
          clearInterval(poll)
          setIsRunning(false)
        }
      }, 2000)
    } catch {
      setIsRunning(false)
    }
  }

  async function selectAudit(audit: SiteAudit) {
    try {
      const full = await api.getAudit(audit.id)
      setSelectedAudit(full)
      const issueData = await api.getAuditIssues(audit.id)
      setIssues(issueData)
    } catch { /* ignore */ }
  }

  const filteredIssues = severityFilter === 'all' ? issues : issues.filter((i) => i.severity === severityFilter)
  const issueCounts = {
    critical: issues.filter((i) => i.severity === 'critical').length,
    warning: issues.filter((i) => i.severity === 'warning').length,
    info: issues.filter((i) => i.severity === 'info').length,
    pass: issues.filter((i) => i.severity === 'pass').length,
  }

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Select a project to run audits</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Site Audit</h1>
        <p className="text-muted-foreground">Run a comprehensive SEO health check on any URL</p>
      </div>

      {/* Audit Launcher */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="pl-10"
                onKeyDown={(e) => e.key === 'Enter' && runAudit()}
              />
            </div>
            <Button onClick={runAudit} disabled={isRunning || !url} className="w-full sm:w-auto">
              {isRunning ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
              {isRunning ? 'Auditing...' : 'Run Audit'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        {/* Results */}
        <div className="space-y-4">
          {selectedAudit && (
            <>
              {/* Score Card */}
              <Card>
                <CardContent className="pt-6">
                  <div className="flex flex-col sm:flex-row items-center gap-6">
                    <ScoreGauge score={selectedAudit.health_score ?? 0} />
                    <div className="flex-1 space-y-2 text-center sm:text-left">
                      <h3 className="font-semibold text-lg">Health Score</h3>
                      <p className="text-sm text-muted-foreground">{selectedAudit.url}</p>
                      <div className="flex gap-2 flex-wrap">
                        <Badge variant="destructive">{issueCounts.critical} Critical</Badge>
                        <Badge variant="secondary">{issueCounts.warning} Warnings</Badge>
                        <Badge variant="outline">{issueCounts.info} Info</Badge>
                        <Badge variant="outline" className="border-green-300">{issueCounts.pass} Passed</Badge>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Issues */}
              <Card>
                <CardHeader>
                  <CardTitle>Issues</CardTitle>
                  <CardDescription>{issues.length} issues found</CardDescription>
                </CardHeader>
                <CardContent>
                  <Tabs value={severityFilter} onValueChange={setSeverityFilter}>
                    <TabsList>
                      <TabsTrigger value="all">All ({issues.length})</TabsTrigger>
                      <TabsTrigger value="critical">Critical ({issueCounts.critical})</TabsTrigger>
                      <TabsTrigger value="warning">Warning ({issueCounts.warning})</TabsTrigger>
                      <TabsTrigger value="info">Info ({issueCounts.info})</TabsTrigger>
                    </TabsList>
                    <TabsContent value={severityFilter} className="mt-4 space-y-3">
                      {filteredIssues.length === 0 ? (
                        <p className="text-sm text-muted-foreground py-4 text-center">No issues found</p>
                      ) : (
                        filteredIssues.map((issue) => {
                          const config = severityConfig[issue.severity]
                          const Icon = config.icon
                          return (
                            <div key={issue.id} className={`rounded-lg border p-4 ${config.bg}`}>
                              <div className="flex items-start gap-3">
                                <Icon className={`h-5 w-5 mt-0.5 ${config.color}`} />
                                <div className="flex-1 space-y-1">
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium text-sm">{issue.title}</span>
                                    <Badge variant={config.badge} className="text-[10px]">{issue.category}</Badge>
                                  </div>
                                  <p className="text-sm text-muted-foreground">{issue.description}</p>
                                  {issue.recommendation && (
                                    <p className="text-sm text-foreground/80 mt-2">
                                      <strong>Fix:</strong> {issue.recommendation}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          )
                        })
                      )}
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            </>
          )}

          {!selectedAudit && !isRunning && (
            <Card>
              <CardContent className="py-12 text-center">
                <Globe className="h-12 w-12 mx-auto text-muted-foreground/40 mb-4" />
                <h3 className="font-medium text-lg mb-1">No audit selected</h3>
                <p className="text-sm text-muted-foreground">Enter a URL above to run a site audit, or select a previous audit from the history</p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Audit History Sidebar */}
        <div className="space-y-3">
          <h3 className="font-semibold text-sm">Audit History</h3>
          {audits.length === 0 ? (
            <p className="text-sm text-muted-foreground">No audits yet</p>
          ) : (
            audits.map((audit) => (
              <Card
                key={audit.id}
                className={`cursor-pointer transition-colors hover:bg-accent ${selectedAudit?.id === audit.id ? 'ring-2 ring-primary' : ''}`}
                onClick={() => selectAudit(audit)}
              >
                <CardContent className="p-3">
                  <p className="text-sm font-medium truncate">{audit.url}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant={audit.status === 'completed' ? 'outline' : audit.status === 'failed' ? 'destructive' : 'secondary'} className="text-[10px]">
                      {audit.status}
                    </Badge>
                    {audit.health_score != null && (
                      <span className="text-xs text-muted-foreground">Score: {audit.health_score}</span>
                    )}
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-1">{new Date(audit.created_at).toLocaleDateString()}</p>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
