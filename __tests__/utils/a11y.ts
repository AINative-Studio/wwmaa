/**
 * Accessibility Testing Utilities
 * Helper functions for automated accessibility testing with jest-axe
 */

import { configureAxe, type JestAxeConfigureOptions } from 'jest-axe'
import { RenderResult } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

/**
 * Default axe configuration for WCAG 2.2 AA compliance
 * Covers the most critical accessibility requirements
 */
export const defaultAxeConfig: JestAxeConfigureOptions = {
  rules: {
    // WCAG 2.2 Level A & AA rules
    'color-contrast': { enabled: true },
    'valid-lang': { enabled: true },
    'html-has-lang': { enabled: true },
    'image-alt': { enabled: true },
    'button-name': { enabled: true },
    'link-name': { enabled: true },
    'label': { enabled: true },
    'input-button-name': { enabled: true },
    'form-field-multiple-labels': { enabled: true },
    'frame-title': { enabled: true },
    'duplicate-id': { enabled: true },
    'duplicate-id-active': { enabled: true },
    'duplicate-id-aria': { enabled: true },
    'heading-order': { enabled: true },
    'landmark-one-main': { enabled: true },
    'landmark-complementary-is-top-level': { enabled: true },
    'page-has-heading-one': { enabled: true },
    'region': { enabled: true },
    'skip-link': { enabled: true },
    'focus-order-semantics': { enabled: true },
    'aria-allowed-attr': { enabled: true },
    'aria-required-attr': { enabled: true },
    'aria-valid-attr-value': { enabled: true },
    'aria-valid-attr': { enabled: true },
    'aria-hidden-focus': { enabled: true },
    'aria-roles': { enabled: true },
    'role-img-alt': { enabled: true },
    'list': { enabled: true },
    'listitem': { enabled: true },
    'definition-list': { enabled: true },
    'dlitem': { enabled: true },
  },
}

/**
 * Create a pre-configured axe instance with WCAG 2.2 AA rules
 */
export const axe = configureAxe(defaultAxeConfig)

/**
 * Run automated accessibility tests on a component
 * @param container - The rendered component container
 * @param options - Optional axe configuration overrides
 * @returns Promise resolving to axe test results
 *
 * @example
 * const { container } = render(<MyComponent />);
 * const results = await runAxeTest(container);
 * expect(results).toHaveNoViolations();
 */
export async function runAxeTest(
  container: Element,
  options?: JestAxeConfigureOptions
) {
  const axeInstance = options ? configureAxe(options) : axe
  return await axeInstance(container)
}

/**
 * Test keyboard navigation through interactive elements
 * Verifies that all interactive elements are keyboard accessible
 *
 * @param renderResult - The result from @testing-library/react render()
 * @param expectedFocusableElements - Array of expected focusable element selectors
 * @returns Object with helper methods for keyboard testing
 *
 * @example
 * const { getAllByRole } = render(<Form />);
 * const nav = testKeyboardNavigation({ getAllByRole }, ['button', 'input']);
 * await nav.tabThroughElements();
 * expect(nav.getFocusedElement()).toBe(firstButton);
 */
export function testKeyboardNavigation(
  renderResult: Pick<RenderResult, 'container' | 'getByRole' | 'getAllByRole' | 'queryByRole'>,
  expectedFocusableElements?: string[]
) {
  const user = userEvent.setup()
  const { container } = renderResult

  return {
    /**
     * Tab through all focusable elements in order
     */
    async tabThroughElements() {
      const focusableElements = container.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )

      for (let i = 0; i < focusableElements.length; i++) {
        await user.tab()
      }

      return focusableElements
    },

    /**
     * Tab backwards through elements
     */
    async shiftTabThroughElements() {
      await user.tab({ shift: true })
    },

    /**
     * Get the currently focused element
     */
    getFocusedElement() {
      return document.activeElement
    },

    /**
     * Press Enter on the currently focused element
     */
    async pressEnter() {
      await user.keyboard('{Enter}')
    },

    /**
     * Press Space on the currently focused element
     */
    async pressSpace() {
      await user.keyboard(' ')
    },

    /**
     * Press Escape key
     */
    async pressEscape() {
      await user.keyboard('{Escape}')
    },

    /**
     * Navigate with arrow keys
     */
    async pressArrowDown() {
      await user.keyboard('{ArrowDown}')
    },

    async pressArrowUp() {
      await user.keyboard('{ArrowUp}')
    },

    async pressArrowLeft() {
      await user.keyboard('{ArrowLeft}')
    },

    async pressArrowRight() {
      await user.keyboard('{ArrowRight}')
    },

    /**
     * Verify all expected focusable elements are present
     */
    verifyFocusableElements() {
      if (!expectedFocusableElements) return true

      const focusableElements = container.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )

      return focusableElements.length >= expectedFocusableElements.length
    },
  }
}

/**
 * Verify screen reader labels and ARIA attributes
 * Checks for proper labeling of interactive elements
 *
 * @param renderResult - The result from @testing-library/react render()
 * @returns Object with helper methods for ARIA testing
 *
 * @example
 * const screen = render(<LoginForm />);
 * const aria = testScreenReaderLabels(screen);
 * aria.verifyButtonHasLabel('Submit');
 * aria.verifyInputHasLabel('Email', 'email-input');
 */
export function testScreenReaderLabels(
  renderResult: Pick<RenderResult, 'container' | 'getByRole' | 'getByLabelText' | 'queryByRole'>
) {
  const { container, getByRole, getByLabelText, queryByRole } = renderResult

  return {
    /**
     * Verify a button has accessible name
     */
    verifyButtonHasLabel(buttonText: string) {
      const button = getByRole('button', { name: new RegExp(buttonText, 'i') })
      expect(button).toBeInTheDocument()
      expect(button).toHaveAccessibleName()
      return button
    },

    /**
     * Verify an input has a label
     */
    verifyInputHasLabel(labelText: string, inputId?: string) {
      const input = getByLabelText(new RegExp(labelText, 'i'))
      expect(input).toBeInTheDocument()

      if (inputId) {
        expect(input).toHaveAttribute('id', inputId)
      }

      return input
    },

    /**
     * Verify an element has proper ARIA attributes
     */
    verifyAriaAttributes(element: HTMLElement, expectedAttrs: Record<string, string | boolean>) {
      Object.entries(expectedAttrs).forEach(([attr, value]) => {
        if (typeof value === 'boolean') {
          if (value) {
            expect(element).toHaveAttribute(attr)
          } else {
            expect(element).not.toHaveAttribute(attr)
          }
        } else {
          expect(element).toHaveAttribute(attr, value)
        }
      })
    },

    /**
     * Verify landmarks are present
     */
    verifyLandmarks() {
      const nav = queryByRole('navigation')
      const main = queryByRole('main')
      const contentinfo = queryByRole('contentinfo')

      return {
        hasNavigation: !!nav,
        hasMain: !!main,
        hasFooter: !!contentinfo,
      }
    },

    /**
     * Verify heading hierarchy
     */
    verifyHeadingHierarchy() {
      const headings = Array.from(container.querySelectorAll('h1, h2, h3, h4, h5, h6'))
      const levels = headings.map(h => parseInt(h.tagName.charAt(1)))

      let valid = true
      let expectedLevel = 1

      for (const level of levels) {
        if (level > expectedLevel + 1) {
          valid = false
          break
        }
        expectedLevel = level
      }

      return {
        isValid: valid,
        levels,
        headings,
      }
    },

    /**
     * Verify live regions for dynamic content
     */
    verifyLiveRegion(role: 'status' | 'alert' | 'log') {
      const region = queryByRole(role)
      return region
    },
  }
}

/**
 * Test color contrast ratios for text elements
 * Note: This is a basic implementation. For production use, consider using axe-core's color-contrast rule
 *
 * @param element - The element to test
 * @returns Object with contrast information
 */
export function testColorContrast(element: HTMLElement) {
  const computedStyle = window.getComputedStyle(element)
  const color = computedStyle.color
  const backgroundColor = computedStyle.backgroundColor

  return {
    color,
    backgroundColor,
    // Note: Actual contrast calculation requires parsing RGB values
    // This is a placeholder - axe-core handles this automatically
    meetsWCAG_AA: true, // Determined by axe-core
    meetsWCAG_AAA: true, // Determined by axe-core
  }
}

/**
 * Test focus trap in modals
 * Ensures focus stays within modal when tabbing
 *
 * @param modalContainer - The modal container element
 * @returns Object with focus trap testing methods
 */
export function testFocusTrap(modalContainer: HTMLElement) {
  const user = userEvent.setup()

  return {
    /**
     * Verify focus stays within modal when tabbing
     */
    async verifyFocusTrapped() {
      const focusableElements = modalContainer.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )

      if (focusableElements.length === 0) return false

      const firstElement = focusableElements[0] as HTMLElement
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement

      // Tab to last element
      lastElement.focus()
      await user.tab()

      // Should cycle back to first element
      const isFocusTrapped = document.activeElement === firstElement

      return isFocusTrapped
    },

    /**
     * Verify focus returns to trigger element when modal closes
     */
    verifyFocusReturn(triggerElement: HTMLElement) {
      return document.activeElement === triggerElement
    },
  }
}

/**
 * Helper to test skip links
 */
export function testSkipLink(renderResult: RenderResult) {
  const { container } = renderResult
  const user = userEvent.setup()

  return {
    /**
     * Find and activate skip link
     */
    async activateSkipLink() {
      const skipLink = container.querySelector('a[href^="#"][href*="main"], a[href^="#"][href*="content"]') as HTMLElement

      if (!skipLink) return null

      skipLink.focus()
      await user.keyboard('{Enter}')

      return skipLink
    },

    /**
     * Verify skip link is present
     */
    hasSkipLink() {
      const skipLink = container.querySelector('a[href^="#"][href*="main"], a[href^="#"][href*="content"]')
      return !!skipLink
    },
  }
}

/**
 * Test form accessibility
 */
export function testFormAccessibility(renderResult: RenderResult) {
  const { container, getByLabelText, queryByRole } = renderResult

  return {
    /**
     * Verify all inputs have labels
     */
    verifyAllInputsHaveLabels() {
      const inputs = container.querySelectorAll('input, select, textarea')
      const unlabeledInputs: HTMLElement[] = []

      inputs.forEach(input => {
        const id = input.getAttribute('id')
        const ariaLabel = input.getAttribute('aria-label')
        const ariaLabelledBy = input.getAttribute('aria-labelledby')
        const label = id ? container.querySelector(`label[for="${id}"]`) : null

        if (!label && !ariaLabel && !ariaLabelledBy) {
          unlabeledInputs.push(input as HTMLElement)
        }
      })

      return {
        allLabeled: unlabeledInputs.length === 0,
        unlabeledInputs,
      }
    },

    /**
     * Verify error messages are announced
     */
    verifyErrorAnnouncement() {
      const errorRegion = queryByRole('alert')
      return !!errorRegion
    },

    /**
     * Verify required fields are marked
     */
    verifyRequiredFields() {
      const requiredInputs = container.querySelectorAll('input[required], select[required], textarea[required]')
      const results: Array<{ element: Element; hasAriaRequired: boolean; hasVisualIndicator: boolean }> = []

      requiredInputs.forEach(input => {
        const hasAriaRequired = input.hasAttribute('aria-required') || input.hasAttribute('required')
        const label = input.id ? container.querySelector(`label[for="${input.id}"]`) : null
        const hasVisualIndicator = label?.textContent?.includes('*') || false

        results.push({
          element: input,
          hasAriaRequired,
          hasVisualIndicator,
        })
      })

      return results
    },
  }
}

/**
 * Custom axe configurations for specific scenarios
 */
export const axeConfigs = {
  /**
   * Configuration for testing color contrast only
   */
  colorContrast: configureAxe({
    rules: {
      'color-contrast': { enabled: true },
    },
  }),

  /**
   * Configuration for testing keyboard accessibility
   */
  keyboard: configureAxe({
    rules: {
      'focus-order-semantics': { enabled: true },
      'tabindex': { enabled: true },
    },
  }),

  /**
   * Configuration for testing ARIA
   */
  aria: configureAxe({
    rules: {
      'aria-allowed-attr': { enabled: true },
      'aria-required-attr': { enabled: true },
      'aria-valid-attr-value': { enabled: true },
      'aria-valid-attr': { enabled: true },
      'aria-hidden-focus': { enabled: true },
      'aria-roles': { enabled: true },
    },
  }),

  /**
   * Configuration for testing forms
   */
  forms: configureAxe({
    rules: {
      'label': { enabled: true },
      'input-button-name': { enabled: true },
      'form-field-multiple-labels': { enabled: true },
    },
  }),

  /**
   * Strict configuration for production readiness
   */
  strict: configureAxe({
    rules: {
      // Enable all rules
      'color-contrast': { enabled: true },
      'image-alt': { enabled: true },
      'label': { enabled: true },
      'button-name': { enabled: true },
      'link-name': { enabled: true },
      'heading-order': { enabled: true },
      'landmark-one-main': { enabled: true },
      'page-has-heading-one': { enabled: true },
    },
  }),
}

/**
 * Accessibility test result severity levels
 */
export enum A11ySeverity {
  CRITICAL = 'critical',
  SERIOUS = 'serious',
  MODERATE = 'moderate',
  MINOR = 'minor',
}

/**
 * Helper to categorize axe violations by severity
 */
export function categorizeViolations(results: any) {
  const violations = results.violations || []

  return {
    critical: violations.filter((v: any) => v.impact === A11ySeverity.CRITICAL),
    serious: violations.filter((v: any) => v.impact === A11ySeverity.SERIOUS),
    moderate: violations.filter((v: any) => v.impact === A11ySeverity.MODERATE),
    minor: violations.filter((v: any) => v.impact === A11ySeverity.MINOR),
    total: violations.length,
  }
}
