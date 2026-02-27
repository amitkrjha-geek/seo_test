import { useState, useEffect } from 'react'
import { useProject } from '@/hooks/use-project'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { TrendingUp, RefreshCw, Globe, Plus, X, Gauge, Clock, MousePointerClick, ArrowUp, ArrowDown, Minus } from 'lucide-react'

interface RankingResult {
  keyword: string
  position: number | null
  url: string | null
  previous_position?: number | null
}

interface CWVResult {
  lcp: number | null
  inp: number | null
  cls: number | null
  fcp: number | null
  ttfb: number | null
  performance_score: number | null
}

export default function TrackPage() {
  const { currentProject } = useProject()
  const [url, setUrl] = useState('')
  const [keywordInput, setKeywordInput] = useState('')
  const [trackedKeywords, setTrackedKeywords] = useState<string[]>([])
  const [rankings, setRankings] = useState<RankingResult[]>([])
  const [cwv, setCwv] = useState<CWVResult | null>(null)
  const [isCheckingRanks, setIsCheckingRanks] = useState(false)
  const [isCheckingCWV, setIsCheckingCWV] = useState(false)

  useEffect(() => {
    if (currentProject) {
      setUrl(currentProject.domain ? `https://${currentProject.domain}` : '')
    }
  }, [currentProject])

  function addKeyword() {
    const kw = keywordInput.trim()
    if (kw && !trackedKeywords.includes(kw)) {
      setTrackedKeywords([...trackedKeywords, kw])
      setKeywordInput('')
    }
  }

  function removeKeyword(kw: string) {
    setTrackedKeywords(trackedKeywords.filter((k) => k !== kw))
  }

  async function checkRankings() {
    if (!currentProject || trackedKeywords.length === 0) return
    setIsCheckingRanks(true)
    try {
      const data = await api.checkRankings(currentProject.id, trackedKeywords)
      setRankings((data as { rankings?: RankingResult[] }).rankings || [])
    } catch { /* ignore */ }
    setIsCheckingRanks(false)
  }

  async function checkCWV() {
    if (!currentProject || !url) return
    setIsCheckingCWV(true)
    try {
      const data = await api.checkCoreWebVitals(currentProject.id, url)
      setCwv(data as unknown as CWVResult)
    } catch { /* ignore */ }
    setIsCheckingCWV(false)
  }

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Select a project to track rankings</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Rank Tracking</h1>
        <p className="text-muted-foreground">Monitor keyword rankings and Core Web Vitals</p>
      </div>

      <Tabs defaultValue="rankings">
        <TabsList>
          <TabsTrigger value="rankings">Rankings</TabsTrigger>
          <TabsTrigger value="cwv">Core Web Vitals</TabsTrigger>
        </TabsList>

        {/* Rankings Tab */}
        <TabsContent value="rankings" className="mt-4 space-y-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col sm:flex-row gap-3">
                <Input
                  placeholder="Add a keyword to track..."
                  value={keywordInput}
                  onChange={(e) => setKeywordInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addKeyword()}
                  className="flex-1"
                />
                <div className="flex gap-3">
                  <Button variant="outline" onClick={addKeyword} disabled={!keywordInput.trim()} className="flex-1 sm:flex-none">
                    <Plus className="h-4 w-4 mr-1" /> Add
                  </Button>
                  <Button onClick={checkRankings} disabled={isCheckingRanks || trackedKeywords.length === 0} className="flex-1 sm:flex-none">
                    {isCheckingRanks ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <TrendingUp className="h-4 w-4 mr-2" />}
                    <span className="hidden sm:inline">Check Rankings</span>
                    <span className="sm:hidden">Check</span>
                  </Button>
                </div>
              </div>

              {trackedKeywords.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {trackedKeywords.map((kw) => (
                    <Badge key={kw} variant="secondary" className="gap-1">
                      {kw}
                      <button onClick={() => removeKeyword(kw)} className="ml-1 hover:text-destructive">
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {rankings.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Rankings</CardTitle>
                <CardDescription>Current positions for tracked keywords</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border overflow-x-auto">
                  <table className="w-full text-sm min-w-[500px]">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="px-3 py-2 text-left font-medium text-muted-foreground">Keyword</th>
                        <th className="px-3 py-2 text-left font-medium text-muted-foreground">Position</th>
                        <th className="px-3 py-2 text-left font-medium text-muted-foreground">Change</th>
                        <th className="px-3 py-2 text-left font-medium text-muted-foreground">URL</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rankings.map((r, idx) => {
                        const change = r.previous_position != null && r.position != null
                          ? r.previous_position - r.position
                          : null
                        return (
                          <tr key={idx} className="border-b last:border-0 hover:bg-muted/30">
                            <td className="px-3 py-2 font-medium">{r.keyword}</td>
                            <td className="px-3 py-2">
                              {r.position != null ? (
                                <span className={r.position <= 3 ? 'text-green-600 font-bold' : r.position <= 10 ? 'text-green-600' : r.position <= 20 ? 'text-yellow-600' : 'text-muted-foreground'}>
                                  #{r.position}
                                </span>
                              ) : (
                                <span className="text-muted-foreground">Not ranked</span>
                              )}
                            </td>
                            <td className="px-3 py-2">
                              {change != null ? (
                                <span className={`flex items-center gap-1 ${change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-muted-foreground'}`}>
                                  {change > 0 ? <ArrowUp className="h-3 w-3" /> : change < 0 ? <ArrowDown className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
                                  {Math.abs(change)}
                                </span>
                              ) : (
                                <span className="text-muted-foreground">-</span>
                              )}
                            </td>
                            <td className="px-3 py-2 text-xs text-muted-foreground truncate max-w-[200px]">{r.url || '-'}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Core Web Vitals Tab */}
        <TabsContent value="cwv" className="mt-4 space-y-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex gap-3">
                <div className="relative flex-1">
                  <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="https://example.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Button onClick={checkCWV} disabled={isCheckingCWV || !url}>
                  {isCheckingCWV ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Gauge className="h-4 w-4 mr-2" />}
                  Check CWV
                </Button>
              </div>
            </CardContent>
          </Card>

          {cwv && (
            <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
              <CWVCard
                label="Largest Contentful Paint"
                value={cwv.lcp}
                unit="s"
                icon={<Clock className="h-4 w-4" />}
                good={2.5}
                poor={4.0}
              />
              <CWVCard
                label="Interaction to Next Paint"
                value={cwv.inp}
                unit="ms"
                icon={<MousePointerClick className="h-4 w-4" />}
                good={200}
                poor={500}
              />
              <CWVCard
                label="Cumulative Layout Shift"
                value={cwv.cls}
                unit=""
                icon={<ArrowUp className="h-4 w-4" />}
                good={0.1}
                poor={0.25}
              />
              {cwv.fcp != null && (
                <CWVCard label="First Contentful Paint" value={cwv.fcp} unit="s" icon={<Clock className="h-4 w-4" />} good={1.8} poor={3.0} />
              )}
              {cwv.ttfb != null && (
                <CWVCard label="Time to First Byte" value={cwv.ttfb} unit="ms" icon={<Clock className="h-4 w-4" />} good={800} poor={1800} />
              )}
              {cwv.performance_score != null && (
                <Card>
                  <CardContent className="pt-6 text-center">
                    <Gauge className="h-5 w-5 mx-auto text-muted-foreground mb-2" />
                    <p className="text-xs text-muted-foreground mb-1">Performance Score</p>
                    <p className={`text-3xl font-bold ${cwv.performance_score >= 90 ? 'text-green-600' : cwv.performance_score >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {cwv.performance_score}
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

function CWVCard({ label, value, unit, icon, good, poor }: {
  label: string; value: number | null; unit: string; icon: React.ReactNode; good: number; poor: number
}) {
  if (value == null) return null
  const status = value <= good ? 'good' : value <= poor ? 'needs-improvement' : 'poor'
  const color = status === 'good' ? 'text-green-600' : status === 'needs-improvement' ? 'text-yellow-600' : 'text-red-600'
  const bg = status === 'good' ? 'bg-green-500/10' : status === 'needs-improvement' ? 'bg-yellow-500/10' : 'bg-red-500/10'

  return (
    <Card>
      <CardContent className="pt-6 text-center">
        <div className="flex items-center justify-center gap-1.5 text-muted-foreground mb-2">{icon}<span className="text-xs">{label}</span></div>
        <div className={`inline-flex items-baseline gap-1 rounded-full px-4 py-2 ${bg}`}>
          <span className={`text-2xl font-bold ${color}`}>{typeof value === 'number' ? value.toFixed(value < 1 ? 3 : 1) : value}</span>
          <span className="text-xs text-muted-foreground">{unit}</span>
        </div>
        <p className="text-xs mt-2">
          <Badge variant={status === 'good' ? 'outline' : status === 'needs-improvement' ? 'secondary' : 'destructive'} className="text-[10px]">
            {status === 'good' ? 'Good' : status === 'needs-improvement' ? 'Needs Improvement' : 'Poor'}
          </Badge>
        </p>
      </CardContent>
    </Card>
  )
}
