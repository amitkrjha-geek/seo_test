import { useState, useEffect } from 'react'
import { useProject } from '@/hooks/use-project'
import { api } from '@/lib/api'
import type { KeywordResearch, Keyword } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Search, Play, RefreshCw, ArrowUpDown } from 'lucide-react'

type SortKey = 'keyword' | 'source' | 'search_volume' | 'difficulty' | 'intent'

export default function KeywordsPage() {
  const { currentProject } = useProject()
  const [seedKeyword, setSeedKeyword] = useState('')
  const [researches, setResearches] = useState<KeywordResearch[]>([])
  const [selectedResearch, setSelectedResearch] = useState<KeywordResearch | null>(null)
  const [keywords, setKeywords] = useState<Keyword[]>([])
  const [isRunning, setIsRunning] = useState(false)
  const [clusterFilter, setClusterFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [sortKey, setSortKey] = useState<SortKey>('keyword')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  useEffect(() => {
    if (currentProject) loadResearches()
  }, [currentProject])

  async function loadResearches() {
    if (!currentProject) return
    try {
      const data = await api.getKeywordResearches(currentProject.id)
      setResearches(data)
    } catch { /* ignore */ }
  }

  async function startResearch() {
    if (!currentProject || !seedKeyword) return
    setIsRunning(true)
    try {
      const { id } = await api.createKeywordResearch(currentProject.id, seedKeyword)
      const poll = setInterval(async () => {
        try {
          const research = await api.getKeywordResearch(id)
          if (research.status === 'completed' || research.status === 'failed') {
            clearInterval(poll)
            setIsRunning(false)
            setSelectedResearch(research)
            setKeywords(research.keywords || [])
            loadResearches()
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

  async function selectResearch(r: KeywordResearch) {
    try {
      const full = await api.getKeywordResearch(r.id)
      setSelectedResearch(full)
      setKeywords((full as KeywordResearch & { keywords?: Keyword[] }).keywords || [])
    } catch { /* ignore */ }
  }

  const clusters = [...new Set(keywords.map((k) => k.cluster).filter(Boolean))] as string[]
  const sources = [...new Set(keywords.map((k) => k.source).filter(Boolean))] as string[]

  let filteredKeywords = keywords
  if (clusterFilter !== 'all') filteredKeywords = filteredKeywords.filter((k) => k.cluster === clusterFilter)
  if (sourceFilter !== 'all') filteredKeywords = filteredKeywords.filter((k) => k.source === sourceFilter)

  filteredKeywords = [...filteredKeywords].sort((a, b) => {
    const aVal = a[sortKey] ?? ''
    const bVal = b[sortKey] ?? ''
    if (typeof aVal === 'number' && typeof bVal === 'number') return sortDir === 'asc' ? aVal - bVal : bVal - aVal
    return sortDir === 'asc' ? String(aVal).localeCompare(String(bVal)) : String(bVal).localeCompare(String(aVal))
  })

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Select a project to research keywords</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Keyword Research</h1>
        <p className="text-muted-foreground">Discover keywords from Google Autocomplete, Serper, and Trends</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Enter a seed keyword..."
                value={seedKeyword}
                onChange={(e) => setSeedKeyword(e.target.value)}
                className="pl-10"
                onKeyDown={(e) => e.key === 'Enter' && startResearch()}
              />
            </div>
            <Button onClick={startResearch} disabled={isRunning || !seedKeyword} className="w-full sm:w-auto">
              {isRunning ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
              {isRunning ? 'Researching...' : 'Research'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-[1fr_260px]">
        <div className="space-y-4">
          {selectedResearch && keywords.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Keywords for "{selectedResearch.seed_keyword}"</CardTitle>
                    <CardDescription>{keywords.length} keywords found</CardDescription>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <select
                      className="border rounded-md px-2 py-1 text-sm bg-background"
                      value={sourceFilter}
                      onChange={(e) => setSourceFilter(e.target.value)}
                    >
                      <option value="all">All sources</option>
                      {sources.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <select
                      className="border rounded-md px-2 py-1 text-sm bg-background"
                      value={clusterFilter}
                      onChange={(e) => setClusterFilter(e.target.value)}
                    >
                      <option value="all">All clusters</option>
                      {clusters.map((c) => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border overflow-x-auto">
                  <table className="w-full text-sm min-w-[600px]">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <SortHeader label="Keyword" sortKey="keyword" current={sortKey} dir={sortDir} onToggle={toggleSort} />
                        <SortHeader label="Source" sortKey="source" current={sortKey} dir={sortDir} onToggle={toggleSort} />
                        <SortHeader label="Volume" sortKey="search_volume" current={sortKey} dir={sortDir} onToggle={toggleSort} />
                        <SortHeader label="Difficulty" sortKey="difficulty" current={sortKey} dir={sortDir} onToggle={toggleSort} />
                        <SortHeader label="Intent" sortKey="intent" current={sortKey} dir={sortDir} onToggle={toggleSort} />
                        <th className="px-3 py-2 text-left font-medium text-muted-foreground">Cluster</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredKeywords.map((kw) => (
                        <tr key={kw.id} className="border-b last:border-0 hover:bg-muted/30">
                          <td className="px-3 py-2 font-medium">{kw.keyword}</td>
                          <td className="px-3 py-2"><Badge variant="outline" className="text-[10px]">{kw.source}</Badge></td>
                          <td className="px-3 py-2 text-muted-foreground">{kw.search_volume ?? '-'}</td>
                          <td className="px-3 py-2">
                            {kw.difficulty != null ? (
                              <span className={kw.difficulty > 70 ? 'text-red-600' : kw.difficulty > 40 ? 'text-yellow-600' : 'text-green-600'}>
                                {kw.difficulty}
                              </span>
                            ) : '-'}
                          </td>
                          <td className="px-3 py-2">
                            {kw.intent && <Badge variant="secondary" className="text-[10px]">{kw.intent}</Badge>}
                          </td>
                          <td className="px-3 py-2 text-muted-foreground text-xs">{kw.cluster || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {!selectedResearch && !isRunning && (
            <Card>
              <CardContent className="py-12 text-center">
                <Search className="h-12 w-12 mx-auto text-muted-foreground/40 mb-4" />
                <h3 className="font-medium text-lg mb-1">No research selected</h3>
                <p className="text-sm text-muted-foreground">Enter a seed keyword to start research, or select from history</p>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-3">
          <h3 className="font-semibold text-sm">Research History</h3>
          {researches.length === 0 ? (
            <p className="text-sm text-muted-foreground">No research yet</p>
          ) : (
            researches.map((r) => (
              <Card
                key={r.id}
                className={`cursor-pointer transition-colors hover:bg-accent ${selectedResearch?.id === r.id ? 'ring-2 ring-primary' : ''}`}
                onClick={() => selectResearch(r)}
              >
                <CardContent className="p-3">
                  <p className="text-sm font-medium">{r.seed_keyword}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant={r.status === 'completed' ? 'outline' : 'secondary'} className="text-[10px]">{r.status}</Badge>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-1">{new Date(r.created_at).toLocaleDateString()}</p>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

function SortHeader({ label, sortKey, current, dir, onToggle }: {
  label: string; sortKey: SortKey; current: SortKey; dir: 'asc' | 'desc'; onToggle: (k: SortKey) => void
}) {
  return (
    <th className="px-3 py-2 text-left font-medium text-muted-foreground cursor-pointer select-none" onClick={() => onToggle(sortKey)}>
      <span className="flex items-center gap-1">
        {label}
        <ArrowUpDown className={`h-3 w-3 ${current === sortKey ? 'opacity-100' : 'opacity-30'}`} />
      </span>
    </th>
  )
}
