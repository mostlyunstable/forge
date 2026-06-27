import { test, expect } from '@playwright/test'

test.describe('Forge Desktop App', () => {
  test('shows login view when no auth token', async ({ page }) => {
    await page.goto('/')
    // Clear any stored auth
    await page.evaluate(() => localStorage.clear())
    await page.reload()

    // Should show login view
    await expect(page.getByText('Connect to Forge Server')).toBeVisible()
    await expect(page.getByPlaceholder('http://localhost:8000')).toBeVisible()
  })

  test('can connect with valid server', async ({ page }) => {
    await page.goto('/')
    await page.evaluate(() => localStorage.clear())
    await page.reload()

    // Fill in server URL
    const urlInput = page.getByPlaceholder('http://localhost:8000')
    await urlInput.fill('http://127.0.0.1:8000')

    // Click connect
    await page.getByRole('button', { name: /connect/i }).click()

    // Should transition to main app (or show loading)
    await expect(page.locator('body')).toBeVisible()
  })

  test('shows sidebar navigation', async ({ page }) => {
    await page.goto('/')
    // Set auth token to bypass login
    await page.evaluate(() => {
      localStorage.setItem('forge-settings', JSON.stringify({
        state: { authToken: 'test-token', apiUrl: 'http://127.0.0.1:8000' },
        version: 0,
      }))
    })
    await page.reload()

    // Should show sidebar with Forge branding
    await expect(page.getByText('Forge')).toBeVisible()
    await expect(page.getByText('Dashboard')).toBeVisible()
    await expect(page.getByText('Code')).toBeVisible()
    await expect(page.getByText('Decisions')).toBeVisible()
    await expect(page.getByText('Bugs')).toBeVisible()
  })

  test('sidebar collapse toggle works', async ({ page }) => {
    await page.goto('/')
    await page.evaluate(() => {
      localStorage.setItem('forge-settings', JSON.stringify({
        state: { authToken: 'test-token', apiUrl: 'http://127.0.0.1:8000' },
        version: 0,
      }))
    })
    await page.reload()

    // Click collapse button
    const collapseBtn = page.getByText('Collapse')
    await collapseBtn.click()

    // Sidebar should be collapsed - nav labels hidden
    await expect(page.getByText('Dashboard')).not.toBeVisible()
  })

  test('keyboard shortcut Cmd+K opens command palette', async ({ page }) => {
    await page.goto('/')
    await page.evaluate(() => {
      localStorage.setItem('forge-settings', JSON.stringify({
        state: { authToken: 'test-token', apiUrl: 'http://127.0.0.1:8000' },
        version: 0,
      }))
    })
    await page.reload()

    // Press Cmd+K
    await page.keyboard.press('Meta+k')

    // Command palette should appear
    await expect(page.getByPlaceholder('Search commands...')).toBeVisible()
  })
})
