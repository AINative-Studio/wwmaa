# Accessibility Testing Guide

This guide explains how to test accessibility in the World Wide Martial Arts Alliance application. Follow these procedures to ensure WCAG 2.2 AA compliance.

## Table of Contents
- [Quick Start](#quick-start)
- [Automated Testing](#automated-testing)
- [Manual Testing](#manual-testing)
- [Tools Setup](#tools-setup)
- [Common Issues and Fixes](#common-issues-and-fixes)
- [CI/CD Integration](#cicd-integration)

---

## Quick Start

### Run All A11y Tests
```bash
# Run all accessibility tests
npm test -- __tests__/a11y

# Run with coverage
npm test -- __tests__/a11y --coverage

# Watch mode for development
npm test -- __tests__/a11y --watch
```

### Test a Single Component
```bash
# Test specific component
npm test -- __tests__/a11y/event-components.test.tsx

# Generate accessibility report
npm run test:a11y:report
```

---

## Automated Testing

### jest-axe Integration

All components should have automated accessibility tests using jest-axe.

#### Basic Test Template

```typescript
import { render } from '@testing-library/react'
import { runAxeTest } from '__tests__/utils/a11y'
import { MyComponent } from '@/components/my-component'

describe('MyComponent - Accessibility', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(<MyComponent />)
    const results = await runAxeTest(container)
    expect(results).toHaveNoViolations()
  })
})
```

#### Testing with Props

```typescript
it('should be accessible in all states', async () => {
  // Test default state
  const { container, rerender } = render(<Button>Click me</Button>)
  expect(await runAxeTest(container)).toHaveNoViolations()

  // Test disabled state
  rerender(<Button disabled>Click me</Button>)
  expect(await runAxeTest(container)).toHaveNoViolations()

  // Test loading state
  rerender(<Button loading>Click me</Button>)
  expect(await runAxeTest(container)).toHaveNoViolations()
})
```

#### Testing with Custom Rules

```typescript
import { axeConfigs } from '__tests__/utils/a11y'

it('should pass color contrast checks', async () => {
  const { container } = render(<MyComponent />)
  const results = await axeConfigs.colorContrast(container)
  expect(results).toHaveNoViolations()
})
```

### Keyboard Navigation Testing

```typescript
import { testKeyboardNavigation } from '__tests__/utils/a11y'

it('should be keyboard navigable', async () => {
  const renderResult = render(<NavigationMenu />)
  const nav = testKeyboardNavigation(renderResult)

  // Tab through all elements
  await nav.tabThroughElements()

  // Check first element is focused
  const firstButton = renderResult.getByRole('button', { name: 'Home' })
  expect(nav.getFocusedElement()).toBe(firstButton)

  // Test activation with Enter
  await nav.pressEnter()
  expect(mockNavigate).toHaveBeenCalled()

  // Test closing with Escape
  await nav.pressEscape()
  expect(menuOpen).toBe(false)
})
```

### Screen Reader Label Testing

```typescript
import { testScreenReaderLabels } from '__tests__/utils/a11y'

it('should have proper ARIA labels', () => {
  const renderResult = render(<LoginForm />)
  const aria = testScreenReaderLabels(renderResult)

  // Verify button has label
  aria.verifyButtonHasLabel('Sign In')

  // Verify input has label
  aria.verifyInputHasLabel('Email Address', 'email-input')

  // Verify ARIA attributes
  const alertDiv = renderResult.getByRole('alert')
  aria.verifyAriaAttributes(alertDiv, {
    'aria-live': 'assertive',
    'role': 'alert',
  })
})
```

### Form Accessibility Testing

```typescript
import { testFormAccessibility } from '__tests__/utils/a11y'

it('should have accessible form', () => {
  const renderResult = render(<ContactForm />)
  const form = testFormAccessibility(renderResult)

  // All inputs have labels
  const { allLabeled, unlabeledInputs } = form.verifyAllInputsHaveLabels()
  expect(allLabeled).toBe(true)
  expect(unlabeledInputs.length).toBe(0)

  // Required fields marked
  const requiredFields = form.verifyRequiredFields()
  requiredFields.forEach(field => {
    expect(field.hasAriaRequired).toBe(true)
  })

  // Errors announced
  // Submit form with invalid data
  fireEvent.submit(renderResult.getByRole('form'))
  expect(form.verifyErrorAnnouncement()).toBe(true)
})
```

---

## Manual Testing

### Keyboard Navigation Testing

Manual keyboard testing is essential to verify the full user experience.

#### Basic Keyboard Testing Procedure

1. **Tab Navigation**
   ```
   - Press Tab repeatedly through the entire page
   - Verify every interactive element receives focus
   - Verify focus indicator is clearly visible
   - Verify tab order matches visual order
   ```

2. **Reverse Tab Navigation**
   ```
   - Press Shift+Tab to move backward
   - Verify reverse order works correctly
   ```

3. **Element Activation**
   ```
   - Press Enter on links and buttons
   - Press Space on buttons and checkboxes
   - Verify actions trigger correctly
   ```

4. **Special Keys**
   ```
   - Press Escape to close modals/menus
   - Use Arrow keys in dropdowns, tabs, carousels
   - Use Home/End to jump to start/end
   ```

#### Testing Checklist

- [ ] Tab reaches all interactive elements
- [ ] Skip link appears and works (first Tab)
- [ ] Focus indicator visible at all times
- [ ] No keyboard traps (can exit all components)
- [ ] Enter/Space activate buttons and links
- [ ] Escape closes modals and menus
- [ ] Arrow keys work in custom widgets
- [ ] Form submission works with Enter key

### Screen Reader Testing

Test with at least one screen reader to verify content is properly announced.

#### VoiceOver (macOS)

**Enable VoiceOver:**
```
System Preferences → Accessibility → VoiceOver → Enable VoiceOver
Or: Cmd+F5
```

**Basic Commands:**
- `VO + Right Arrow`: Next element
- `VO + Left Arrow`: Previous element
- `VO + Space`: Activate element
- `VO + A`: Read from cursor
- `VO + U`: Open rotor (navigate by headings, links, landmarks)

**Testing Steps:**
1. Enable VoiceOver (Cmd+F5)
2. Navigate through the page with VO+Right Arrow
3. Use rotor (VO+U) to jump to landmarks, headings, links
4. Verify all content is announced
5. Verify images have appropriate alt text
6. Verify form labels are announced
7. Disable VoiceOver (Cmd+F5)

#### NVDA (Windows, Free)

**Download:** https://www.nvaccess.org/download/

**Basic Commands:**
- `Down Arrow`: Next line
- `Up Arrow`: Previous line
- `H`: Next heading
- `K`: Next link
- `F`: Next form field
- `D`: Next landmark
- `Insert + F7`: Elements list (navigate by type)

**Testing Steps:**
1. Start NVDA (Ctrl+Alt+N)
2. Navigate with arrow keys
3. Use H key to jump between headings
4. Use K key to jump between links
5. Use F key to jump between form fields
6. Verify all interactive elements announced
7. Exit NVDA (Insert+Q)

#### JAWS (Windows, Commercial)

**Download:** https://www.freedomscientific.com/products/software/jaws/

Similar commands to NVDA. Test if JAWS license available.

### Visual Testing

#### Zoom Testing (200%)

1. Open page in browser
2. Zoom to 200% (Cmd/Ctrl + "+" or Cmd/Ctrl + scroll)
3. Verify:
   - All content visible
   - No horizontal scrolling
   - No overlapping content
   - Text reflows properly
   - Interactive elements still usable

#### Text Spacing Testing

Test with increased text spacing to ensure content doesn't break.

**Bookmarklet:**
```javascript
javascript:(function(){var%20style=document.createElement('style');style.innerHTML='*{line-height:1.5!important;letter-spacing:0.12em!important;word-spacing:0.16em!important;}p{margin-bottom:2em!important;}';document.head.appendChild(style);})();
```

1. Add bookmarklet to browser
2. Open page
3. Click bookmarklet
4. Verify no content is cut off or obscured

#### Small Viewport Testing (320px)

1. Open Chrome DevTools (F12)
2. Toggle device toolbar (Cmd/Ctrl+Shift+M)
3. Set viewport to 320px width
4. Verify:
   - All content accessible
   - No horizontal scrolling
   - Touch targets at least 44x44px
   - Text readable (minimum 16px)

#### High Contrast Mode (Windows)

1. Enable Windows High Contrast
   ```
   Settings → Ease of Access → High Contrast → Turn on High Contrast
   ```
2. Open application
3. Verify:
   - All text visible
   - All interactive elements visible
   - Icons and images visible or have text alternatives
   - Focus indicators visible

---

## Tools Setup

### 1. axe DevTools Browser Extension

**Install:**
- [Chrome/Edge](https://chrome.google.com/webstore/detail/axe-devtools-web-accessib/lhdoppojpmngadmnindnejefpokejbdd)
- [Firefox](https://addons.mozilla.org/en-US/firefox/addon/axe-devtools/)

**Usage:**
1. Open DevTools (F12)
2. Click "axe DevTools" tab
3. Click "Scan ALL of my page"
4. Review violations by severity:
   - Critical (fix immediately)
   - Serious (high priority)
   - Moderate (medium priority)
   - Minor (low priority)
5. Click each violation for:
   - Description
   - Impact
   - Affected elements
   - How to fix

### 2. WAVE Browser Extension

**Install:**
- [Chrome](https://chrome.google.com/webstore/detail/wave-evaluation-tool/jbbplnpkjmmeebjpijfedlgcdilocofh)
- [Firefox](https://addons.mozilla.org/en-US/firefox/addon/wave-accessibility-tool/)

**Usage:**
1. Open page
2. Click WAVE extension icon
3. Review visual indicators:
   - Red icons: Errors (must fix)
   - Yellow icons: Alerts (review)
   - Green icons: Features (good practices)
4. Click "Details" tab for full report
5. Click "Structure" tab to view semantic outline

### 3. Lighthouse (Chrome DevTools)

**Usage:**
1. Open Chrome DevTools (F12)
2. Click "Lighthouse" tab
3. Select "Accessibility" category
4. Click "Generate report"
5. Review score and opportunities
6. Follow recommendations

### 4. Color Contrast Analyzer

**Download:**
- [Windows/Mac](https://www.tpgi.com/color-contrast-checker/)

**Usage:**
1. Open application
2. Use eyedropper to select foreground color
3. Use eyedropper to select background color
4. View contrast ratio
5. Verify meets WCAG AA (4.5:1 for normal text, 3:1 for large text)

---

## Common Issues and Fixes

### Missing Alt Text

**Issue:**
```tsx
<img src="/logo.png" />
```

**Fix:**
```tsx
<img src="/logo.png" alt="World Wide Martial Arts Alliance" />
```

### Low Color Contrast

**Issue:**
```css
color: #777;
background: #fff;
/* Contrast ratio: 4.47:1 (fails for small text) */
```

**Fix:**
```css
color: #5f5f5f;
background: #fff;
/* Contrast ratio: 5.74:1 (passes WCAG AA) */
```

### Missing Form Labels

**Issue:**
```tsx
<input type="email" placeholder="Email" />
```

**Fix:**
```tsx
<label htmlFor="email">Email Address</label>
<input id="email" type="email" />
```

Or with aria-label:
```tsx
<input type="email" aria-label="Email Address" />
```

### Unlabeled Buttons

**Issue:**
```tsx
<button>
  <XIcon />
</button>
```

**Fix:**
```tsx
<button aria-label="Close">
  <XIcon aria-hidden="true" />
</button>
```

### Non-semantic HTML

**Issue:**
```tsx
<div onClick={handleClick}>Click me</div>
```

**Fix:**
```tsx
<button onClick={handleClick}>Click me</button>
```

### Missing Focus Indicator

**Issue:**
```css
button:focus {
  outline: none;
}
```

**Fix:**
```css
button:focus-visible {
  outline: 2px solid #0066cc;
  outline-offset: 2px;
}
```

### Keyboard Trap in Modal

**Issue:**
Modal allows Tab to reach background elements.

**Fix:**
```tsx
import { FocusTrap } from '@/components/a11y/focus-trap'

<FocusTrap>
  <Dialog>
    {/* Modal content */}
  </Dialog>
</FocusTrap>
```

### Missing Live Region

**Issue:**
Form errors appear but aren't announced.

**Fix:**
```tsx
{error && (
  <div role="alert" aria-live="assertive">
    {error}
  </div>
)}
```

### Incorrect Heading Hierarchy

**Issue:**
```tsx
<h1>Page Title</h1>
<h3>Section Title</h3> {/* Skipped h2 */}
```

**Fix:**
```tsx
<h1>Page Title</h1>
<h2>Section Title</h2>
```

---

## CI/CD Integration

### GitHub Actions Workflow

Accessibility tests run automatically on every commit.

**Configuration (`.github/workflows/a11y-tests.yml`):**
```yaml
name: Accessibility Tests

on: [push, pull_request]

jobs:
  a11y-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run test:a11y
      - name: Upload A11y Report
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: a11y-report
          path: a11y-report.html
```

### Railway Deployment

Accessibility tests run before deployment.

**Configuration:**
```json
{
  "build": {
    "command": "npm run build && npm run test:a11y"
  }
}
```

### Local Pre-commit Hook

Run tests before each commit.

**Setup:**
```bash
# Install husky
npm install --save-dev husky

# Initialize husky
npx husky install

# Add pre-commit hook
npx husky add .husky/pre-commit "npm run test:a11y"
```

---

## Accessibility Scoring

### Violation Severity Levels

1. **Critical** (0 allowed)
   - Missing alt text on informative images
   - Forms without labels
   - Missing page title
   - Color contrast < 3:1

2. **Serious** (0 allowed)
   - Low color contrast (< 4.5:1)
   - Missing landmark regions
   - Improper heading hierarchy
   - Unlabeled buttons

3. **Moderate** (max 5)
   - Missing skip link
   - Non-descriptive link text
   - Missing field descriptions
   - Insufficient touch target size

4. **Minor** (max 10)
   - Missing lang attribute on parts
   - Redundant alt text
   - Missing fieldset/legend
   - Non-optimal ARIA usage

### Scoring Criteria

- **100%**: No violations
- **90-99%**: Minor violations only
- **80-89%**: Moderate violations, no serious
- **70-79%**: Serious violations, no critical
- **< 70%**: Critical violations present (fail)

### CI/CD Thresholds

```typescript
// jest.config.js
module.exports = {
  a11yThresholds: {
    critical: 0,    // Build fails
    serious: 0,     // Build fails
    moderate: 5,    // Warning
    minor: 10,      // Warning
  },
}
```

---

## Reporting Accessibility Issues

### During Development

1. Run automated tests: `npm run test:a11y`
2. Fix critical and serious violations immediately
3. Document moderate violations for sprint planning
4. Create GitHub issues for remaining violations

### For Production Issues

1. Use axe DevTools on live site
2. Test with screen reader
3. Create detailed bug report:
   - URL
   - Violation description
   - WCAG criterion violated
   - Severity level
   - Steps to reproduce
   - Screenshots/screen recording
   - Suggested fix

### Accessibility Report Template

```markdown
## Accessibility Violation Report

**Page:** /events/calendar
**Severity:** Critical
**WCAG Criterion:** 1.1.1 Non-text Content (Level A)

**Description:**
Event image is missing alt text.

**Impact:**
Screen reader users cannot understand the image content.

**Steps to Reproduce:**
1. Navigate to /events/calendar
2. Inspect event card image
3. Verify alt attribute is empty

**Expected:**
`<img src="event.jpg" alt="Karate seminar with Master Smith" />`

**Actual:**
`<img src="event.jpg" alt="" />`

**Suggested Fix:**
Add descriptive alt text based on event title and type.

**Related:**
- Event Card Component: components/events/event-card.tsx:77
```

---

## Best Practices

1. **Test Early and Often**
   - Run automated tests during development
   - Test with keyboard regularly
   - Use axe DevTools frequently

2. **Fix Issues Immediately**
   - Don't accumulate accessibility debt
   - Fix critical issues before code review
   - Address all serious issues before merge

3. **Test with Real Users**
   - Conduct usability testing with assistive tech users
   - Gather feedback from users with disabilities
   - Iterate based on real-world usage

4. **Stay Updated**
   - Follow WCAG updates
   - Review axe-core release notes
   - Learn from accessibility community

5. **Document Patterns**
   - Create reusable accessible components
   - Document accessibility considerations
   - Share knowledge with team

---

## Resources

### Official Documentation
- [WCAG 2.2 Guidelines](https://www.w3.org/TR/WCAG22/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [jest-axe Documentation](https://github.com/nickcolley/jest-axe)

### Learning Resources
- [WebAIM Articles](https://webaim.org/articles/)
- [A11ycasts (YouTube)](https://www.youtube.com/playlist?list=PLNYkxOF6rcICWx0C9LVWWVqvHlYJyqw7g)
- [Deque University](https://dequeuniversity.com/)

### Community
- [A11y Slack](https://web-a11y.slack.com/)
- [A11y Project](https://www.a11yproject.com/)
- [WebAIM Forum](https://webaim.org/discussion/)

---

**Last Updated:** 2025-11-10
**Version:** 1.0.0
