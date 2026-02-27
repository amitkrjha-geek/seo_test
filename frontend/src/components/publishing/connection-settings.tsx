import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Globe, Trash2, CheckCircle, XCircle, Plus, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import type { PublishingConnection, PublishingPlatform } from '@/lib/types'

interface ConnectionSettingsProps {
  projectId: string
}

export function ConnectionSettings({ projectId }: ConnectionSettingsProps) {
  const [connections, setConnections] = useState<PublishingConnection[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testingId, setTestingId] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<{ id: string; success: boolean; message: string } | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  // Form state
  const [platform, setPlatform] = useState<PublishingPlatform>('wordpress')
  const [siteUrl, setSiteUrl] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [token, setToken] = useState('')

  const loadConnections = useCallback(async () => {
    try {
      const data = await api.getPublishingConnections(projectId)
      setConnections(data)
    } catch {
      // silently fail
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    loadConnections()
  }, [loadConnections])

  const resetForm = () => {
    setPlatform('wordpress')
    setSiteUrl('')
    setUsername('')
    setPassword('')
    setToken('')
    setShowForm(false)
  }

  const handleSave = async () => {
    if (!siteUrl.trim()) return
    setSaving(true)
    try {
      await api.createPublishingConnection({
        project_id: projectId,
        platform,
        site_url: siteUrl.trim(),
        ...(platform === 'wordpress'
          ? { username: username.trim(), password: password.trim() }
          : { token: token.trim() }),
      })
      resetForm()
      await loadConnections()
    } catch {
      // handled by api client
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async (id: string) => {
    setTestingId(id)
    setTestResult(null)
    try {
      const result = await api.testPublishingConnection(id)
      setTestResult({ id, success: result.success, message: result.message })
      await loadConnections()
    } catch {
      setTestResult({ id, success: false, message: 'Test request failed' })
    } finally {
      setTestingId(null)
    }
  }

  const handleDelete = async (id: string) => {
    setDeletingId(id)
    try {
      await api.deletePublishingConnection(id)
      setConnections((prev) => prev.filter((c) => c.id !== id))
      if (testResult?.id === id) setTestResult(null)
    } catch {
      // handled by api client
    } finally {
      setDeletingId(null)
    }
  }

  const platformLabel = (p: PublishingPlatform) =>
    p === 'wordpress' ? 'WordPress' : 'Strapi'

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">Publishing Connections</CardTitle>
            <CardDescription>
              Connect to WordPress or Strapi to publish content directly.
            </CardDescription>
          </div>
          {!showForm && (
            <Button size="sm" variant="outline" onClick={() => setShowForm(true)}>
              <Plus className="mr-1.5 h-3.5 w-3.5" />
              Add Connection
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Existing connections */}
        {connections.length === 0 && !showForm && (
          <p className="text-sm text-muted-foreground text-center py-4">
            No publishing connections configured yet.
          </p>
        )}

        {connections.map((conn) => (
          <div
            key={conn.id}
            className="flex items-center justify-between rounded-lg border p-3"
          >
            <div className="flex items-center gap-3 min-w-0">
              <Globe className="h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">
                    {platformLabel(conn.platform)}
                  </span>
                  <Badge
                    variant={conn.is_active ? 'default' : 'secondary'}
                    className="text-[10px] px-1.5 py-0"
                  >
                    {conn.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground truncate">
                  {conn.site_url}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1.5 shrink-0">
              {testResult?.id === conn.id && (
                <span
                  className={`flex items-center gap-1 text-xs ${
                    testResult.success ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {testResult.success ? (
                    <CheckCircle className="h-3.5 w-3.5" />
                  ) : (
                    <XCircle className="h-3.5 w-3.5" />
                  )}
                  <span className="max-w-[140px] truncate">{testResult.message}</span>
                </span>
              )}
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleTest(conn.id)}
                disabled={testingId === conn.id}
              >
                {testingId === conn.id ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  'Test'
                )}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="text-destructive hover:text-destructive"
                onClick={() => handleDelete(conn.id)}
                disabled={deletingId === conn.id}
              >
                {deletingId === conn.id ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Trash2 className="h-3.5 w-3.5" />
                )}
              </Button>
            </div>
          </div>
        ))}

        {/* Add connection form */}
        {showForm && (
          <div className="rounded-lg border p-4 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="pub-platform">Platform</Label>
              <Select
                value={platform}
                onValueChange={(val) => setPlatform(val as PublishingPlatform)}
              >
                <SelectTrigger id="pub-platform" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="wordpress">WordPress</SelectItem>
                  <SelectItem value="strapi">Strapi</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="pub-site-url">Site URL</Label>
              <Input
                id="pub-site-url"
                placeholder={
                  platform === 'wordpress'
                    ? 'https://yourblog.com'
                    : 'https://cms.example.com'
                }
                value={siteUrl}
                onChange={(e) => setSiteUrl(e.target.value)}
              />
            </div>

            {platform === 'wordpress' && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="pub-username">Username</Label>
                  <Input
                    id="pub-username"
                    placeholder="admin"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="pub-password">Application Password</Label>
                  <Input
                    id="pub-password"
                    type="password"
                    placeholder="xxxx xxxx xxxx xxxx xxxx xxxx"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Generate an Application Password in WordPress under Users &rarr; Profile &rarr; Application Passwords.
                  </p>
                </div>
              </>
            )}

            {platform === 'strapi' && (
              <div className="space-y-2">
                <Label htmlFor="pub-token">API Token</Label>
                <Input
                  id="pub-token"
                  type="password"
                  placeholder="Bearer token from Strapi admin"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Create an API token in Strapi under Settings &rarr; API Tokens.
                </p>
              </div>
            )}

            <div className="flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={resetForm}>
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleSave}
                disabled={
                  saving ||
                  !siteUrl.trim() ||
                  (platform === 'wordpress' && (!username.trim() || !password.trim())) ||
                  (platform === 'strapi' && !token.trim())
                }
              >
                {saving && <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />}
                Save Connection
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
