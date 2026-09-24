let navigateAfterOAuth = true
const completedOAuthStates = new Set<string>()

export function setOAuthNavigate(navigate: boolean) {
  navigateAfterOAuth = navigate
}

export function shouldNavigateAfterOAuth(): boolean {
  const navigate = navigateAfterOAuth
  navigateAfterOAuth = true
  return navigate
}

export function markOAuthStateComplete(state: string): boolean {
  if (completedOAuthStates.has(state)) return false
  completedOAuthStates.add(state)
  return true
}
