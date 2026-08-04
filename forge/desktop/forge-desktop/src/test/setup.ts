import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach } from 'vitest'
import 'whatwg-fetch'

afterEach(() => {
  cleanup()
})

// Reset module-level state between tests
beforeEach(() => {
  // Clear localStorage
  localStorage.clear()
})
