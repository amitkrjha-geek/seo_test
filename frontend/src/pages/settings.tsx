import { useState, useEffect } from 'react'
import { useProject } from '@/hooks/use-project'
import { api } from '@/lib/api'
import type { BrandPersona, ProjectApiKey } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Trash2, Save, Eye, EyeOff } from 'lucide-react'
import { ApiKeyGuide } from '@/components/settings/api-key-guide'
import { ConnectionSettings } from '@/components/publishing/connection-settings'

const API_PROVIDERS = [
  { key: 'anthropic', label: 'Anthropic (Claude)', description: 'AI writing & analysis' },
  { key: 'openai', label: 'OpenAI (GPT)', description: 'AI writing & analysis' },
  { key: 'google_ai', label: 'Google AI (Gemini)', description: 'AI writing & analysis' },
  { key: 'serper', label: 'Serper.dev', description: 'SERP data & keyword research' },
  { key: 'textrazor', label: 'TextRazor', description: 'NLP entity extraction' },
  { key: 'google_nlp', label: 'Google Cloud NLP', description: 'Entity extraction' },
  { key: 'pagespeed', label: 'PageSpeed Insights', description: 'Core Web Vitals' },
]

export default function SettingsPage() {
  const { currentProject } = useProject()

  if (!currentProject) {
    return (
      <div className="py-20 text-center text-muted-foreground">
        Select a project to manage settings
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Project Settings</h1>
        <p className="text-muted-foreground">{currentProject.name}</p>
      </div>
      <Tabs defaultValue="persona">
        <TabsList className="w-full sm:w-auto">
          <TabsTrigger value="persona" className="flex-1 sm:flex-none">Brand Persona</TabsTrigger>
          <TabsTrigger value="api-keys" className="flex-1 sm:flex-none">API Keys</TabsTrigger>
          <TabsTrigger value="publishing" className="flex-1 sm:flex-none">Publishing</TabsTrigger>
          <TabsTrigger value="general" className="flex-1 sm:flex-none">General</TabsTrigger>
        </TabsList>
        <TabsContent value="persona" className="mt-4">
          <BrandPersonaForm projectId={currentProject.id} />
        </TabsContent>
        <TabsContent value="api-keys" className="mt-4">
          <ApiKeysForm projectId={currentProject.id} />
        </TabsContent>
        <TabsContent value="publishing" className="mt-4">
          <ConnectionSettings projectId={currentProject.id} />
        </TabsContent>
        <TabsContent value="general" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Project Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label>Name</Label>
                  <p className="text-sm">{currentProject.name}</p>
                </div>
                <div>
                  <Label>Domain</Label>
                  <p className="text-sm">{currentProject.domain}</p>
                </div>
                <div>
                  <Label>Business Type</Label>
                  <p className="text-sm capitalize">{currentProject.business_type}</p>
                </div>
                <div>
                  <Label>Created</Label>
                  <p className="text-sm">{new Date(currentProject.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

function BrandPersonaForm({ projectId }: { projectId: string }) {
  const [persona, setPersona] = useState<Partial<BrandPersona>>({})
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    setLoading(true)
    api.getBrandPersona(projectId)
      .then((p) => setPersona(p))
      .catch(() => setPersona({}))
      .finally(() => setLoading(false))
  }, [projectId])

  const handleSave = async () => {
    setSaving(true)
    setSuccess(false)
    try {
      const updated = await api.updateBrandPersona(projectId, persona)
      setPersona(updated)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch {
      // error
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="text-sm text-muted-foreground">Loading persona...</p>

  return (
    <Card>
      <CardHeader>
        <CardTitle>Brand Persona</CardTitle>
        <CardDescription>
          Define your brand voice. This is automatically injected into every AI prompt for this project.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Brand Name</Label>
            <Input
              value={persona.brand_name || ''}
              onChange={(e) => setPersona({ ...persona, brand_name: e.target.value })}
              placeholder="Acme SaaS"
            />
          </div>
          <div className="space-y-2">
            <Label>Tagline</Label>
            <Input
              value={persona.tagline || ''}
              onChange={(e) => setPersona({ ...persona, tagline: e.target.value })}
              placeholder="Simplify your workflow"
            />
          </div>
        </div>
        <div className="space-y-2">
          <Label>Voice & Tone</Label>
          <Textarea
            value={persona.voice_tone || ''}
            onChange={(e) => setPersona({ ...persona, voice_tone: e.target.value })}
            placeholder="Professional but approachable, witty not sarcastic"
            rows={2}
          />
        </div>
        <div className="space-y-2">
          <Label>Writing Style</Label>
          <Textarea
            value={persona.writing_style || ''}
            onChange={(e) => setPersona({ ...persona, writing_style: e.target.value })}
            placeholder="Use short sentences. Active voice. Data-driven claims."
            rows={2}
          />
        </div>
        <div className="space-y-2">
          <Label>Target Audience</Label>
          <Input
            value={persona.target_audience || ''}
            onChange={(e) => setPersona({ ...persona, target_audience: e.target.value })}
            placeholder="CTOs and engineering managers at mid-size companies"
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Do's</Label>
            <Textarea
              value={persona.dos || ''}
              onChange={(e) => setPersona({ ...persona, dos: e.target.value })}
              placeholder="Use customer success stories, cite specific metrics"
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label>Don'ts</Label>
            <Textarea
              value={persona.donts || ''}
              onChange={(e) => setPersona({ ...persona, donts: e.target.value })}
              placeholder="Never use jargon without explaining, avoid superlatives"
              rows={3}
            />
          </div>
        </div>
        <div className="space-y-2">
          <Label>Sample Content</Label>
          <Textarea
            value={persona.sample_content || ''}
            onChange={(e) => setPersona({ ...persona, sample_content: e.target.value })}
            placeholder="Paste an example of existing brand content..."
            rows={4}
          />
        </div>
        <div className="flex items-center gap-3">
          <Button onClick={handleSave} disabled={saving}>
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Saving...' : 'Save Persona'}
          </Button>
          {success && <span className="text-sm text-green-600">Saved!</span>}
        </div>
      </CardContent>
    </Card>
  )
}

function ApiKeysForm({ projectId }: { projectId: string }) {
  const [keys, setKeys] = useState<ProjectApiKey[]>([])
  const [newKeys, setNewKeys] = useState<Record<string, string>>({})
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    api.getProjectApiKeys(projectId)
      .then(setKeys)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [projectId])

  const handleSaveKey = async (provider: string) => {
    const key = newKeys[provider]
    if (!key) return
    try {
      await api.upsertProjectApiKey(projectId, { provider, api_key: key })
      const updated = await api.getProjectApiKeys(projectId)
      setKeys(updated)
      setNewKeys({ ...newKeys, [provider]: '' })
    } catch {
      // error
    }
  }

  const handleDeleteKey = async (provider: string) => {
    try {
      await api.deleteProjectApiKey(projectId, provider)
      setKeys(keys.filter((k) => k.provider !== provider))
    } catch {
      // error
    }
  }

  if (loading) return <p className="text-sm text-muted-foreground">Loading API keys...</p>

  return (
    <div className="space-y-4">
      {API_PROVIDERS.map((prov) => {
        const existing = keys.find((k) => k.provider === prov.key)
        return (
          <Card key={prov.key}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div>
                    <CardTitle className="text-sm">{prov.label}</CardTitle>
                    <CardDescription className="text-xs">{prov.description}</CardDescription>
                  </div>
                  <ApiKeyGuide provider={prov.key} />
                </div>
                {existing && <Badge variant="secondary">Configured</Badge>}
              </div>
            </CardHeader>
            <CardContent>
              {existing ? (
                <div className="flex items-center gap-2">
                  <Input value={existing.masked_key} disabled className="font-mono text-xs" />
                  <Button size="sm" variant="destructive" onClick={() => handleDeleteKey(prov.key)}>
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <div className="relative flex-1">
                    <Input
                      type={showKeys[prov.key] ? 'text' : 'password'}
                      value={newKeys[prov.key] || ''}
                      onChange={(e) => setNewKeys({ ...newKeys, [prov.key]: e.target.value })}
                      placeholder={`Enter ${prov.label} API key`}
                      className="pr-8 font-mono text-xs"
                    />
                    <button
                      type="button"
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground"
                      onClick={() => setShowKeys({ ...showKeys, [prov.key]: !showKeys[prov.key] })}
                    >
                      {showKeys[prov.key] ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                    </button>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => handleSaveKey(prov.key)}
                    disabled={!newKeys[prov.key]}
                  >
                    <Save className="h-3 w-3" />
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
