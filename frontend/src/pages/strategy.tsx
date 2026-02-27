import { useState, useEffect } from 'react'
import { useProject } from '@/hooks/use-project'
import { api } from '@/lib/api'
import type { ContentPillar, TopicCluster } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Lightbulb, Plus, Trash2, Sparkles, RefreshCw, Layers } from 'lucide-react'

interface AiPillarRecommendation {
  name: string
  description: string
  topics: string[]
}

export default function StrategyPage() {
  const { currentProject } = useProject()
  const [pillars, setPillars] = useState<ContentPillar[]>([])
  const [clusters, setClusters] = useState<TopicCluster[]>([])
  const [loading, setLoading] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiRecommendations, setAiRecommendations] = useState<AiPillarRecommendation[]>([])

  // Add pillar dialog
  const [showAddPillar, setShowAddPillar] = useState(false)
  const [newPillarName, setNewPillarName] = useState('')
  const [newPillarDesc, setNewPillarDesc] = useState('')
  const [newPillarKeywords, setNewPillarKeywords] = useState('')
  const [newPillarColor, setNewPillarColor] = useState('#6366f1')

  // Add cluster dialog
  const [showAddCluster, setShowAddCluster] = useState(false)
  const [clusterPillarId, setClusterPillarId] = useState('')
  const [newClusterTopic, setNewClusterTopic] = useState('')
  const [newClusterSubtopics, setNewClusterSubtopics] = useState('')

  useEffect(() => {
    if (currentProject) loadData()
  }, [currentProject])

  async function loadData() {
    if (!currentProject) return
    setLoading(true)
    try {
      const [p, c] = await Promise.all([
        api.getPillars(currentProject.id),
        api.getClusters(currentProject.id),
      ])
      setPillars(p)
      setClusters(c)
    } catch {
      /* ignore */
    } finally {
      setLoading(false)
    }
  }

  async function handleAddPillar() {
    if (!currentProject || !newPillarName.trim()) return
    try {
      const keywords = newPillarKeywords
        .split(',')
        .map((k) => k.trim())
        .filter(Boolean)
      const pillar = await api.createPillar({
        project_id: currentProject.id,
        name: newPillarName.trim(),
        description: newPillarDesc.trim() || undefined,
        keywords: keywords.length > 0 ? keywords : undefined,
        color: newPillarColor,
      })
      setPillars((prev) => [pillar, ...prev])
      setShowAddPillar(false)
      setNewPillarName('')
      setNewPillarDesc('')
      setNewPillarKeywords('')
      setNewPillarColor('#6366f1')
    } catch {
      /* ignore */
    }
  }

  async function handleDeletePillar(id: string) {
    try {
      await api.deletePillar(id)
      setPillars((prev) => prev.filter((p) => p.id !== id))
      setClusters((prev) => prev.filter((c) => c.pillar_id !== id))
    } catch {
      /* ignore */
    }
  }

  function openAddCluster(pillarId: string) {
    setClusterPillarId(pillarId)
    setNewClusterTopic('')
    setNewClusterSubtopics('')
    setShowAddCluster(true)
  }

  async function handleAddCluster() {
    if (!currentProject || !clusterPillarId || !newClusterTopic.trim()) return
    try {
      const subtopics = newClusterSubtopics
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
      const cluster = await api.createCluster({
        project_id: currentProject.id,
        pillar_id: clusterPillarId,
        topic: newClusterTopic.trim(),
        subtopics: subtopics.length > 0 ? subtopics : undefined,
      })
      setClusters((prev) => [cluster, ...prev])
      setShowAddCluster(false)
    } catch {
      /* ignore */
    }
  }

  async function handleDeleteCluster(id: string) {
    try {
      await api.deleteCluster(id)
      setClusters((prev) => prev.filter((c) => c.id !== id))
    } catch {
      /* ignore */
    }
  }

  async function handleGenerateRecommendations() {
    if (!currentProject) return
    setAiLoading(true)
    setAiRecommendations([])
    try {
      const result = await api.getAiRecommendations(currentProject.id)
      setAiRecommendations(result.pillars || [])
    } catch {
      /* ignore */
    } finally {
      setAiLoading(false)
    }
  }

  async function addRecommendationToStrategy(rec: AiPillarRecommendation) {
    if (!currentProject) return
    try {
      const pillar = await api.createPillar({
        project_id: currentProject.id,
        name: rec.name,
        description: rec.description,
      })
      setPillars((prev) => [pillar, ...prev])

      // Also add topics as clusters
      for (const topic of rec.topics) {
        const cluster = await api.createCluster({
          project_id: currentProject.id,
          pillar_id: pillar.id,
          topic,
        })
        setClusters((prev) => [cluster, ...prev])
      }

      // Remove from recommendations
      setAiRecommendations((prev) => prev.filter((r) => r.name !== rec.name))
    } catch {
      /* ignore */
    }
  }

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Select a project to manage content strategy</p>
      </div>
    )
  }

  const pillarClusters = (pillarId: string) => clusters.filter((c) => c.pillar_id === pillarId)

  const COLORS = ['#6366f1', '#f43f5e', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16']

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Content Strategy</h1>
        <p className="text-muted-foreground">Organize your content into pillars and topic clusters</p>
      </div>

      {/* Content Pillars */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Content Pillars</h2>
          </div>
          <Button size="sm" onClick={() => setShowAddPillar(true)}>
            <Plus className="h-4 w-4 mr-1" /> Add Pillar
          </Button>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        )}

        {!loading && pillars.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <Layers className="h-12 w-12 mx-auto text-muted-foreground/40 mb-4" />
              <h3 className="font-medium text-lg mb-1">No content pillars yet</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Create pillars to organize your content strategy, or use AI to generate recommendations.
              </p>
              <Button variant="outline" onClick={() => setShowAddPillar(true)}>
                <Plus className="h-4 w-4 mr-1" /> Create Your First Pillar
              </Button>
            </CardContent>
          </Card>
        )}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {pillars.map((pillar) => (
            <Card key={pillar.id} className="overflow-hidden">
              <div className="flex">
                <div className="w-1.5 shrink-0" style={{ backgroundColor: pillar.color }} />
                <div className="flex-1">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-base">{pillar.name}</CardTitle>
                        {pillar.description && (
                          <p className="text-sm text-muted-foreground mt-1">{pillar.description}</p>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-muted-foreground hover:text-destructive shrink-0"
                        onClick={() => handleDeletePillar(pillar.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                    {pillar.keywords && pillar.keywords.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        <Badge variant="secondary" className="text-[10px]">
                          {pillar.keywords.length} keyword{pillar.keywords.length !== 1 ? 's' : ''}
                        </Badge>
                        {pillar.keywords.slice(0, 3).map((kw) => (
                          <Badge key={kw} variant="outline" className="text-[10px]">
                            {kw}
                          </Badge>
                        ))}
                        {pillar.keywords.length > 3 && (
                          <Badge variant="outline" className="text-[10px]">
                            +{pillar.keywords.length - 3} more
                          </Badge>
                        )}
                      </div>
                    )}
                  </CardHeader>
                  <CardContent className="pt-0 pb-3">
                    <div className="space-y-1.5">
                      {pillarClusters(pillar.id).map((cluster) => (
                        <div
                          key={cluster.id}
                          className="flex items-center justify-between rounded-md bg-muted/50 px-2.5 py-1.5 text-sm"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <Lightbulb className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                            <span className="truncate">{cluster.topic}</span>
                          </div>
                          <div className="flex items-center gap-1.5 shrink-0">
                            <Badge variant="outline" className="text-[9px]">
                              {cluster.priority}
                            </Badge>
                            <button
                              className="text-muted-foreground hover:text-destructive"
                              onClick={() => handleDeleteCluster(cluster.id)}
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          </div>
                        </div>
                      ))}
                      {pillarClusters(pillar.id).length === 0 && (
                        <p className="text-xs text-muted-foreground italic py-1">No topics yet</p>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-2 h-7 text-xs w-full"
                      onClick={() => openAddCluster(pillar.id)}
                    >
                      <Plus className="h-3 w-3 mr-1" /> Add Topic
                    </Button>
                  </CardContent>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* AI Recommendations */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">AI Recommendations</h2>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={handleGenerateRecommendations}
            disabled={aiLoading}
          >
            {aiLoading ? (
              <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4 mr-1" />
            )}
            {aiLoading ? 'Generating...' : 'Generate AI Recommendations'}
          </Button>
        </div>

        {aiLoading && (
          <Card>
            <CardContent className="py-12 text-center">
              <RefreshCw className="h-8 w-8 mx-auto animate-spin text-primary mb-4" />
              <p className="text-sm text-muted-foreground">
                AI is analyzing your keywords and brand to suggest content pillars...
              </p>
            </CardContent>
          </Card>
        )}

        {!aiLoading && aiRecommendations.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <Sparkles className="h-12 w-12 mx-auto text-muted-foreground/40 mb-4" />
              <h3 className="font-medium text-lg mb-1">No recommendations yet</h3>
              <p className="text-sm text-muted-foreground">
                Click "Generate AI Recommendations" to get content strategy suggestions based on your keywords and brand persona.
              </p>
            </CardContent>
          </Card>
        )}

        {aiRecommendations.length > 0 && (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {aiRecommendations.map((rec, idx) => (
              <Card key={idx} className="border-dashed">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-base">{rec.name}</CardTitle>
                    <Badge variant="secondary" className="text-[10px] shrink-0">AI Suggested</Badge>
                  </div>
                  {rec.description && (
                    <p className="text-sm text-muted-foreground mt-1">{rec.description}</p>
                  )}
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-1 mb-3">
                    {rec.topics.map((topic, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Lightbulb className="h-3 w-3 shrink-0" />
                        <span>{topic}</span>
                      </div>
                    ))}
                  </div>
                  <Button
                    size="sm"
                    className="w-full"
                    onClick={() => addRecommendationToStrategy(rec)}
                  >
                    <Plus className="h-4 w-4 mr-1" /> Add to Strategy
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Add Pillar Dialog */}
      <Dialog open={showAddPillar} onOpenChange={setShowAddPillar}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Content Pillar</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <label className="text-sm font-medium mb-1.5 block">Name</label>
              <Input
                placeholder="e.g., Technical SEO"
                value={newPillarName}
                onChange={(e) => setNewPillarName(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">Description</label>
              <Input
                placeholder="Brief description of this content pillar"
                value={newPillarDesc}
                onChange={(e) => setNewPillarDesc(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">Keywords (comma-separated)</label>
              <Input
                placeholder="seo, technical seo, site speed"
                value={newPillarKeywords}
                onChange={(e) => setNewPillarKeywords(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">Color</label>
              <div className="flex gap-2">
                {COLORS.map((c) => (
                  <button
                    key={c}
                    className={`h-7 w-7 rounded-full border-2 transition-all ${newPillarColor === c ? 'border-foreground scale-110' : 'border-transparent'}`}
                    style={{ backgroundColor: c }}
                    onClick={() => setNewPillarColor(c)}
                  />
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddPillar(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddPillar} disabled={!newPillarName.trim()}>
              Create Pillar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Cluster Dialog */}
      <Dialog open={showAddCluster} onOpenChange={setShowAddCluster}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Topic Cluster</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <label className="text-sm font-medium mb-1.5 block">Topic</label>
              <Input
                placeholder="e.g., Core Web Vitals Optimization"
                value={newClusterTopic}
                onChange={(e) => setNewClusterTopic(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">Subtopics (comma-separated)</label>
              <Input
                placeholder="LCP, FID, CLS, performance budget"
                value={newClusterSubtopics}
                onChange={(e) => setNewClusterSubtopics(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddCluster(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddCluster} disabled={!newClusterTopic.trim()}>
              Add Topic
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
