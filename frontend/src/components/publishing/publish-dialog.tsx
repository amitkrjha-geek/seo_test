import { useState, useEffect, useCallback } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Send, ExternalLink, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import type { PublishingConnection, PublishLog } from '@/lib/types'

interface PublishDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  draftId: string
  projectId: string
}

export function PublishDialog({
  open,
  onOpenChange,
  draftId,
  projectId,
}: PublishDialogProps) {
  const [connections, setConnections] = useState<PublishingConnection[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [publishing, setPublishing] = useState(false)
  const [result, setResult] = useState<PublishLog | null>(null)

  const loadConnections = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.getPublishingConnections(projectId)
      setConnections(data.filter((c) => c.is_active))
    } catch {
      setConnections([])
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    if (open) {
      setResult(null)
      setSelectedId(null)
      loadConnections()
    }
  }, [open, loadConnections])

  const selectedConnection = connections.find((c) => c.id === selectedId)

  const platformLabel = (platform: string) =>
    platform === 'wordpress' ? 'WordPress' : 'Strapi'

  const handlePublish = async () => {
    if (!selectedId) return
    setPublishing(true)
    setResult(null)
    try {
      const log = await api.publishDraft(draftId, selectedId)
      setResult(log)
    } catch {
      setResult({
        id: '',
        draft_id: draftId,
        connection_id: selectedId,
        platform: selectedConnection?.platform || 'wordpress',
        external_id: '',
        external_url: '',
        status: 'failed',
        error_message: 'Publish request failed. Please try again.',
        published_at: new Date().toISOString(),
      })
    } finally {
      setPublishing(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Publish Content</DialogTitle>
          <DialogDescription>
            Choose a CMS connection to publish your content.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-2">
          {loading && (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          )}

          {!loading && connections.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4">
              No active publishing connections found. Add one in Settings first.
            </p>
          )}

          {!loading &&
            connections.map((conn) => (
              <label
                key={conn.id}
                className={`flex items-center gap-3 rounded-lg border p-3 cursor-pointer transition-colors ${
                  selectedId === conn.id
                    ? 'border-primary bg-primary/5'
                    : 'hover:bg-muted/50'
                }`}
              >
                <input
                  type="radio"
                  name="connection"
                  className="sr-only"
                  checked={selectedId === conn.id}
                  onChange={() => {
                    setSelectedId(conn.id)
                    setResult(null)
                  }}
                />
                <div
                  className={`h-4 w-4 rounded-full border-2 flex items-center justify-center shrink-0 ${
                    selectedId === conn.id
                      ? 'border-primary'
                      : 'border-muted-foreground/40'
                  }`}
                >
                  {selectedId === conn.id && (
                    <div className="h-2 w-2 rounded-full bg-primary" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">
                      {platformLabel(conn.platform)}
                    </span>
                    <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                      {conn.platform}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground truncate">
                    {conn.site_url}
                  </p>
                </div>
              </label>
            ))}

          {/* Result display */}
          {result && result.status === 'success' && (
            <div className="rounded-lg border border-green-200 bg-green-50 p-3 dark:border-green-900 dark:bg-green-950">
              <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
                <CheckCircle className="h-4 w-4 shrink-0" />
                <span className="text-sm font-medium">Published successfully</span>
              </div>
              {result.external_url && (
                <a
                  href={result.external_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-flex items-center gap-1 text-xs text-green-700 hover:underline dark:text-green-400"
                >
                  <ExternalLink className="h-3 w-3" />
                  View on {platformLabel(result.platform)}
                </a>
              )}
            </div>
          )}

          {result && result.status === 'failed' && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-900 dark:bg-red-950">
              <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
                <XCircle className="h-4 w-4 shrink-0" />
                <span className="text-sm font-medium">Publishing failed</span>
              </div>
              {result.error_message && (
                <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                  {result.error_message}
                </p>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" size="sm" onClick={() => onOpenChange(false)}>
            {result?.status === 'success' ? 'Done' : 'Cancel'}
          </Button>
          {(!result || result.status === 'failed') && (
            <Button
              size="sm"
              onClick={handlePublish}
              disabled={!selectedId || publishing}
            >
              {publishing ? (
                <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
              ) : (
                <Send className="mr-1.5 h-3.5 w-3.5" />
              )}
              Publish
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
