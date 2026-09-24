import type { AgentName } from '@/types'
import type { RoomAgentName } from '@/lib/agents'

export const STARTER_PROMPTS = [
  {
    id: 'unread-notifications',
    title: 'Unread notifications',
    prompt: 'Summarize my unread GitHub notifications. Highlight anything that needs a reply or review.',
    agent: 'notifications' as const,
  },
  {
    id: 'open-prs',
    title: 'Open pull requests',
    prompt: 'List my open pull requests across repositories I can access and flag anything waiting on me.',
    agent: 'pulls' as const,
  },
  {
    id: 'recent-issues',
    title: 'Recent issues',
    prompt: 'Show recent open issues assigned to me and summarize the most urgent ones.',
    agent: 'issues' as const,
  },
  {
    id: 'repo-summary',
    title: 'Repo overview',
    prompt: 'List my most recently updated repositories and summarize the top 5.',
    agent: 'repos' as const,
  },
] as const

export const ROOM_STARTER_PROMPTS: Record<
  RoomAgentName,
  { id: string; title: string; prompt: string }[]
> = {
  repos: [
    {
      id: 'repo-summary',
      title: 'Recent repos',
      prompt: 'List my most recently updated repositories.',
    },
    {
      id: 'search-python',
      title: 'Python repos',
      prompt: 'Search my repositories for language:python and list the matches.',
    },
    {
      id: 'profile',
      title: 'My profile',
      prompt: 'Show my GitHub profile.',
    },
    {
      id: 'latest-repo',
      title: 'Latest repo details',
      prompt: 'List my recent repositories and show details for the most recently updated one, including the README.',
    },
  ],
  issues: [
    {
      id: 'recent-issues',
      title: 'My issues',
      prompt: 'Show recent open issues assigned to me.',
    },
    {
      id: 'created-issues',
      title: 'Issues I opened',
      prompt: 'Search for open issues I created with is:issue is:open author:@me.',
    },
    {
      id: 'urgent-issues',
      title: 'Needs attention',
      prompt: 'Show open issues assigned to me and summarize the most urgent ones.',
    },
  ],
  pulls: [
    {
      id: 'open-prs',
      title: 'Open PRs',
      prompt: 'List my open pull requests and flag anything waiting on me.',
    },
    {
      id: 'prs-to-review',
      title: 'Review requests',
      prompt: 'Search for open pull requests waiting on my review with is:pr is:open review-requested:@me.',
    },
    {
      id: 'my-authored-prs',
      title: 'PRs I opened',
      prompt: 'List open pull requests I authored across repositories.',
    },
  ],
  code: [
    {
      id: 'recent-commits',
      title: 'Recent commits',
      prompt: 'If an active repo is in this chat, list its recent commits. Otherwise ask which repository to inspect.',
    },
    {
      id: 'readme',
      title: 'Read README',
      prompt: 'If an active repo is in this chat, show the README contents. Otherwise ask which repository to open.',
    },
    {
      id: 'search-todo',
      title: 'Find TODOs',
      prompt: 'If an active repo is in this chat, search its code for TODO. Otherwise ask which repository to search.',
    },
  ],
  notifications: [
    {
      id: 'unread-notifications',
      title: 'Unread',
      prompt: 'Summarize my unread GitHub notifications. Highlight anything that needs a reply or review.',
    },
    {
      id: 'all-notifications',
      title: 'All recent',
      prompt: 'List my recent GitHub notifications, including already-read ones.',
    },
  ],
  web: [
    {
      id: 'web-news',
      title: 'Today in tech',
      prompt: 'Search the web for the top technology news today and summarize with source links.',
    },
    {
      id: 'web-explain',
      title: 'Explain a topic',
      prompt: 'Search the web and explain what a GitHub Actions workflow is, with source links.',
    },
    {
      id: 'web-howto',
      title: 'How-to',
      prompt: 'Search the web for how to write a good GitHub search query and summarize with links.',
    },
  ],
}

export function startersForAgent(agent: AgentName | string | null | undefined) {
  if (!agent || !(agent in ROOM_STARTER_PROMPTS)) return []
  return ROOM_STARTER_PROMPTS[agent as RoomAgentName]
}
