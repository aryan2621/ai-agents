const ONBOARDING_KEY = 'onboarding_v1_complete'

export async function isOnboardingComplete(): Promise<boolean> {
  if (typeof window === 'undefined') return true
  try {
    const { load } = await import('@tauri-apps/plugin-store')
    const store = await load('app.json', { autoSave: true, defaults: {} })
    return Boolean(await store.get<boolean>(ONBOARDING_KEY))
  } catch {
    return localStorage.getItem(ONBOARDING_KEY) === 'true'
  }
}

export async function markOnboardingComplete(): Promise<void> {
  try {
    const { load } = await import('@tauri-apps/plugin-store')
    const store = await load('app.json', { autoSave: true, defaults: {} })
    await store.set(ONBOARDING_KEY, true)
    await store.save()
  } catch {
    localStorage.setItem(ONBOARDING_KEY, 'true')
  }
}

export async function resetOnboarding(): Promise<void> {
  try {
    const { load } = await import('@tauri-apps/plugin-store')
    const store = await load('app.json', { autoSave: true, defaults: {} })
    await store.delete(ONBOARDING_KEY)
    await store.save()
  } catch {
    localStorage.removeItem(ONBOARDING_KEY)
  }
}

export const PRODUCT_TAGLINE =
  'Your private, local AI for GitHub — repos, issues, pull requests, and notifications.'

export const PRODUCT_NAME = 'GitHub Agent'
