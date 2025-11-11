/**
 * Tests for Accessibility Utilities
 * Ensures all a11y helper functions work correctly
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  runAxeTest,
  testKeyboardNavigation,
  testScreenReaderLabels,
  testColorContrast,
  testFocusTrap,
  testSkipLink,
  testFormAccessibility,
  categorizeViolations,
  axeConfigs,
  A11ySeverity,
  defaultAxeConfig,
} from './a11y'

describe('Accessibility Utilities', () => {
  describe('runAxeTest', () => {
    it('should run axe tests on accessible component', async () => {
      const { container } = render(
        <div>
          <button>Click me</button>
        </div>
      )

      const results = await runAxeTest(container)
      expect(results).toHaveNoViolations()
    })

    it('should detect accessibility violations', async () => {
      const { container } = render(
        <div>
          {/* Button without accessible name */}
          <button></button>
        </div>
      )

      const results = await runAxeTest(container)
      expect(results.violations.length).toBeGreaterThan(0)
    })

    it('should accept custom axe configuration', async () => {
      const { container } = render(
        <div>
          <button>Test</button>
        </div>
      )

      const customConfig = {
        rules: {
          'button-name': { enabled: true },
        },
      }

      const results = await runAxeTest(container, customConfig)
      expect(results).toBeDefined()
    })
  })

  describe('testKeyboardNavigation', () => {
    it('should tab through focusable elements', async () => {
      const { container, getByRole, getAllByRole, queryByRole } = render(
        <div>
          <button>Button 1</button>
          <button>Button 2</button>
          <input type="text" aria-label="Input" />
        </div>
      )

      const nav = testKeyboardNavigation({ container, getByRole, getAllByRole, queryByRole })
      const elements = await nav.tabThroughElements()

      expect(elements.length).toBe(3)
    })

    it('should get currently focused element', async () => {
      const { container, getByRole, getAllByRole, queryByRole } = render(
        <div>
          <button>Focus me</button>
        </div>
      )

      const button = getByRole('button')
      button.focus()

      const nav = testKeyboardNavigation({ container, getByRole, getAllByRole, queryByRole })
      expect(nav.getFocusedElement()).toBe(button)
    })

    it('should press Enter key', async () => {
      const handleClick = jest.fn()
      const { container, getByRole, getAllByRole, queryByRole } = render(
        <button onClick={handleClick}>Click me</button>
      )

      const button = getByRole('button')
      button.focus()

      const nav = testKeyboardNavigation({ container, getByRole, getAllByRole, queryByRole })
      await nav.pressEnter()

      expect(handleClick).toHaveBeenCalled()
    })

    it('should press Space key', async () => {
      const handleClick = jest.fn()
      const { container, getByRole, getAllByRole, queryByRole } = render(
        <button onClick={handleClick}>Click me</button>
      )

      const button = getByRole('button')
      button.focus()

      const nav = testKeyboardNavigation({ container, getByRole, getAllByRole, queryByRole })
      await nav.pressSpace()

      expect(handleClick).toHaveBeenCalled()
    })

    it('should press Escape key', async () => {
      const { container, getByRole, getAllByRole, queryByRole } = render(
        <div>
          <button>Test</button>
        </div>
      )

      const nav = testKeyboardNavigation({ container, getByRole, getAllByRole, queryByRole })

      // Should execute without errors
      await nav.pressEscape()
      expect(true).toBe(true)
    })

    it('should navigate with arrow keys', async () => {
      const { container, getByRole, getAllByRole, queryByRole } = render(
        <div>
          <button>Test</button>
        </div>
      )

      const nav = testKeyboardNavigation({ container, getByRole, getAllByRole, queryByRole })

      await nav.pressArrowDown()
      await nav.pressArrowUp()
      await nav.pressArrowLeft()
      await nav.pressArrowRight()

      // Should execute without errors
      expect(true).toBe(true)
    })

    it('should verify focusable elements', () => {
      const { container, getByRole, getAllByRole, queryByRole } = render(
        <div>
          <button>Button 1</button>
          <button>Button 2</button>
        </div>
      )

      const nav = testKeyboardNavigation(
        { container, getByRole, getAllByRole, queryByRole },
        ['button', 'button']
      )

      expect(nav.verifyFocusableElements()).toBe(true)
    })
  })

  describe('testScreenReaderLabels', () => {
    it('should verify button has accessible name', () => {
      const { container, getByRole, getByLabelText, queryByRole } = render(
        <button>Submit Form</button>
      )

      const aria = testScreenReaderLabels({ container, getByRole, getByLabelText, queryByRole })
      const button = aria.verifyButtonHasLabel('Submit Form')

      expect(button).toBeInTheDocument()
      expect(button).toHaveAccessibleName('Submit Form')
    })

    it('should verify input has label', () => {
      const { container, getByRole, getByLabelText, queryByRole } = render(
        <div>
          <label htmlFor="email-input">Email Address</label>
          <input id="email-input" type="email" />
        </div>
      )

      const aria = testScreenReaderLabels({ container, getByRole, getByLabelText, queryByRole })
      const input = aria.verifyInputHasLabel('Email Address', 'email-input')

      expect(input).toBeInTheDocument()
      expect(input).toHaveAttribute('id', 'email-input')
    })

    it('should verify ARIA attributes', () => {
      const { container, getByRole, getByLabelText, queryByRole } = render(
        <div role="alert" aria-live="assertive" aria-atomic="true">
          Error message
        </div>
      )

      const element = getByRole('alert')
      const aria = testScreenReaderLabels({ container, getByRole, getByLabelText, queryByRole })

      aria.verifyAriaAttributes(element, {
        'aria-live': 'assertive',
        'aria-atomic': 'true',
        role: 'alert',
      })

      expect(element).toHaveAttribute('role', 'alert')
    })

    it('should verify landmarks are present', () => {
      const { container, getByRole, getByLabelText, queryByRole } = render(
        <div>
          <nav>Navigation</nav>
          <main>Main content</main>
          <footer>Footer</footer>
        </div>
      )

      const aria = testScreenReaderLabels({ container, getByRole, getByLabelText, queryByRole })
      const landmarks = aria.verifyLandmarks()

      expect(landmarks.hasNavigation).toBe(true)
      expect(landmarks.hasMain).toBe(true)
      expect(landmarks.hasFooter).toBe(true)
    })

    it('should verify heading hierarchy', () => {
      const { container, getByRole, getByLabelText, queryByRole } = render(
        <div>
          <h1>Main Title</h1>
          <h2>Section Title</h2>
          <h3>Subsection</h3>
        </div>
      )

      const aria = testScreenReaderLabels({ container, getByRole, getByLabelText, queryByRole })
      const hierarchy = aria.verifyHeadingHierarchy()

      expect(hierarchy.isValid).toBe(true)
      expect(hierarchy.levels).toEqual([1, 2, 3])
    })

    it('should detect invalid heading hierarchy', () => {
      const { container, getByRole, getByLabelText, queryByRole } = render(
        <div>
          <h1>Main Title</h1>
          <h3>Skipped h2</h3>
        </div>
      )

      const aria = testScreenReaderLabels({ container, getByRole, getByLabelText, queryByRole })
      const hierarchy = aria.verifyHeadingHierarchy()

      expect(hierarchy.isValid).toBe(false)
    })

    it('should verify live region', () => {
      const { container, getByRole, getByLabelText, queryByRole } = render(
        <div role="status" aria-live="polite">
          Loading...
        </div>
      )

      const aria = testScreenReaderLabels({ container, getByRole, getByLabelText, queryByRole })
      const liveRegion = aria.verifyLiveRegion('status')

      expect(liveRegion).toBeInTheDocument()
    })
  })

  describe('testColorContrast', () => {
    it('should return color information', () => {
      const { container } = render(
        <div style={{ color: 'rgb(0, 0, 0)', backgroundColor: 'rgb(255, 255, 255)' }}>
          Test text
        </div>
      )

      const element = container.firstChild as HTMLElement
      const contrast = testColorContrast(element)

      expect(contrast.color).toBeDefined()
      expect(contrast.backgroundColor).toBeDefined()
    })
  })

  describe('testFocusTrap', () => {
    it('should verify focus trap in modal', async () => {
      const { container } = render(
        <div role="dialog" aria-modal="true">
          <button>First</button>
          <button>Second</button>
          <button>Last</button>
        </div>
      )

      const modal = container.firstChild as HTMLElement
      const focusTrap = testFocusTrap(modal)

      const isTrapped = await focusTrap.verifyFocusTrapped()
      expect(typeof isTrapped).toBe('boolean')
    })

    it('should verify focus returns to trigger', () => {
      const { container } = render(
        <div>
          <button id="trigger">Open Modal</button>
        </div>
      )

      const trigger = container.querySelector('#trigger') as HTMLElement
      trigger.focus()

      const focusTrap = testFocusTrap(container)
      const returned = focusTrap.verifyFocusReturn(trigger)

      expect(returned).toBe(true)
    })
  })

  describe('testSkipLink', () => {
    it('should find skip link', () => {
      const renderResult = render(
        <div>
          <a href="#main-content">Skip to main content</a>
          <main id="main-content">Content</main>
        </div>
      )

      const skipLink = testSkipLink(renderResult)
      expect(skipLink.hasSkipLink()).toBe(true)
    })

    it('should return false when no skip link present', () => {
      const renderResult = render(
        <div>
          <main>Content</main>
        </div>
      )

      const skipLink = testSkipLink(renderResult)
      expect(skipLink.hasSkipLink()).toBe(false)
    })

    it('should activate skip link', async () => {
      const renderResult = render(
        <div>
          <a href="#main">Skip to main</a>
          <main id="main">Content</main>
        </div>
      )

      const skipLink = testSkipLink(renderResult)
      const link = await skipLink.activateSkipLink()

      expect(link).toBeInTheDocument()
    })
  })

  describe('testFormAccessibility', () => {
    it('should verify all inputs have labels', () => {
      const renderResult = render(
        <form>
          <label htmlFor="name">Name</label>
          <input id="name" type="text" />
          <label htmlFor="email">Email</label>
          <input id="email" type="email" />
        </form>
      )

      const form = testFormAccessibility(renderResult)
      const result = form.verifyAllInputsHaveLabels()

      expect(result.allLabeled).toBe(true)
      expect(result.unlabeledInputs.length).toBe(0)
    })

    it('should detect unlabeled inputs', () => {
      const renderResult = render(
        <form>
          <input type="text" />
        </form>
      )

      const form = testFormAccessibility(renderResult)
      const result = form.verifyAllInputsHaveLabels()

      expect(result.allLabeled).toBe(false)
      expect(result.unlabeledInputs.length).toBe(1)
    })

    it('should verify error announcement', () => {
      const renderResult = render(
        <div>
          <div role="alert">Error: Invalid input</div>
        </div>
      )

      const form = testFormAccessibility(renderResult)
      expect(form.verifyErrorAnnouncement()).toBe(true)
    })

    it('should verify required fields', () => {
      const renderResult = render(
        <form>
          <label htmlFor="required-field">
            Required Field *
          </label>
          <input id="required-field" type="text" required aria-required="true" />
        </form>
      )

      const form = testFormAccessibility(renderResult)
      const results = form.verifyRequiredFields()

      expect(results.length).toBe(1)
      expect(results[0].hasAriaRequired).toBe(true)
    })
  })

  describe('categorizeViolations', () => {
    it('should categorize violations by severity', () => {
      const mockResults = {
        violations: [
          { impact: 'critical', id: 'test-1' },
          { impact: 'serious', id: 'test-2' },
          { impact: 'moderate', id: 'test-3' },
          { impact: 'minor', id: 'test-4' },
          { impact: 'critical', id: 'test-5' },
        ],
      }

      const categorized = categorizeViolations(mockResults)

      expect(categorized.critical.length).toBe(2)
      expect(categorized.serious.length).toBe(1)
      expect(categorized.moderate.length).toBe(1)
      expect(categorized.minor.length).toBe(1)
      expect(categorized.total).toBe(5)
    })

    it('should handle empty violations', () => {
      const mockResults = {
        violations: [],
      }

      const categorized = categorizeViolations(mockResults)

      expect(categorized.critical.length).toBe(0)
      expect(categorized.total).toBe(0)
    })
  })

  describe('axeConfigs', () => {
    it('should have predefined configurations', () => {
      expect(axeConfigs.colorContrast).toBeDefined()
      expect(axeConfigs.keyboard).toBeDefined()
      expect(axeConfigs.aria).toBeDefined()
      expect(axeConfigs.forms).toBeDefined()
      expect(axeConfigs.strict).toBeDefined()
    })

    it('should run color contrast config', async () => {
      const { container } = render(
        <div>
          <button>Test</button>
        </div>
      )

      const results = await axeConfigs.colorContrast(container)
      expect(results).toBeDefined()
    })

    it('should run forms config', async () => {
      const { container } = render(
        <form>
          <label htmlFor="test">Test</label>
          <input id="test" type="text" />
        </form>
      )

      const results = await axeConfigs.forms(container)
      expect(results).toBeDefined()
    })
  })

  describe('defaultAxeConfig', () => {
    it('should have WCAG 2.2 AA rules enabled', () => {
      expect(defaultAxeConfig.rules).toBeDefined()
      expect(defaultAxeConfig.rules?.['color-contrast']).toEqual({ enabled: true })
      expect(defaultAxeConfig.rules?.['image-alt']).toEqual({ enabled: true })
      expect(defaultAxeConfig.rules?.['label']).toEqual({ enabled: true })
    })
  })

  describe('A11ySeverity', () => {
    it('should have correct severity levels', () => {
      expect(A11ySeverity.CRITICAL).toBe('critical')
      expect(A11ySeverity.SERIOUS).toBe('serious')
      expect(A11ySeverity.MODERATE).toBe('moderate')
      expect(A11ySeverity.MINOR).toBe('minor')
    })
  })
})
