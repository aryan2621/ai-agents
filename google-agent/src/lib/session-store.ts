import { load, Store } from '@tauri-apps/plugin-store'

const ACCESS_TOKEN_KEY = 'auth.accessToken'

let _store: Store | null = null

async function getStore(): Promise<Store> {
  if (!_store) {
    _store = await load('session.json', { autoSave: true, defaults: {} })
  }
  return _store
}

/** Minimal client-side persistence: access token only for session restore. All other data lives in PostgreSQL. */
export const sessionStore = {
  async getAccessToken(): Promise<string | null> {
    try {
      const store = await getStore()
      return (await store.get<string>(ACCESS_TOKEN_KEY)) ?? null
    } catch {
      return null
    }
  },
  async setAccessToken(token: string): Promise<void> {
    const store = await getStore()
    await store.set(ACCESS_TOKEN_KEY, token)
    await store.save()
  },
  async clearAccessToken(): Promise<void> {
    const store = await getStore()
    await store.delete(ACCESS_TOKEN_KEY)
    await store.save()
  },
}
