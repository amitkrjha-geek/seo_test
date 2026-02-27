import { useState, useEffect } from 'react'
import { useProject } from '@/hooks/use-project'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Target, Play, RefreshCw, ExternalLink } from 'lucide-react'

interface CompetitorAnalysis {
  id: string
  target_keyword: string
  status: string
  created_at: string
}

interface CompetitorDetail {
  id: string
  target_keyword: string
  status: string
  gap_data: Record<string, unknown> | null
  pages: { id: string; url: string; title: string; snippet: string; position: number; word_count: number }[]
}

export default function CompetitorsPage() {
  const { currentProject } = useProject()
  const [keyword, setKeyword] = useState('')
  const [ownUrl, setOwnUrl] = useState('')
  const [analyses, setAnalyses] = useState<CompetitorAnalysis[]>([])
  const [selected, setSelected] = useState<CompetitorDetail | null>(null)
  const [isRunning, setIsRunning] = useState(false)

  useEffect(() => {
    if (currentProject) {
      setOwnUrl(currentProject.domain ? `https://${currentProject.domain}` : '')
      loadAnalyses()
    }
  }, [currentProject])

  async function loadAnalyses() {
    if (!currentProject) return
    try {
      const data = await api.getCompetitorAnalyses(currentProject.id)
      setAnalyses(data)
    } catch { /* ignore */ }
  }

  async function startAnalysis() {
    if (!currentProject || !keyword) return
    setIsRunning(true)
    try {
      const { id } = await api.createCompetitorAnalysis(currentProject.id, keyword, ownUrl || undefined)
      const poll = setInterval(async () => {
        try {
          const result = await api.getCompetitorAnalysis(id)
          if ((result as Record<string, unknown>).status === 'completed' || (result as Record<string, unknown>).status === 'failed') {
            clearInterval(poll)
            setIsRunning(false)
            setSelected(result as unknown as CompetitorDetail)
            loadAnalyses()
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

  async function selectAnalysis(a: CompetitorAnalysis) {
    try {
      const result = await api.getCompetitorAnalysis(a.id)
      setSelected(result as unknown as CompetitorDetail)
    } catch { /* ignore */ }
  }

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Select a project to analyze competitors</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Competitor Analysis</h1>
        <p className="text-muted-foreground">Analyze SERP competitors and identify content gaps</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Target className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Target keyword..."
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                className="pl-10"
              />
            </div>
            <Input
              placeholder="Your URL (optional)"
              value={ownUrl}
              onChange={(e) => setOwnUrl(e.target.value)}
              className="sm:max-w-[200px]"
            />
            <Button onClick={startAnalysis} disabled={isRunning || !keyword} className="w-full sm:w-auto">
              {isRunning ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
              {isRunning ? 'Analyzing...' : 'Analyze'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-[1fr_260px]">
        <div className="space-y-4 min-w-0">
          {selected && (
            <>
              {/* Gap Analysis */}
              {selected.gap_data && (
                <Card>
                  <CardHeader>
                    <CardTitle>Content Gap Analysis</CardTitle>
                    <CardDescription>Opportunities based on competitor comparison for "{selected.target_keyword}"</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4 md:grid-cols-3">
                      {Object.entries(selected.gap_data).map(([key, value]) => (
                        <div key={key} className="rounded-lg border p-3">
                          <p className="text-xs text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</p>
                          <p className="font-medium text-sm mt-1">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* SERP Results */}
              <Card>
                <CardHeader>
                  <CardTitle>SERP Competitors</CardTitle>
                  <CardDescription>{selected.pages?.length || 0} pages analyzed</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {(selected.pages || []).map((page, idx) => (
                      <div key={page.id} className="rounded-lg border p-4 hover:bg-muted/30 transition-colors">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold">
                                {page.position || idx + 1}
                              </span>
                              <h4 className="font-medium text-sm truncate">{page.title || page.url}</h4>
                            </div>
                            <a href={page.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline flex items-center gap-1 truncate">
                              {page.url}
                              <ExternalLink className="h-3 w-3 flex-shrink-0" />
                            </a>
                            {page.snippet && <p className="text-sm text-muted-foreground mt-2">{page.snippet}</p>}
                          </div>
                          <div className="text-right flex-shrink-0">
                            {page.word_count > 0 && (
                              <Badge variant="outline" className="text-[10px]">{page.word_count.toLocaleString()} words</Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          )}

          {!selected && !isRunning && (
            <Card>
              <CardContent className="py-12 text-center">
                <Target className="h-12 w-12 mx-auto text-muted-foreground/40 mb-4" />
                <h3 className="font-medium text-lg mb-1">No analysis selected</h3>
                <p className="text-sm text-muted-foreground">Enter a keyword to analyze competitors, or select from history</p>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-3">
          <h3 className="font-semibold text-sm">Analysis History</h3>
          {analyses.length === 0 ? (
            <p className="text-sm text-muted-foreground">No analyses yet</p>
          ) : (
            analyses.map((a) => (
              <Card
                key={a.id}
                className={`cursor-pointer transition-colors hover:bg-accent ${selected?.id === a.id ? 'ring-2 ring-primary' : ''}`}
                onClick={() => selectAnalysis(a)}
              >
                <CardContent className="p-3">
                  <p className="text-sm font-medium">{a.target_keyword}</p>
                  <Badge variant={a.status === 'completed' ? 'outline' : 'secondary'} className="text-[10px] mt-1">{a.status}</Badge>
                  <p className="text-[10px] text-muted-foreground mt-1">{new Date(a.created_at).toLocaleDateString()}</p>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
