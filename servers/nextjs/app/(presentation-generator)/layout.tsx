import React from 'react'
import { ConfigurationInitializer } from '../ConfigurationInitializer'
import ErrorBoundary from './components/ErrorBoundary'
const layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div>
      <ErrorBoundary>
        <ConfigurationInitializer>
          {children}
        </ConfigurationInitializer>
      </ErrorBoundary>
    </div>
  )
}

export default layout
