import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'
import Highlight from '@tiptap/extension-highlight'
import Typography from '@tiptap/extension-typography'
import Link from '@tiptap/extension-link'
import Image from '@tiptap/extension-image'
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight'
import { common, createLowlight } from 'lowlight'
import { EditorToolbar } from './editor-toolbar'
import { AiInlineMenu } from './ai-inline-menu'
import { useEffect, useImperativeHandle, forwardRef } from 'react'

const lowlight = createLowlight(common)

export interface TiptapEditorProps {
  content?: string
  onUpdate?: (html: string, text: string) => void
  editable?: boolean
  placeholder?: string
  projectId?: string
  provider?: string
  className?: string
}

export interface TiptapEditorRef {
  getHTML: () => string
  getText: () => string
  insertContent: (content: string) => void
  setContent: (content: string) => void
  clear: () => void
  focus: () => void
}

export const TiptapEditor = forwardRef<TiptapEditorRef, TiptapEditorProps>(
  ({ content = '', onUpdate, editable = true, placeholder = 'Start writing...', projectId, provider, className }, ref) => {
    const editor = useEditor({
      extensions: [
        StarterKit.configure({
          codeBlock: false,
          heading: { levels: [1, 2, 3, 4] },
        }),
        Placeholder.configure({ placeholder }),
        Underline,
        TextAlign.configure({ types: ['heading', 'paragraph'] }),
        Highlight.configure({ multicolor: true }),
        Typography,
        Link.configure({ openOnClick: false, autolink: true }),
        Image.configure({ inline: false, allowBase64: true }),
        CodeBlockLowlight.configure({ lowlight }),
      ],
      content,
      editable,
      onUpdate: ({ editor: ed }) => {
        onUpdate?.(ed.getHTML(), ed.getText())
      },
      editorProps: {
        attributes: {
          class: 'prose prose-sm max-w-none focus:outline-none min-h-[400px] px-4 py-3',
        },
      },
    })

    useEffect(() => {
      if (editor && content && editor.getHTML() !== content && !editor.isFocused) {
        editor.commands.setContent(content, false)
      }
    }, [content, editor])

    useImperativeHandle(ref, () => ({
      getHTML: () => editor?.getHTML() || '',
      getText: () => editor?.getText() || '',
      insertContent: (c: string) => editor?.commands.insertContent(c),
      setContent: (c: string) => editor?.commands.setContent(c),
      clear: () => editor?.commands.clearContent(),
      focus: () => editor?.commands.focus(),
    }), [editor])

    if (!editor) return null

    return (
      <div className={`border rounded-lg overflow-hidden bg-background ${className || ''}`}>
        <EditorToolbar editor={editor} />
        <div className="relative">
          <AiInlineMenu editor={editor} projectId={projectId} provider={provider} />
          <EditorContent editor={editor} />
        </div>
      </div>
    )
  }
)

TiptapEditor.displayName = 'TiptapEditor'
