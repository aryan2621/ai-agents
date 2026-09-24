import type { AgentName } from '@/types'
import type { RoomAgentName } from '@/lib/agents'

export const STARTER_PROMPTS = [
  {
    id: 'unread-summary',
    title: 'Summarize unread emails',
    prompt: 'Summarize my unread emails from today. Highlight anything urgent or needing a reply.',
    agent: 'gmail' as const,
  },
  {
    id: 'free-slot',
    title: 'Find a meeting slot',
    prompt:
      'Find my next free 30-minute slot this week and draft a meeting invite for a team sync.',
    agent: 'calendar' as const,
  },
  {
    id: 'drive-search',
    title: 'Search Drive',
    prompt: 'Search my Google Drive for recent spreadsheets and list the 5 most recently modified.',
    agent: 'drive' as const,
  },
  {
    id: 'week-ahead',
    title: 'Week ahead preview',
    prompt: 'What does my calendar look like for the rest of this week? Flag any conflicts.',
    agent: 'calendar' as const,
  },
  {
    id: 'draft-reply',
    title: 'Draft an email reply',
    prompt: 'Find my most recent unread email and draft a polite reply I can review before sending.',
    agent: 'gmail' as const,
  },
] as const

export const ROOM_STARTER_PROMPTS: Record<
  RoomAgentName,
  { id: string; title: string; prompt: string }[]
> = {
  gmail: [
    {
      id: 'unread-summary',
      title: 'Summarize unread',
      prompt: 'Summarize my unread emails from today. Highlight anything urgent or needing a reply.',
    },
    {
      id: 'inbox-today',
      title: 'Today’s inbox',
      prompt: 'List my inbox emails from today with subject, sender, and a one-line takeaway.',
    },
    {
      id: 'draft-reply',
      title: 'Draft a reply',
      prompt: 'Find my most recent unread email and draft a polite reply I can review before sending.',
    },
    {
      id: 'search-receipts',
      title: 'Find receipts',
      prompt: 'Search my email for receipts or invoices from the last 30 days and list the matches.',
    },
    {
      id: 'draft-self',
      title: 'Draft to myself',
      prompt: 'Create a Gmail draft to myself with subject Weekly recap and a short outline I can edit.',
    },
    {
      id: 'list-labels',
      title: 'List labels',
      prompt: 'List my Gmail labels and say which ones look like they are for work vs personal.',
    },
  ],
  calendar: [
    {
      id: 'today-agenda',
      title: 'Today’s agenda',
      prompt: 'What is on my calendar today? List each event with time and location.',
    },
    {
      id: 'week-ahead',
      title: 'Week ahead',
      prompt: 'What does my calendar look like for the rest of this week? Flag any conflicts.',
    },
    {
      id: 'free-slot',
      title: 'Find a free slot',
      prompt: 'Find my next free 30-minute slot this week.',
    },
    {
      id: 'search-syncs',
      title: 'Find standups',
      prompt: 'Search my calendar for events named standup, sync, or 1:1 and list the upcoming ones.',
    },
    {
      id: 'focus-block',
      title: 'Block focus time',
      prompt: 'Create a 30-minute calendar event tomorrow at 3:00 PM titled Deep work.',
    },
    {
      id: 'tomorrow',
      title: 'Tomorrow',
      prompt: 'Show my calendar for tomorrow and note any back-to-back meetings.',
    },
  ],
  drive: [
    {
      id: 'drive-recent',
      title: 'Recent files',
      prompt: 'List my most recently modified Drive files with name and link.',
    },
    {
      id: 'drive-shared',
      title: 'Shared with me',
      prompt: 'List files recently shared with me and who they came from if available.',
    },
    {
      id: 'drive-search-sheets',
      title: 'Find spreadsheets',
      prompt: 'Search my Drive for spreadsheets and list the most recent matches.',
    },
    {
      id: 'drive-root',
      title: 'My Drive folder',
      prompt: 'List the files and folders at the top level of My Drive.',
    },
    {
      id: 'drive-pdfs',
      title: 'Find PDFs',
      prompt: 'Search my Drive for PDF files and list the most recently modified ones.',
    },
    {
      id: 'drive-folder',
      title: 'New folder',
      prompt: 'Create a Drive folder named Scratch and confirm with the link.',
    },
  ],
  docs: [
    {
      id: 'list-docs',
      title: 'Recent docs',
      prompt: 'List my most recently modified Google Docs.',
    },
    {
      id: 'search-docs',
      title: 'Search docs',
      prompt: 'Search my Google Docs for anything with notes in the title and list the matches.',
    },
    {
      id: 'read-latest-doc',
      title: 'Read latest',
      prompt: 'List my recent Docs and show the text of the most recently modified one.',
    },
    {
      id: 'create-notes',
      title: 'Meeting notes',
      prompt: 'Create a Google Doc titled Meeting notes and add today’s date as the first line.',
    },
    {
      id: 'create-outline',
      title: 'New outline',
      prompt: 'Create a Google Doc titled Project outline with headings Goal, Timeline, and Next steps.',
    },
    {
      id: 'append-latest',
      title: 'Add a note',
      prompt: 'Find my most recently modified Google Doc and append a short “Follow-up” section at the end.',
    },
  ],
  sheets: [
    {
      id: 'list-sheets',
      title: 'Recent sheets',
      prompt: 'List my most recently modified Google Sheets.',
    },
    {
      id: 'search-sheets',
      title: 'Search sheets',
      prompt: 'Search my spreadsheets for anything with tracker or budget in the title.',
    },
    {
      id: 'read-latest-sheet',
      title: 'Read latest',
      prompt: 'List my recent Sheets and summarize the first page of the most recently modified one.',
    },
    {
      id: 'habit-tracker',
      title: 'Habit tracker',
      prompt:
        'Create a spreadsheet titled Habit tracker with headers Date, Habit, Done and three example rows.',
    },
    {
      id: 'expense-log',
      title: 'Expense log',
      prompt:
        'Create a spreadsheet titled Expenses with headers Date, Item, Category, Amount and two example rows.',
    },
    {
      id: 'append-row',
      title: 'Add a row',
      prompt:
        'Find my most recently modified spreadsheet and append one example row that matches its headers.',
    },
  ],
  web: [
    {
      id: 'web-news',
      title: 'Today in tech',
      prompt: 'Search the web for the top technology news today and summarize with source links.',
    },
    {
      id: 'web-weather',
      title: 'Weather today',
      prompt: 'Search the web for today’s weather in New Delhi and cite the source.',
    },
    {
      id: 'web-explain',
      title: 'Explain a topic',
      prompt: 'Search the web and explain what an MCP server is, with source links.',
    },
    {
      id: 'web-compare',
      title: 'Compare tools',
      prompt: 'Search the web and compare Notion vs Google Docs for team notes. Cite sources.',
    },
    {
      id: 'web-howto',
      title: 'How-to',
      prompt: 'Search the web for how to write a good Gmail search query and summarize with links.',
    },
    {
      id: 'web-headlines',
      title: 'World headlines',
      prompt: 'Search the web for today’s top world news headlines and list them with source links.',
    },
  ],
}

export function startersForAgent(agent: AgentName | string | null | undefined) {
  if (!agent || !(agent in ROOM_STARTER_PROMPTS)) return []
  return ROOM_STARTER_PROMPTS[agent as RoomAgentName]
}
