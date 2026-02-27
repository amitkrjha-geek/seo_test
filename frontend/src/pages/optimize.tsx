import { useState } from 'react'
import { useProject } from '@/hooks/use-project'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Sparkles, Play, RefreshCw, BookOpen, BarChart3, Lightbulb, ShieldCheck } from 'lucide-react'

interface OptimizationResult {
  readability_score: number | null
  grade_level: string | null
  keyword_density: number | null
  word_count: number | null
  entities: { name: string; type: string; relevance: number }[]
  suggestions: { category: string; message: string; priority: string }[]
  eeat_score: Record<string, number | string> | null
}

export default function OptimizePage() {
  const { currentProject } = useProject()
  const [content, setContent] = useState('')
  const [keyword, setKeyword] = useState('')
  const [result, setResult] = useState<OptimizationResult | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  async function analyzeContent() {
    if (!content || !keyword) return
    setIsAnalyzing(true)
    try {
      const data = await api.analyzeContent({
        content,
        keyword,
        project_id: currentProject?.id,
      })
      setResult(data as unknown as OptimizationResult)
    } catch { /* ignore */ }
    setIsAnalyzing(false)
  }

  const readabilityColor = (score: number) => score >= 70 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-red-600'
  const readabilityBg = (score: number) => score >= 70 ? 'bg-green-500/10' : score >= 50 ? 'bg-yellow-500/10' : 'bg-red-500/10'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Content Optimization</h1>
        <p className="text-muted-foreground">Analyze and optimize content for SEO performance</p>
      </div>

      {/* Input */}
      <div className="grid gap-4 lg:grid-cols-[1fr_340px]" style={{ minWidth: 0 }}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Content to Analyze</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Input
              placeholder="Target keyword"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
            />
            <Textarea
              placeholder="Paste your content here..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="min-h-[250px] sm:min-h-[400px] font-mono text-sm"
            />
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                {content.split(/\s+/).filter(Boolean).length} words
              </span>
              <Button onClick={analyzeContent} disabled={isAnalyzing || !content || !keyword}>
                {isAnalyzing ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Sparkles className="h-4 w-4 mr-2" />}
                {isAnalyzing ? 'Analyzing...' : 'Analyze'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results Panel */}
        <div className="space-y-4">
          {result ? (
            <>
              {/* Readability Score */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <BookOpen className="h-4 w-4" /> Readability
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4">
                    <div className={`flex flex-col items-center justify-center rounded-full h-20 w-20 ${readabilityBg(result.readability_score ?? 0)}`}>
                      <span className={`text-2xl font-bold ${readabilityColor(result.readability_score ?? 0)}`}>
                        {result.readability_score ?? '-'}
                      </span>
                    </div>
                    <div>
                      {result.grade_level && <p className="text-sm"><span className="text-muted-foreground">Grade Level:</span> {result.grade_level}</p>}
                      {result.word_count && <p className="text-sm"><span className="text-muted-foreground">Words:</span> {result.word_count}</p>}
                      {result.keyword_density != null && (
                        <p className="text-sm"><span className="text-muted-foreground">Keyword Density:</span> {(result.keyword_density * 100).toFixed(1)}%</p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* E-E-A-T Score */}
              {result.eeat_score && Object.keys(result.eeat_score).length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <ShieldCheck className="h-4 w-4" /> E-E-A-T Score
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {Object.entries(result.eeat_score).map(([key, value]) => (
                        <div key={key} className="flex items-center justify-between">
                          <span className="text-sm capitalize">{key.replace(/_/g, ' ')}</span>
                          <span className="text-sm font-medium">{typeof value === 'number' ? `${value}/10` : String(value)}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Entities */}
              {result.entities && result.entities.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <BarChart3 className="h-4 w-4" /> Entities ({result.entities.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-1.5 max-h-60 overflow-y-auto">
                      {result.entities.map((entity, idx) => (
                        <div key={idx} className="flex items-center justify-between text-sm">
                          <span className="font-medium">{entity.name}</span>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-[10px]">{entity.type}</Badge>
                            <span className="text-xs text-muted-foreground">{(entity.relevance * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Suggestions */}
              {result.suggestions && result.suggestions.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Lightbulb className="h-4 w-4" /> Suggestions ({result.suggestions.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 max-h-60 overflow-y-auto">
                      {result.suggestions.map((s, idx) => (
                        <div key={idx} className="rounded-lg border p-2.5">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge
                              variant={s.priority === 'high' ? 'destructive' : s.priority === 'medium' ? 'secondary' : 'outline'}
                              className="text-[10px]"
                            >
                              {s.priority}
                            </Badge>
                            <span className="text-xs text-muted-foreground">{s.category}</span>
                          </div>
                          <p className="text-sm">{s.message}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <Sparkles className="h-10 w-10 mx-auto text-muted-foreground/40 mb-3" />
                <h3 className="font-medium mb-1">No analysis yet</h3>
                <p className="text-xs text-muted-foreground">Paste content and click Analyze to get optimization suggestions</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
