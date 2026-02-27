import { useState, useEffect, useRef } from 'react'
import { useProject } from '@/hooks/use-project'
import { api } from '@/lib/api'
import type { ContentDraft } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { TiptapEditor, type TiptapEditorRef } from '@/components/editor/tiptap-editor'
import { SeoSidebar } from '@/components/editor/seo-sidebar'
import { PublishDialog } from '@/components/publishing/publish-dialog'
import { PenTool, RefreshCw, Save, Sparkles, Copy, FileText, Send } from 'lucide-react'

export default function WritePage() {
  const { currentProject } = useProject()
  const [keyword, setKeyword] = useState('')
  const [provider, setProvider] = useState('anthropic')
  const [drafts, setDrafts] = useState<ContentDraft[]>([])
  const [selected, setSelected] = useState<ContentDraft | null>(null)
  const [editorText, setEditorText] = useState('')
  const [editorHtml, setEditorHtml] = useState('')
  const [isWriting, setIsWriting] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [metaTitle, setMetaTitle] = useState('')
  const [metaDescription, setMetaDescription] = useState('')
  const [showPublish, setShowPublish] = useState(false)
  const editorRef = useRef<TiptapEditorRef>(null)
  const abortRef = useRef<(() => void) | null>(null)

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

  async function startWriting() {
    if (!currentProject || !keyword) return
    setIsWriting(true)
    editorRef.current?.clear()

    try {
      let accumulated = ''
      const cancel = api.streamSSE(
        `/content/stream?project_id=${currentProject.id}&keyword=${encodeURIComponent(keyword)}&provider=${provider}`,
        (data) => {
          if (typeof data === 'object' && data !== null && 'chunk' in data) {
            const chunk = (data as { chunk: string }).chunk
            accumulated += chunk
            editorRef.current?.setContent(markdownToHtml(accumulated))
          }
        },
        () => {
          setIsWriting(false)
          loadDrafts()
        }
      )
      abortRef.current = cancel
    } catch {
      setIsWriting(false)
    }
  }

  async function selectDraft(d: ContentDraft) {
    try {
      const draft = await api.getContentDraft(d.id)
      setSelected(draft)
      setMetaTitle(draft.meta_title || '')
      setMetaDescription(draft.meta_description || '')
      const html = draft.content_html || markdownToHtml(draft.body || '')
      setEditorHtml(html)
      setEditorText(draft.body || '')
      editorRef.current?.setContent(html)
    } catch { /* ignore */ }
  }

  async function saveDraft() {
    if (!selected) return
    setIsSaving(true)
    try {
      const body = editorRef.current?.getText() || editorText
      const content_html = editorRef.current?.getHTML() || editorHtml
      const updated = await api.updateContentDraft(selected.id, {
        body,
        title: metaTitle || selected.title,
        content_html,
        meta_title: metaTitle,
        meta_description: metaDescription,
      })
      setSelected({ ...selected, ...updated })
      loadDrafts()
    } catch { /* ignore */ }
    setIsSaving(false)
  }

  function copyContent() {
    const content = editorRef.current?.getText() || editorText
    if (content) navigator.clipboard.writeText(content)
  }

  function handleEditorUpdate(html: string, text: string) {
    setEditorHtml(html)
    setEditorText(text)
  }

  const wordCount = editorText.split(/\s+/).filter(Boolean).length

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Select a project to write content</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">AI Content Writer</h1>
        <p className="text-muted-foreground">Generate SEO-optimized content with your brand voice</p>
      </div>

      {/* Writer Controls */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <PenTool className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Target keyword for content..."
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                className="pl-10"
                onKeyDown={(e) => e.key === 'Enter' && startWriting()}
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
              <Button onClick={startWriting} disabled={isWriting || !keyword} className="flex-1 sm:flex-none">
                {isWriting ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Sparkles className="h-4 w-4 mr-2" />}
                {isWriting ? 'Writing...' : 'Write Content'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-[1fr_220px_260px]">
        {/* Editor Area */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="min-w-0">
                  <CardTitle className="truncate">{selected?.title || keyword || 'New Content'}</CardTitle>
                  <CardDescription>
                    {wordCount} words
                    {selected?.seo_score != null && ` · SEO Score: ${selected.seo_score}/100`}
                    {selected?.llm_provider && ` · ${selected.llm_provider}`}
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={copyContent}>
                    <Copy className="h-3.5 w-3.5 mr-1" /> Copy
                  </Button>
                  {selected && (
                    <>
                      <Button size="sm" onClick={saveDraft} disabled={isSaving}>
                        <Save className="h-3.5 w-3.5 mr-1" /> {isSaving ? 'Saving...' : 'Save'}
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => setShowPublish(true)}>
                        <Send className="h-3.5 w-3.5 mr-1" /> Publish
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <TiptapEditor
                ref={editorRef}
                content={editorHtml}
                onUpdate={handleEditorUpdate}
                placeholder="Start writing or use AI to generate content..."
                projectId={currentProject.id}
                provider={provider}
              />
              {isWriting && (
                <div className="flex items-center gap-2 mt-3 text-sm text-muted-foreground">
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  AI is writing content...
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* SEO Sidebar */}
        <SeoSidebar
          text={editorText}
          keyword={keyword}
          seoScore={selected?.seo_score ?? null}
          metaTitle={metaTitle}
          metaDescription={metaDescription}
          onMetaTitleChange={setMetaTitle}
          onMetaDescriptionChange={setMetaDescription}
        />

        {/* Draft History */}
        <div className="space-y-3">
          <h3 className="font-semibold text-sm">Content Drafts</h3>
          {drafts.length === 0 ? (
            <p className="text-sm text-muted-foreground">No drafts yet</p>
          ) : (
            drafts.map((d) => (
              <Card
                key={d.id}
                className={`cursor-pointer transition-colors hover:bg-accent ${selected?.id === d.id ? 'ring-2 ring-primary' : ''}`}
                onClick={() => selectDraft(d)}
              >
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                    <p className="text-sm font-medium truncate">{d.title}</p>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant={d.status === 'published' ? 'outline' : d.status === 'failed' ? 'destructive' : 'secondary'} className="text-[10px]">
                      {d.status}
                    </Badge>
                    {d.seo_score != null && <span className="text-[10px] text-muted-foreground">Score: {d.seo_score}</span>}
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-1">{d.llm_provider} · {new Date(d.created_at).toLocaleDateString()}</p>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>

      {selected && (
        <PublishDialog
          open={showPublish}
          onOpenChange={setShowPublish}
          draftId={selected.id}
          projectId={currentProject.id}
        />
      )}
    </div>
  )
}

function markdownToHtml(md: string): string {
  if (!md) return ''
  return md
    .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[hulo])(.+)$/gm, '<p>$1</p>')
    .replace(/<p><\/p>/g, '')
}
