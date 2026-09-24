'use client'

import { useEffect, useState, type ReactNode } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { Copy, Pencil, RotateCcw, Square, Volume2, X } from 'lucide-react'
import { toast } from 'sonner'
import { iconClass, iconStroke } from '@/lib/icon'
import { useSettingsStore } from '@/store/settingsStore'
import { chatProseSizeClass } from '@/lib/fontSize'
import {
  isSpeechSupported,
  subscribeSpeaking,
  toggleSpeakMessage,
} from '@/lib/textToSpeech'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { MessageLoader } from './MessageLoader'
import { renderMarkdownLink } from './GitHubResourceLink'
import { getAgentLabel } from '@/lib/agents'
import type { Message } from '@/types'

interface Props {
  message: Message
  disabled?: boolean
  onEditResend?: (messageId: string, content: string) => void
}

function isTableSeparator(line: string) {
  return /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(line.trim())
}

function parsePipeTable(text: string): string[][] | null {
  const lines = text
    .trim()
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
  if (lines.length < 2 || !lines.every((line) => line.includes('|'))) return null

  const rows = lines
    .filter((line) => !isTableSeparator(line))
    .map((line) =>
      line
        .replace(/^\|/, '')
        .replace(/\|$/, '')
        .split('|')
        .map((cell) => cell.trim())
    )

  if (rows.length === 0 || rows[0].length < 2) return null
  return rows
}

function extractCodeText(children: ReactNode): string {
  if (typeof children === 'string') return children
  if (Array.isArray(children)) return children.map(extractCodeText).join('')
  if (children && typeof children === 'object' && 'props' in children) {
    const props = (children as { props?: { children?: ReactNode } }).props
    return extractCodeText(props?.children ?? '')
  }
  return ''
}

function MessageTable({ rows }: { rows: string[][] }) {
  const [header, ...body] = rows
  return (
    <div className="my-3 overflow-x-auto">
      <table className="w-full text-app-body text-foreground border-collapse">
        <thead>
          <tr>
            {header.map((cell, index) => (
              <th
                key={`${cell}-${index}`}
                className="px-2 py-1.5 text-left font-medium border-b border-border whitespace-nowrap"
              >
                {cell}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td
                  key={`${rowIndex}-${cellIndex}`}
                  className="px-2 py-1.5 border-b border-border whitespace-nowrap"
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const markdownTableComponents = {
  table: ({ children }: { children?: ReactNode }) => (
    <div className="my-3 overflow-x-auto">
      <table className="w-full text-app-body text-foreground border-collapse">{children}</table>
    </div>
  ),
  th: ({ children }: { children?: ReactNode }) => (
    <th className="px-2 py-1.5 text-left font-medium border-b border-border whitespace-nowrap">
      {children}
    </th>
  ),
  td: ({ children }: { children?: ReactNode }) => (
    <td className="px-2 py-1.5 border-b border-border whitespace-nowrap">{children}</td>
  ),
}

export function MessageBubble({ message, disabled, onEditResend }: Props) {
  const fontSize = useSettingsStore((s) => s.settings.fontSize)
  const proseClass = chatProseSizeClass(fontSize)
  const isUser = message.role === 'user'
  const [isEditing, setIsEditing] = useState(false)
  const [draft, setDraft] = useState(message.content)
  const [isSpeaking, setIsSpeaking] = useState(false)

  useEffect(() => {
    if (isUser) return
    return subscribeSpeaking((activeId) => {
      setIsSpeaking(activeId === message.id)
    })
  }, [isUser, message.id])

  const copy = () => {
    navigator.clipboard.writeText(message.content)
    toast.success('Copied to clipboard')
  }

  const startEdit = () => {
    setDraft(message.content)
    setIsEditing(true)
  }

  const cancelEdit = () => {
    setDraft(message.content)
    setIsEditing(false)
  }

  const submitEdit = () => {
    const text = draft.trim()
    if (!text || !onEditResend) return
    onEditResend(message.id, text)
    setIsEditing(false)
  }

  const handleListen = () => {
    if (!isSpeechSupported()) {
      toast.error('Text-to-speech is not supported on this device')
      return
    }
    const started = toggleSpeakMessage(message.id, message.content)
    if (!started && !isSpeaking) {
      toast.error('Nothing to read aloud')
    }
  }

  if (isUser) {
    return (
      <div className="flex justify-end mb-6 group">
        <div className="max-w-[85%] w-full flex flex-col items-end gap-2">
          {isEditing ? (
            <div className="w-full bg-card border border-border rounded-3xl p-3 space-y-3">
              <Textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                className="min-h-[72px] resize-none border-0 bg-transparent p-0 focus-visible:ring-0 text-app-body"
                autoFocus
                disabled={disabled}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    e.preventDefault()
                    submitEdit()
                  }
                  if (e.key === 'Escape') cancelEdit()
                }}
              />
              <div className="flex items-center justify-end gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={cancelEdit}
                  disabled={disabled}
                  className="h-8 px-3"
                >
                  <X size={14} className="mr-1.5" strokeWidth={iconStroke} />
                  Cancel
                </Button>
                <Button
                  type="button"
                  size="sm"
                  onClick={submitEdit}
                  disabled={disabled || !draft.trim()}
                  className="h-8 px-3"
                >
                  <RotateCcw size={14} className="mr-1.5" strokeWidth={iconStroke} />
                  Send again
                </Button>
              </div>
            </div>
          ) : (
            <>
              <div className="bg-card text-foreground rounded-3xl px-4 py-3 text-app-body leading-relaxed">
                {message.content}
              </div>
              {!disabled && onEditResend && (
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-fast">
                  <button
                    type="button"
                    onClick={copy}
                    className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors duration-fast"
                    aria-label="Copy message"
                  >
                    <Copy size={13} className={iconClass} strokeWidth={iconStroke} />
                  </button>
                  <button
                    type="button"
                    onClick={startEdit}
                    className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors duration-fast"
                    aria-label="Edit message"
                  >
                    <Pencil size={13} className={iconClass} strokeWidth={iconStroke} />
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    )
  }

  const showLoader = message.isStreaming && !message.content.trim()
  const displayContent = message.content
  const agentLabel = getAgentLabel(message.agentName)
  const loaderLabel = 'Thinking'

  return (
    <div className="mb-8 group">
      {agentLabel ? (
        <p className="text-app-caption text-muted-foreground mb-2">{agentLabel}</p>
      ) : null}
      {showLoader ? (
        <MessageLoader label={loaderLabel} />
      ) : (
        <div
          className={`prose prose-neutral dark:prose-invert ${proseClass} max-w-none text-foreground leading-relaxed font-sans
          prose-code:bg-card prose-code:border prose-code:border-border prose-code:rounded prose-code:px-1 prose-code:font-mono prose-code:text-foreground
          prose-pre:bg-card prose-pre:border prose-pre:border-border prose-pre:font-mono prose-pre:text-foreground
          prose-headings:font-rounded prose-headings:font-medium prose-headings:text-foreground
          prose-a:text-foreground prose-a:underline
          prose-blockquote:border-border prose-blockquote:text-muted-foreground
          prose-table:text-foreground prose-th:text-foreground prose-td:text-foreground`}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={{
              ...markdownTableComponents,
              a: ({ href, children }) => renderMarkdownLink(href, children),
              pre: ({ node, children }) => {
                const codeNode = node?.children?.[0]
                const rawText =
                  codeNode &&
                  'children' in codeNode &&
                  codeNode.children?.[0] &&
                  'value' in codeNode.children[0]
                    ? String(codeNode.children[0].value)
                    : extractCodeText(children)
                const rows = parsePipeTable(rawText)
                if (rows) return <MessageTable rows={rows} />
                return (
                  <pre className="overflow-x-auto rounded-lg border border-border bg-card p-3 text-foreground">
                    {children}
                  </pre>
                )
              },
              code: ({ className, children, ...props }) => {
                if (className) {
                  return (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  )
                }
                return (
                  <code className="text-foreground" {...props}>
                    {children}
                  </code>
                )
              },
            }}
          >
            {displayContent || ' '}
          </ReactMarkdown>
          {message.isStreaming && (
            <span className="inline-block w-1.5 h-4 bg-foreground/70 ml-0.5 animate-pulse rounded-sm align-text-bottom" />
          )}
        </div>
      )}

      {message.error && !message.isStreaming && (
        <p className="mt-2 text-app-caption text-destructive">{message.error}</p>
      )}

      {!message.isStreaming && message.content && (
        <div className="flex items-center gap-1 mt-2 opacity-60 group-hover:opacity-100 transition-opacity duration-fast">
          {isSpeechSupported() && (
            <button
              type="button"
              onClick={handleListen}
              className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors duration-fast"
              aria-label={isSpeaking ? 'Stop reading aloud' : 'Read aloud'}
            >
              {isSpeaking ? (
                <Square size={13} className={iconClass} strokeWidth={iconStroke} />
              ) : (
                <Volume2 size={13} className={iconClass} strokeWidth={iconStroke} />
              )}
            </button>
          )}
          <button
            type="button"
            onClick={copy}
            className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors duration-fast"
            aria-label="Copy message"
          >
            <Copy size={13} className={iconClass} strokeWidth={iconStroke} />
          </button>
        </div>
      )}
    </div>
  )
}
