'use client'

import { SettingsSection } from '../SettingsLayout'
import { ModelManager } from '../ModelManager'

export function ModelsTab() {
  return (
    <div className="space-y-8">
      <SettingsSection
        title="Built-in AI"
        description="The agent rooms run on an open model on this Mac. Download one to start; you can switch any time."
      >
        <ModelManager />
      </SettingsSection>
    </div>
  )
}
