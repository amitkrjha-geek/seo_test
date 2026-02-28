import { useState, useEffect } from 'react'
import { useProject } from '@/hooks/use-project'
import { api } from '@/lib/api'
import type { ContentBrief } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { BookOpen, Play, RefreshCw, FileText, List, Target } from 'lucide-react'

export default function BriefPage() {
  const { currentProject } = useProject()
  const [keyword, setKeyword] = useState('')
  const [provider, setProvider] = useState('anthropic')
  const [briefs, setBriefs] = useState<{ id: string; target_keyword: string; status: string; created_at: string }[]>([])
  const [selected, setSelected] = useState<ContentBrief | null>(null)
  const [isRunning, setIsRunning] = useState(false)

  useEffect(() => {
    if (currentProject) loadBriefs()
  }, [currentProject])

  async function loadBriefs() {
    if (!currentProject) return
    try {
      const data = await api.getBriefs(currentProject.id)
      setBriefs(data)
    } catch { /* ignore */ }
  }

  async function generateBrief() {
    if (!currentProject || !keyword) return
    setIsRunning(true)
    try {
      const { id } = await api.createBrief(currentProject.id, keyword, provider)
      const poll = setInterval(async () => {
        try {
          const brief = await api.getBrief(id)
          if (brief.status === 'ready' || brief.status === 'failed') {
            clearInterval(poll)
            setIsRunning(false)
            setSelected(brief)
            loadBriefs()
          }
        } catch {
          clearInterval(poll)
          setIsRunning(false)
        }
      }, 3000)
    } catch {
      setIsRunning(false)
    }
  }

  async function selectBrief(b: { id: string }) {
    try {
      const brief = await api.getBrief(b.id)
      setSelected(brief)
    } catch { /* ignore */ }
  }

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Select a project to generate briefs</p>
      </div>
    )
  }

  const outline = selected?.outline as Record<string, unknown> | null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Content Brief</h1>
        <p className="text-muted-foreground">Generate AI-powered content briefs from SERP analysis</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <BookOpen className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Target keyword for the brief..."
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                className="pl-10"
                onKeyDown={(e) => e.key === 'Enter' && generateBrief()}
              />
            </div>
            <div className="flex gap-3">
              <select
                className="border rounded-md px-3 py-2 text-sm bg-background flex-1 sm:flex-none"
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
              >
                <option value="anthropic">Claude</option>
                <option value="openai">GPT</option>
                <option value="google_ai">Gemini</option>
              </select>
              <Button onClick={generateBrief} disabled={isRunning || !keyword} className="flex-1 sm:flex-none">
                {isRunning ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
                {isRunning ? 'Generating...' : 'Generate Brief'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-[1fr_260px]">
        <div className="space-y-4">
          {selected && (
            <>
              {/* SERP Insights */}
              {selected.serp_insights && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2"><Target className="h-4 w-4" /> SERP Insights</CardTitle>
                    <CardDescription>Analysis of top-ranking pages for "{selected.target_keyword}"</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-3 md:grid-cols-2">
                      {Object.entries(selected.serp_insights).map(([key, value]) => (
                        <div key={key} className="rounded-lg border p-3">
                          <p className="text-xs text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</p>
                          <div className="text-sm font-medium mt-1">
                            {Array.isArray(value)
                              ? value.length > 0 && typeof value[0] === 'object'
                                ? (value as Array<Record<string, unknown>>).map((item, i) => (
                                    <div key={i} className="mb-2 last:mb-0">
                                      {item.title && <p className="font-semibold">{String(item.title)}</p>}
                                      {item.snippet && <p className="text-xs text-muted-foreground">{String(item.snippet)}</p>}
                                      {item.link && <a href={String(item.link)} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline break-all">{String(item.link)}</a>}
                                      {item.question && <p>{String(item.question)}</p>}
                                    </div>
                                  ))
                                : (value as string[]).join(', ')
                              : typeof value === 'object' && value !== null
                                ? JSON.stringify(value, null, 2)
                                : String(value)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Outline */}
              {outline && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2"><List className="h-4 w-4" /> Content Outline</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <OutlineViewer data={outline} />
                  </CardContent>
                </Card>
              )}

              {!outline && selected.status === 'ready' && (
                <Card>
                  <CardContent className="py-8 text-center">
                    <p className="text-muted-foreground">Brief generated but no outline data available</p>
                  </CardContent>
                </Card>
              )}
            </>
          )}

          {!selected && !isRunning && (
            <Card>
              <CardContent className="py-12 text-center">
                <BookOpen className="h-12 w-12 mx-auto text-muted-foreground/40 mb-4" />
                <h3 className="font-medium text-lg mb-1">No brief selected</h3>
                <p className="text-sm text-muted-foreground">Enter a keyword to generate a content brief, or select from history</p>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-3">
          <h3 className="font-semibold text-sm">Brief History</h3>
          {briefs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No briefs yet</p>
          ) : (
            briefs.map((b) => (
              <Card
                key={b.id}
                className={`cursor-pointer transition-colors hover:bg-accent ${selected?.id === b.id ? 'ring-2 ring-primary' : ''}`}
                onClick={() => selectBrief(b)}
              >
                <CardContent className="p-3">
                  <p className="text-sm font-medium">{b.target_keyword}</p>
                  <Badge variant={b.status === 'ready' ? 'outline' : b.status === 'failed' ? 'destructive' : 'secondary'} className="text-[10px] mt-1">
                    {b.status}
                  </Badge>
                  <p className="text-[10px] text-muted-foreground mt-1">{new Date(b.created_at).toLocaleDateString()}</p>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

function parseOutlineData(data: Record<string, unknown>): Record<string, unknown> {
  // If we have a raw_brief string, try to parse it as JSON (strip code fences first)
  if (data.raw_brief && typeof data.raw_brief === 'string') {
    try {
      let cleaned = (data.raw_brief as string).trim()
      if (cleaned.startsWith('```')) {
        cleaned = cleaned.split('\n').slice(1).join('\n') // remove opening fence line
        if (cleaned.trimEnd().endsWith('```')) {
          cleaned = cleaned.trimEnd().slice(0, -3).trimEnd()
        }
      }
      const parsed = JSON.parse(cleaned)
      if (typeof parsed === 'object' && parsed !== null) return parsed
    } catch { /* fall through */ }
  }
  return data
}

function extractSections(data: Record<string, unknown>): Record<string, unknown>[] {
  // Direct array fields
  for (const key of ['sections', 'headings']) {
    if (Array.isArray(data[key])) return data[key] as Record<string, unknown>[]
  }
  // Nested outline objects like { content_outline: { h2: [...] } } or { outline: { sections: [...] } }
  for (const key of ['content_outline', 'outline']) {
    const val = data[key]
    if (val && typeof val === 'object' && !Array.isArray(val)) {
      const obj = val as Record<string, unknown>
      // Look for arrays inside the outline object
      for (const subKey of ['h2', 'sections', 'headings', 'h2_sections']) {
        if (Array.isArray(obj[subKey])) return obj[subKey] as Record<string, unknown>[]
      }
      // If the outline object itself has numbered/named children, try first array found
      const firstArray = Object.values(obj).find(v => Array.isArray(v))
      if (firstArray) return firstArray as Record<string, unknown>[]
    }
    if (Array.isArray(val)) return val as Record<string, unknown>[]
  }
  return []
}

function OutlineViewer({ data: rawData }: { data: Record<string, unknown> }) {
  const data = parseOutlineData(rawData)

  const title = data.title || data.suggested_title || data.recommended_title || ''
  const meta = data.meta_description || data.meta || ''
  const wordCount = data.target_word_count || data.word_count || data.word_count_target || ''
  const sections = extractSections(data)

  // Keys we've already rendered
  const handledKeys = new Set([
    'title', 'suggested_title', 'recommended_title',
    'sections', 'headings', 'content_outline', 'outline',
    'meta_description', 'meta', 'target_word_count', 'word_count', 'word_count_target',
    'raw_brief'
  ])
  const extraEntries = Object.entries(data).filter(([k]) => !handledKeys.has(k))

  // If raw_brief couldn't be parsed AND there's no structured data, show as text
  if (rawData.raw_brief && typeof rawData.raw_brief === 'string' && !title && sections.length === 0 && extraEntries.length === 0) {
    return (
      <div className="prose prose-sm max-w-none">
        <div className="whitespace-pre-wrap text-sm">{rawData.raw_brief as string}</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {title && (
        <div>
          <p className="text-xs text-muted-foreground mb-1">Suggested Title</p>
          <p className="font-semibold text-lg">{String(title)}</p>
        </div>
      )}
      {meta && (
        <div>
          <p className="text-xs text-muted-foreground mb-1">Meta Description</p>
          <p className="text-sm">{String(meta)}</p>
        </div>
      )}
      {wordCount && (
        <div>
          <p className="text-xs text-muted-foreground mb-1">Target Word Count</p>
          <Badge variant="secondary">{String(wordCount)} words</Badge>
        </div>
      )}
      {sections.length > 0 && (
        <div>
          <p className="text-xs text-muted-foreground mb-2">Content Outline</p>
          <div className="space-y-2">
            {sections.map((section, idx) => (
              <div key={idx} className="rounded-lg border p-3">
                <div className="flex items-center gap-2 mb-1">
                  <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="font-medium text-sm">
                    {(() => {
                      const raw = typeof section === 'string' ? section : String(section.heading || section.title || section.h2 || section.h3 || `Section ${idx + 1}`)
                      return raw.replace(/^H[2-4]:\s*/i, '')
                    })()}
                  </span>
                </div>
                {typeof section === 'object' && (section.points || section.key_points || section.subheadings || section.sub_sections) && (
                  <ul className="ml-6 mt-1 space-y-1">
                    {((section.points || section.key_points || section.subheadings || section.sub_sections) as unknown[]).map((point, pidx) => (
                      <li key={pidx} className="text-xs text-muted-foreground list-disc">
                        {typeof point === 'string' ? point : typeof point === 'object' && point !== null ? ((point as Record<string, unknown>).heading || (point as Record<string, unknown>).title || (point as Record<string, unknown>).text || JSON.stringify(point)) as string : String(point)}
                      </li>
                    ))}
                  </ul>
                )}
                {typeof section === 'object' && section.description && (
                  <p className="text-xs text-muted-foreground ml-6 mt-1">{section.description as string}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      {extraEntries.length > 0 && (
        <div className="space-y-3">
          {extraEntries.map(([key, value]) => (
            <div key={key} className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground mb-1 capitalize">{key.replace(/_/g, ' ')}</p>
              <div className="text-sm">
                {typeof value === 'string' ? (
                  <p>{value}</p>
                ) : Array.isArray(value) ? (
                  <ul className="ml-4 space-y-1">
                    {value.map((item, i) => (
                      <li key={i} className="list-disc text-sm">
                        {typeof item === 'string' ? item : typeof item === 'object' && item !== null
                          ? (() => {
                              const obj = item as Record<string, unknown>
                              const anchorText = obj.link_anchor || obj.anchor || obj.anchor_text
                              const url = obj.url || obj.link || obj.href
                              if (anchorText && url) {
                                return <><span className="font-medium">{String(anchorText)}</span> <span className="text-muted-foreground">→ {String(url)}</span></>
                              }
                              return String(obj.title || obj.text || obj.query || obj.question || Object.values(obj).join(', '))
                            })()
                          : String(item)}
                      </li>
                    ))}
                  </ul>
                ) : typeof value === 'object' && value !== null ? (
                  <div className="space-y-1">
                    {Object.entries(value as Record<string, unknown>).map(([k, v]) => (
                      <p key={k}><span className="text-muted-foreground capitalize">{k.replace(/_/g, ' ')}:</span> {typeof v === 'string' ? ` ${v}` : Array.isArray(v) ? ` ${v.join(', ')}` : ` ${String(v)}`}</p>
                    ))}
                  </div>
                ) : (
                  <p>{String(value)}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
