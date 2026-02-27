import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import type { CalendarItem, CalendarItemStatus } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Trash2 } from 'lucide-react'

const STATUSES: { value: CalendarItemStatus; label: string }[] = [
  { value: 'idea', label: 'Idea' },
  { value: 'planned', label: 'Planned' },
  { value: 'writing', label: 'Writing' },
  { value: 'review', label: 'Review' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'published', label: 'Published' },
]

interface CalendarItemDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  item?: CalendarItem | null
  projectId: string
  onSave: () => void
}

export function CalendarItemDialog({
  open,
  onOpenChange,
  item,
  projectId,
  onSave,
}: CalendarItemDialogProps) {
  const [title, setTitle] = useState('')
  const [targetKeyword, setTargetKeyword] = useState('')
  const [scheduledDate, setScheduledDate] = useState('')
  const [status, setStatus] = useState<CalendarItemStatus>('idea')
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) {
      if (item) {
        setTitle(item.title)
        setTargetKeyword(item.target_keyword || '')
        setScheduledDate(item.scheduled_date || '')
        setStatus(item.status)
        setNotes(item.notes || '')
      } else {
        setTitle('')
        setTargetKeyword('')
        setScheduledDate('')
        setStatus('idea')
        setNotes('')
      }
    }
  }, [open, item])

  async function handleSave() {
    if (!title.trim()) return
    setSaving(true)
    try {
      if (item) {
        await api.updateCalendarItem(item.id, {
          title,
          target_keyword: targetKeyword,
          scheduled_date: scheduledDate || null,
          status,
          notes,
        })
      } else {
        await api.createCalendarItem({
          project_id: projectId,
          title,
          target_keyword: targetKeyword,
          scheduled_date: scheduledDate || null,
          status,
          notes,
        })
      }
      onSave()
      onOpenChange(false)
    } catch {
      /* ignore */
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!item) return
    setSaving(true)
    try {
      await api.deleteCalendarItem(item.id)
      onSave()
      onOpenChange(false)
    } catch {
      /* ignore */
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{item ? 'Edit Calendar Item' : 'New Calendar Item'}</DialogTitle>
          <DialogDescription>
            {item ? 'Update the details for this calendar item.' : 'Add a new item to the content calendar.'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="cal-title">Title</Label>
            <Input
              id="cal-title"
              placeholder="Article title..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="cal-keyword">Target Keyword</Label>
            <Input
              id="cal-keyword"
              placeholder="e.g. best seo tools"
              value={targetKeyword}
              onChange={(e) => setTargetKeyword(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="cal-date">Scheduled Date</Label>
              <Input
                id="cal-date"
                type="date"
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Status</Label>
              <Select value={status} onValueChange={(v) => setStatus(v as CalendarItemStatus)}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STATUSES.map((s) => (
                    <SelectItem key={s.value} value={s.value}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="cal-notes">Notes</Label>
            <Textarea
              id="cal-notes"
              placeholder="Additional notes..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
            />
          </div>
        </div>

        <DialogFooter className="flex-row justify-between sm:justify-between">
          {item && (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleDelete}
              disabled={saving}
            >
              <Trash2 className="h-4 w-4 mr-1" />
              Delete
            </Button>
          )}
          <div className="flex gap-2 ml-auto">
            <Button variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving || !title.trim()}>
              {saving ? 'Saving...' : item ? 'Update' : 'Create'}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
