import type { Editor } from '@tiptap/react'
import { useState, useEffect, useCallback, useRef } from 'react'
import { posToDOMRect } from '@tiptap/react'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { Sparkles, ArrowDownToLine, ArrowUpFromLine, Wand2, CheckCheck, RefreshCw } from 'lucide-react'

const AI_ACTIONS = [
  { key: 'improve', label: 'Improve', icon: Wand2 },
  { key: 'shorten', label: 'Shorten', icon: ArrowDownToLine },
  { key: 'expand', label: 'Expand', icon: ArrowUpFromLine },
  { key: 'fix_grammar', label: 'Fix Grammar', icon: CheckCheck },
] as const

interface AiInlineMenuProps {
  editor: Editor
  projectId?: string
  provider?: string
}

export function AiInlineMenu({ editor, projectId, provider = 'anthropic' }: AiInlineMenuProps) {
  const [loading, setLoading] = useState(false)
  const [activeAction, setActiveAction] = useState<string | null>(null)
  const [visible, setVisible] = useState(false)
  const [position, setPosition] = useState({ top: 0, left: 0 })
  const menuRef = useRef<HTMLDivElement>(null)

  const updatePosition = useCallback(() => {
    if (!editor) return
    const { from, to } = editor.state.selection
    const hasSelection = to - from > 3

    if (!hasSelection) {
      setVisible(false)
      return
    }

    setVisible(true)
    const rect = posToDOMRect(editor.view, from, to)
    const editorRect = editor.view.dom.getBoundingClientRect()
    const menuWidth = menuRef.current?.offsetWidth || 300
    setPosition({
      top: rect.top - editorRect.top - 44,
      left: Math.max(0, rect.left - editorRect.left + rect.width / 2 - menuWidth / 2),
    })
  }, [editor])

  useEffect(() => {
    if (!editor) return
    editor.on('selectionUpdate', updatePosition)
    editor.on('blur', () => setVisible(false))
    return () => {
      editor.off('selectionUpdate', updatePosition)
    }
  }, [editor, updatePosition])

  const handleAction = async (action: string) => {
    const { from, to } = editor.state.selection
    const selectedText = editor.state.doc.textBetween(from, to, ' ')
    if (!selectedText || !projectId) return

    setLoading(true)
    setActiveAction(action)

    try {
      let result = ''
      api.streamSSE(
        `/content/ai-inline?project_id=${projectId}&text=${encodeURIComponent(selectedText)}&action=${action}&provider=${provider}`,
        (data) => {
          if (typeof data === 'object' && data !== null && 'chunk' in data) {
            result += (data as { chunk: string }).chunk
          }
        },
        () => {
          if (result) {
            editor.chain().focus().deleteRange({ from, to }).insertContentAt(from, result).run()
          }
          setLoading(false)
          setActiveAction(null)
        }
      )
    } catch {
      setLoading(false)
      setActiveAction(null)
    }
  }

  if (!visible) return null

  return (
    <div
      ref={menuRef}
      className="absolute z-50 flex items-center gap-0.5 rounded-lg border bg-popover p-1 shadow-lg"
      style={{ top: position.top, left: position.left }}
    >
      <div className="flex items-center gap-0.5 px-1 text-xs text-muted-foreground">
        <Sparkles className="h-3 w-3" />
        AI
      </div>
      {AI_ACTIONS.map(({ key, label, icon: Icon }) => (
        <Button
          key={key}
          variant="ghost"
          size="sm"
          className="h-7 px-2 text-xs gap-1"
          onMouseDown={(e) => {
            e.preventDefault()
            handleAction(key)
          }}
          disabled={loading}
        >
          {loading && activeAction === key ? (
            <RefreshCw className="h-3 w-3 animate-spin" />
          ) : (
            <Icon className="h-3 w-3" />
          )}
          {label}
        </Button>
      ))}
    </div>
  )
}
