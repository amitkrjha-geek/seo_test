import { useState, useEffect, useCallback } from 'react'
import { useProject } from '@/hooks/use-project'
import { api } from '@/lib/api'
import type { CalendarItem, CalendarItemStatus } from '@/lib/types'
import { CalendarItemDialog } from '@/components/calendar/calendar-item-dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, Plus, GripVertical, Trash2 } from 'lucide-react'

// ---------- helpers ----------

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

const DAY_HEADERS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const STATUS_ORDER: CalendarItemStatus[] = ['idea', 'planned', 'writing', 'review', 'scheduled', 'published']

const STATUS_LABELS: Record<CalendarItemStatus, string> = {
  idea: 'Idea',
  planned: 'Planned',
  writing: 'Writing',
  review: 'Review',
  scheduled: 'Scheduled',
  published: 'Published',
}

const STATUS_COLORS: Record<CalendarItemStatus, string> = {
  idea: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  planned: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  writing: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300',
  review: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
  scheduled: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300',
  published: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
}

function getDaysInMonth(year: number, month: number) {
  return new Date(year, month + 1, 0).getDate()
}

/** Return the weekday offset for the first day of the month (0=Mon ... 6=Sun). */
function getFirstDayOffset(year: number, month: number) {
  const day = new Date(year, month, 1).getDay() // 0=Sun ... 6=Sat
  return day === 0 ? 6 : day - 1
}

function formatDate(year: number, month: number, day: number) {
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

function isToday(year: number, month: number, day: number) {
  const now = new Date()
  return now.getFullYear() === year && now.getMonth() === month && now.getDate() === day
}

// ---------- component ----------

type ViewMode = 'month' | 'kanban'

export default function CalendarPage() {
  const { currentProject } = useProject()
  const [items, setItems] = useState<CalendarItem[]>([])
  const [viewMode, setViewMode] = useState<ViewMode>('month')
  const [currentYear, setCurrentYear] = useState(() => new Date().getFullYear())
  const [currentMonth, setCurrentMonth] = useState(() => new Date().getMonth()) // 0-based
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editItem, setEditItem] = useState<CalendarItem | null>(null)
  const [prefilledDate, setPrefilledDate] = useState<string>('')

  const loadItems = useCallback(async () => {
    if (!currentProject) return
    try {
      const data = await api.getCalendarItems(currentProject.id, currentYear, currentMonth + 1)
      setItems(data)
    } catch {
      /* ignore */
    }
  }, [currentProject, currentYear, currentMonth])

  useEffect(() => {
    loadItems()
  }, [loadItems])

  function prevMonth() {
    if (currentMonth === 0) {
      setCurrentMonth(11)
      setCurrentYear((y) => y - 1)
    } else {
      setCurrentMonth((m) => m - 1)
    }
  }

  function nextMonth() {
    if (currentMonth === 11) {
      setCurrentMonth(0)
      setCurrentYear((y) => y + 1)
    } else {
      setCurrentMonth((m) => m + 1)
    }
  }

  function openCreate(date?: string) {
    setEditItem(null)
    setPrefilledDate(date || '')
    setDialogOpen(true)
  }

  function openEdit(item: CalendarItem) {
    setEditItem(item)
    setPrefilledDate('')
    setDialogOpen(true)
  }

  // ---------- drag-and-drop handlers (month view: reschedule) ----------

  function onDragStartItem(e: React.DragEvent, item: CalendarItem) {
    e.dataTransfer.setData('calendar-item-id', item.id)
    e.dataTransfer.setData('drag-source', 'month')
    e.dataTransfer.effectAllowed = 'move'
  }

  async function onDropOnDay(e: React.DragEvent, dateStr: string) {
    e.preventDefault()
    const itemId = e.dataTransfer.getData('calendar-item-id')
    if (!itemId) return
    try {
      await api.rescheduleCalendarItem(itemId, dateStr)
      loadItems()
    } catch {
      /* ignore */
    }
  }

  function onDragOver(e: React.DragEvent) {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  // ---------- drag-and-drop handlers (kanban view: change status) ----------

  function onDragStartKanban(e: React.DragEvent, item: CalendarItem) {
    e.dataTransfer.setData('calendar-item-id', item.id)
    e.dataTransfer.setData('drag-source', 'kanban')
    e.dataTransfer.effectAllowed = 'move'
  }

  async function onDropOnColumn(e: React.DragEvent, newStatus: CalendarItemStatus) {
    e.preventDefault()
    const itemId = e.dataTransfer.getData('calendar-item-id')
    if (!itemId) return
    try {
      await api.updateCalendarItem(itemId, { status: newStatus })
      loadItems()
    } catch {
      /* ignore */
    }
  }

  // ---------- render ----------

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Select a project to view the calendar</p>
      </div>
    )
  }

  // Build the grid cells for the month view
  const daysInMonth = getDaysInMonth(currentYear, currentMonth)
  const firstDayOffset = getFirstDayOffset(currentYear, currentMonth)
  const totalCells = firstDayOffset + daysInMonth
  const rows = Math.ceil(totalCells / 7)

  // Index items by date string for quick lookup
  const itemsByDate: Record<string, CalendarItem[]> = {}
  for (const it of items) {
    if (it.scheduled_date) {
      if (!itemsByDate[it.scheduled_date]) itemsByDate[it.scheduled_date] = []
      itemsByDate[it.scheduled_date].push(it)
    }
  }

  // Kanban: group items by status
  const itemsByStatus: Record<CalendarItemStatus, CalendarItem[]> = {
    idea: [], planned: [], writing: [], review: [], scheduled: [], published: [],
  }
  for (const it of items) {
    itemsByStatus[it.status].push(it)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <CalendarIcon className="h-6 w-6 text-muted-foreground" />
          <h1 className="text-2xl font-bold">Content Calendar</h1>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {/* View toggle */}
          <div className="flex border rounded-md overflow-hidden">
            <button
              className={`px-3 py-1.5 text-sm font-medium transition-colors ${viewMode === 'month' ? 'bg-primary text-primary-foreground' : 'bg-background hover:bg-accent'}`}
              onClick={() => setViewMode('month')}
            >
              Month
            </button>
            <button
              className={`px-3 py-1.5 text-sm font-medium transition-colors ${viewMode === 'kanban' ? 'bg-primary text-primary-foreground' : 'bg-background hover:bg-accent'}`}
              onClick={() => setViewMode('kanban')}
            >
              Kanban
            </button>
          </div>

          {/* Month navigation */}
          <div className="flex items-center gap-1">
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={prevMonth}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm font-medium min-w-[140px] text-center">
              {MONTH_NAMES[currentMonth]} {currentYear}
            </span>
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={nextMonth}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>

          <Button size="sm" onClick={() => openCreate()}>
            <Plus className="h-4 w-4 mr-1" /> Add Item
          </Button>
        </div>
      </div>

      {/* Month Grid View */}
      {viewMode === 'month' && (
        <div className="border rounded-lg overflow-hidden">
          {/* Day headers */}
          <div className="grid grid-cols-7 bg-muted/50">
            {DAY_HEADERS.map((d) => (
              <div key={d} className="px-2 py-2 text-xs font-medium text-muted-foreground text-center border-b">
                {d}
              </div>
            ))}
          </div>

          {/* Day cells */}
          <div className="grid grid-cols-7">
            {Array.from({ length: rows * 7 }, (_, i) => {
              const dayNum = i - firstDayOffset + 1
              const isValid = dayNum >= 1 && dayNum <= daysInMonth
              const dateStr = isValid ? formatDate(currentYear, currentMonth, dayNum) : ''
              const dayItems = isValid ? (itemsByDate[dateStr] || []) : []
              const today = isValid && isToday(currentYear, currentMonth, dayNum)

              return (
                <div
                  key={i}
                  className={`min-h-[100px] border-b border-r p-1 transition-colors ${isValid ? 'bg-background hover:bg-accent/30' : 'bg-muted/20'} ${today ? 'ring-2 ring-inset ring-primary/30' : ''}`}
                  onDragOver={isValid ? onDragOver : undefined}
                  onDrop={isValid ? (e) => onDropOnDay(e, dateStr) : undefined}
                  onDoubleClick={isValid ? () => openCreate(dateStr) : undefined}
                >
                  {isValid && (
                    <>
                      <div className={`text-xs font-medium px-1 mb-1 ${today ? 'text-primary font-bold' : 'text-muted-foreground'}`}>
                        {dayNum}
                      </div>
                      <div className="space-y-0.5">
                        {dayItems.map((it) => (
                          <div
                            key={it.id}
                            draggable
                            onDragStart={(e) => onDragStartItem(e, it)}
                            onClick={() => openEdit(it)}
                            className={`text-[11px] leading-tight px-1.5 py-0.5 rounded cursor-pointer truncate ${STATUS_COLORS[it.status]}`}
                            title={it.title}
                          >
                            {it.title}
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Kanban View */}
      {viewMode === 'kanban' && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {STATUS_ORDER.map((st) => (
            <div
              key={st}
              className="flex flex-col"
              onDragOver={onDragOver}
              onDrop={(e) => onDropOnColumn(e, st)}
            >
              <div className={`rounded-t-lg px-3 py-2 text-sm font-semibold ${STATUS_COLORS[st]}`}>
                {STATUS_LABELS[st]}
                <span className="ml-1 opacity-60">({itemsByStatus[st].length})</span>
              </div>
              <div className="flex-1 border border-t-0 rounded-b-lg p-2 space-y-2 min-h-[200px] bg-muted/20">
                {itemsByStatus[st].map((it) => (
                  <Card
                    key={it.id}
                    draggable
                    onDragStart={(e) => onDragStartKanban(e, it)}
                    onClick={() => openEdit(it)}
                    className="cursor-pointer hover:shadow-md transition-shadow"
                  >
                    <CardContent className="p-3 space-y-1.5">
                      <div className="flex items-start gap-1">
                        <GripVertical className="h-3.5 w-3.5 mt-0.5 text-muted-foreground/50 flex-shrink-0" />
                        <p className="text-sm font-medium leading-tight line-clamp-2">{it.title}</p>
                      </div>
                      {it.target_keyword && (
                        <Badge variant="outline" className="text-[10px]">
                          {it.target_keyword}
                        </Badge>
                      )}
                      {it.scheduled_date && (
                        <p className="text-[11px] text-muted-foreground">
                          {new Date(it.scheduled_date + 'T00:00:00').toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                          })}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                ))}
                {itemsByStatus[st].length === 0 && (
                  <p className="text-xs text-muted-foreground text-center py-6">No items</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Items without a date (shown below when in month view) */}
      {viewMode === 'month' && items.filter((it) => !it.scheduled_date).length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Unscheduled Items
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="flex flex-wrap gap-2">
              {items
                .filter((it) => !it.scheduled_date)
                .map((it) => (
                  <div
                    key={it.id}
                    draggable
                    onDragStart={(e) => onDragStartItem(e, it)}
                    onClick={() => openEdit(it)}
                    className={`text-xs px-2 py-1 rounded cursor-pointer ${STATUS_COLORS[it.status]}`}
                  >
                    {it.title}
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Dialog */}
      <CalendarItemDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        item={editItem}
        projectId={currentProject.id}
        onSave={loadItems}
      />
    </div>
  )
}
