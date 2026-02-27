import { useState, useEffect } from 'react'
import { useProject } from '@/hooks/use-project'
import { api } from '@/lib/api'
import type { PastArticle } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Link2, Plus, Trash2, RefreshCw, AlertTriangle } from 'lucide-react'

export default function PastArticlesPage() {
  const { currentProject } = useProject()
  const [articles, setArticles] = useState<PastArticle[]>([])
  const [loading, setLoading] = useState(false)
  const [importing, setImporting] = useState(false)
  const [importUrl, setImportUrl] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (currentProject) loadArticles()
  }, [currentProject])

  async function loadArticles() {
    if (!currentProject) return
    setLoading(true)
    try {
      const data = await api.getPastArticles(currentProject.id)
      setArticles(data)
    } catch {
      /* ignore */
    } finally {
      setLoading(false)
    }
  }

  async function handleImport() {
    if (!currentProject || !importUrl.trim()) return
    setImporting(true)
    setError('')
    try {
      const article = await api.importPastArticle(currentProject.id, importUrl.trim())
      setArticles((prev) => [article, ...prev])
      setImportUrl('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to import article')
    } finally {
      setImporting(false)
    }
  }

  async function handleDelete(id: string) {
    try {
      await api.deletePastArticle(id)
      setArticles((prev) => prev.filter((a) => a.id !== id))
    } catch {
      /* ignore */
    }
  }

  function truncateUrl(url: string, maxLen = 50) {
    if (url.length <= maxLen) return url
    return url.slice(0, maxLen) + '...'
  }

  function scoreColor(score: number | null) {
    if (score === null) return 'text-muted-foreground'
    if (score >= 70) return 'text-green-600'
    if (score >= 50) return 'text-yellow-600'
    return 'text-red-600'
  }

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Select a project to manage past articles</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Past Articles</h1>
        <p className="text-muted-foreground">Import and audit your existing content for optimization opportunities</p>
      </div>

      {/* Import Form */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Enter article URL to import (e.g., https://example.com/blog/post)"
                value={importUrl}
                onChange={(e) => setImportUrl(e.target.value)}
                className="pl-10"
                onKeyDown={(e) => e.key === 'Enter' && handleImport()}
              />
            </div>
            <Button
              onClick={handleImport}
              disabled={importing || !importUrl.trim()}
              className="w-full sm:w-auto"
            >
              {importing ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Plus className="h-4 w-4 mr-2" />
              )}
              {importing ? 'Importing...' : 'Import'}
            </Button>
          </div>
          {error && (
            <div className="flex items-center gap-2 mt-3 text-sm text-destructive">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Articles List */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      )}

      {!loading && articles.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <Link2 className="h-12 w-12 mx-auto text-muted-foreground/40 mb-4" />
            <h3 className="font-medium text-lg mb-1">No articles imported yet</h3>
            <p className="text-sm text-muted-foreground">
              Import your existing articles by URL to analyze their SEO performance and find refresh opportunities.
            </p>
          </CardContent>
        </Card>
      )}

      {!loading && articles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Imported Articles ({articles.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border overflow-x-auto">
              <table className="w-full text-sm min-w-[700px]">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-3 py-2 text-left font-medium text-muted-foreground">Title</th>
                    <th className="px-3 py-2 text-left font-medium text-muted-foreground">URL</th>
                    <th className="px-3 py-2 text-left font-medium text-muted-foreground">Words</th>
                    <th className="px-3 py-2 text-left font-medium text-muted-foreground">SEO Score</th>
                    <th className="px-3 py-2 text-left font-medium text-muted-foreground">Status</th>
                    <th className="px-3 py-2 text-left font-medium text-muted-foreground">Crawled</th>
                    <th className="px-3 py-2 text-right font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {articles.map((article) => (
                    <tr key={article.id} className="border-b last:border-0 hover:bg-muted/30">
                      <td className="px-3 py-2 font-medium max-w-[200px] truncate">
                        {article.title || 'Untitled'}
                      </td>
                      <td className="px-3 py-2 text-muted-foreground">
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:underline text-primary"
                          title={article.url}
                        >
                          {truncateUrl(article.url)}
                        </a>
                      </td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {article.word_count.toLocaleString()}
                      </td>
                      <td className="px-3 py-2">
                        <span className={`font-medium ${scoreColor(article.seo_score)}`}>
                          {article.seo_score !== null ? `${article.seo_score}/100` : '--'}
                        </span>
                      </td>
                      <td className="px-3 py-2">
                        {article.needs_refresh ? (
                          <Badge variant="destructive" className="text-[10px]">
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            Needs Refresh
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-[10px] text-green-600 border-green-600/30">
                            OK
                          </Badge>
                        )}
                      </td>
                      <td className="px-3 py-2 text-muted-foreground text-xs">
                        {new Date(article.crawled_at).toLocaleDateString()}
                      </td>
                      <td className="px-3 py-2 text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-muted-foreground hover:text-destructive"
                          onClick={() => handleDelete(article.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      {!loading && articles.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-3xl font-bold">{articles.length}</p>
              <p className="text-sm text-muted-foreground">Total Articles</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-3xl font-bold">
                {articles.filter((a) => a.seo_score !== null && a.seo_score >= 70).length}
              </p>
              <p className="text-sm text-muted-foreground">Good Score (70+)</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-3xl font-bold text-destructive">
                {articles.filter((a) => a.needs_refresh).length}
              </p>
              <p className="text-sm text-muted-foreground">Need Refresh</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
