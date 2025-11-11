# Accessibility Checklist (WCAG 2.2 AA Compliance)

This checklist ensures all features meet WCAG 2.2 Level AA standards for accessibility. Use this when developing new features or reviewing existing code.

## Table of Contents
- [Perceivable](#perceivable)
- [Operable](#operable)
- [Understandable](#understandable)
- [Robust](#robust)
- [Testing Checklist](#testing-checklist)

---

## Perceivable

Information and user interface components must be presentable to users in ways they can perceive.

### Text Alternatives (Level A)
- [ ] **1.1.1** All images have appropriate alt text
  - Decorative images: use `alt=""` or `aria-hidden="true"`
  - Informative images: describe the content/function
  - Complex images (charts, diagrams): provide detailed description
  - Example: `<img src="logo.png" alt="World Wide Martial Arts Alliance" />`

### Time-based Media (Level A)
- [ ] **1.2.1** Pre-recorded audio/video has captions or transcripts
- [ ] **1.2.2** Pre-recorded video has audio description or alternative
- [ ] **1.2.3** Live audio has captions (streaming events)

### Adaptable (Level A)
- [ ] **1.3.1** Information and relationships conveyed through presentation are available programmatically
  - Use semantic HTML (`<nav>`, `<main>`, `<header>`, `<footer>`, `<article>`, `<section>`)
  - Form labels associated with inputs
  - Tables have proper headers
- [ ] **1.3.2** Meaningful sequence maintained when CSS disabled
- [ ] **1.3.3** Instructions don't rely solely on shape, size, location, or sound
  - Bad: "Click the green button on the right"
  - Good: "Click the Submit button"

### Distinguishable (Level AA)
- [ ] **1.4.3** Color contrast ratio of at least 4.5:1 for normal text
  - Large text (18pt+ or 14pt+ bold): 3:1 minimum
  - Use contrast checker tools
  - Test with browser dev tools or axe DevTools
- [ ] **1.4.4** Text can be resized up to 200% without loss of content or functionality
- [ ] **1.4.5** Text is used instead of images of text (except logos)
- [ ] **1.4.10** Content reflows for 320px viewport width (no horizontal scrolling)
- [ ] **1.4.11** UI components and graphical objects have 3:1 contrast with adjacent colors
- [ ] **1.4.12** Text spacing can be increased without loss of content
  - Line height: 1.5x font size
  - Paragraph spacing: 2x font size
  - Letter spacing: 0.12x font size
  - Word spacing: 0.16x font size

---

## Operable

User interface components and navigation must be operable.

### Keyboard Accessible (Level A)
- [ ] **2.1.1** All functionality available via keyboard
  - Test with Tab, Shift+Tab, Enter, Space, Arrow keys, Escape
  - No keyboard traps (can exit all components)
  - Custom components handle keyboard events properly
- [ ] **2.1.2** No keyboard trap - users can navigate away from any component
- [ ] **2.1.4** Single-key shortcuts can be disabled/remapped (if implemented)

### Enough Time (Level A)
- [ ] **2.2.1** Time limits can be turned off, adjusted, or extended
- [ ] **2.2.2** Moving, blinking, scrolling content can be paused/stopped (if > 5 seconds)

### Seizures and Physical Reactions (Level A)
- [ ] **2.3.1** No content flashes more than 3 times per second
  - Avoid animations that could trigger seizures

### Navigable (Level AA)
- [ ] **2.4.1** Skip link provided to bypass repetitive content
  - Example: "Skip to main content" link at top of page
- [ ] **2.4.2** Page has descriptive and unique title
  - Use Next.js `<title>` in each page
- [ ] **2.4.3** Focus order follows meaningful sequence
  - Tab order matches visual order
- [ ] **2.4.4** Link purpose clear from link text or context
  - Bad: "Click here", "Read more", "Learn more"
  - Good: "Read the Getting Started guide", "View event details"
- [ ] **2.4.5** Multiple ways to find pages (search, navigation, sitemap)
- [ ] **2.4.6** Headings and labels are descriptive
- [ ] **2.4.7** Focus indicator is visible
  - Ensure focus outline has sufficient contrast
  - Don't remove `:focus` styles without replacement

### Input Modalities (Level A)
- [ ] **2.5.1** All gestures have keyboard/single-pointer alternative
- [ ] **2.5.2** Touch targets are at least 44x44 CSS pixels (mobile)
- [ ] **2.5.3** Labels in code match visible labels
- [ ] **2.5.4** Motion actuation can be disabled (shake to undo, tilt to scroll)

---

## Understandable

Information and operation of the user interface must be understandable.

### Readable (Level A)
- [ ] **3.1.1** Page language is specified
  - Example: `<html lang="en">`
- [ ] **3.1.2** Language of parts specified when different from page
  - Example: `<span lang="es">Hola</span>`

### Predictable (Level AA)
- [ ] **3.2.1** Focus doesn't trigger unexpected context change
  - Focusing an input shouldn't auto-submit form
- [ ] **3.2.2** Input doesn't trigger unexpected context change
  - Changing a select shouldn't navigate away
  - Use explicit "Go" or "Submit" buttons
- [ ] **3.2.3** Navigation is consistent across pages
- [ ] **3.2.4** Components with same functionality are consistently labeled

### Input Assistance (Level AA)
- [ ] **3.3.1** Error messages clearly identify the problem
  - Example: "Email is required" not just "Error"
- [ ] **3.3.2** Labels or instructions provided for user input
  - All form fields have associated `<label>` or `aria-label`
- [ ] **3.3.3** Error suggestions provided when possible
  - "Email format invalid. Example: user@example.com"
- [ ] **3.3.4** Error prevention for legal/financial/data transactions
  - Confirmation page or ability to review/edit before submission

---

## Robust

Content must be robust enough to be interpreted by a wide variety of user agents, including assistive technologies.

### Compatible (Level A)
- [ ] **4.1.1** Markup is valid and properly nested
  - Use HTML validator
  - No duplicate IDs
- [ ] **4.1.2** Name, role, and value available for all UI components
  - Use semantic HTML or proper ARIA attributes
  - Custom components have appropriate ARIA roles
- [ ] **4.1.3** Status messages can be programmatically determined
  - Use `role="status"` or `role="alert"` for dynamic updates
  - Live regions announce changes to screen readers

---

## Component-Specific Checklist

### Forms
- [ ] All inputs have associated labels (`<label for="id">` or `aria-label`)
- [ ] Required fields marked with `required` or `aria-required="true"`
- [ ] Required field indicator (*) included in label text
- [ ] Error messages associated with fields (`aria-describedby`)
- [ ] Errors announced to screen readers (`role="alert"`)
- [ ] Field constraints explained (format, length, etc.)
- [ ] Success messages announced (`role="status"`)

### Buttons
- [ ] All buttons have accessible names (text, `aria-label`, or `aria-labelledby`)
- [ ] Icon-only buttons have text labels or `aria-label`
- [ ] Button purpose clear from context
- [ ] Disabled buttons have `disabled` attribute
- [ ] Toggle buttons use `aria-pressed` to indicate state

### Links
- [ ] Link purpose clear from text alone
- [ ] Links that open in new window/tab indicated
  - Use `aria-label` or visible text "(opens in new window)"
- [ ] Links vs buttons: Use `<a>` for navigation, `<button>` for actions

### Images
- [ ] Informative images have descriptive alt text
- [ ] Decorative images have `alt=""` or `aria-hidden="true"`
- [ ] Complex images have long descriptions (nearby text or `aria-describedby`)
- [ ] Background images with content have text alternatives
- [ ] Icon fonts have text alternatives or `aria-label`

### Navigation
- [ ] Navigation wrapped in `<nav>` landmark
- [ ] Skip link provided
- [ ] Current page indicated (`aria-current="page"`)
- [ ] Submenus keyboard accessible (arrow keys)
- [ ] Mobile menu button labeled ("Open menu", "Close menu")

### Modals/Dialogs
- [ ] Modal has `role="dialog"` and `aria-modal="true"`
- [ ] Modal has accessible name (`aria-labelledby` referencing title)
- [ ] Focus trapped within modal when open
- [ ] Focus moves to modal when opened
- [ ] Focus returns to trigger element when closed
- [ ] Escape key closes modal
- [ ] Background content inert (`aria-hidden="true"` on `<body>`)

### Tables
- [ ] Data tables have `<th>` headers
- [ ] Complex tables use `scope` attribute
- [ ] Table has `<caption>` or `aria-label`
- [ ] Layout tables use `role="presentation"` (avoid if possible)

### Headings
- [ ] Page has one and only one `<h1>`
- [ ] Heading hierarchy is logical (no skipped levels)
- [ ] Headings describe the content that follows

### Landmarks
- [ ] Page has main landmark (`<main>` or `role="main"`)
- [ ] Multiple landmarks of same type labeled (`aria-label`)
- [ ] All content within landmarks
- [ ] Common landmarks: `<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>`

### Carousels/Sliders
- [ ] Carousel can be paused/stopped
- [ ] Keyboard accessible (arrow keys, Tab)
- [ ] Current slide indicated (`aria-current="true"`)
- [ ] Accessible labels for controls
- [ ] Auto-play can be disabled

### Live Regions
- [ ] Dynamic content updates announced (`role="status"`, `role="alert"`, or `aria-live`)
- [ ] Use `aria-live="polite"` for non-urgent updates
- [ ] Use `aria-live="assertive"` or `role="alert"` for urgent updates
- [ ] Use `role="status"` for status updates (loading, success)

---

## Testing Checklist

### Automated Testing
- [ ] Run jest-axe tests on all components
- [ ] No critical or serious violations
- [ ] Moderate violations documented and planned for fix
- [ ] CI/CD fails on critical violations

### Manual Testing

#### Keyboard Navigation
- [ ] Tab through entire page
- [ ] All interactive elements reachable
- [ ] Focus indicator always visible
- [ ] Tab order follows visual order
- [ ] Shift+Tab works correctly
- [ ] Enter/Space activate buttons and links
- [ ] Escape closes modals/menus
- [ ] Arrow keys work in custom components (dropdowns, tabs, etc.)

#### Screen Reader Testing
Test with at least one screen reader:
- [ ] **NVDA** (Windows, free)
- [ ] **JAWS** (Windows, commercial)
- [ ] **VoiceOver** (macOS/iOS, built-in)

Checklist:
- [ ] All content announced
- [ ] Landmarks navigable (use landmarks menu)
- [ ] Headings navigable (use headings menu)
- [ ] Forms navigable (use forms menu)
- [ ] Links have descriptive names
- [ ] Images have appropriate alt text
- [ ] Dynamic content announced (alerts, status)

#### Visual Testing
- [ ] Zoom to 200% - no content loss, no horizontal scroll
- [ ] Increase text spacing - content still readable
- [ ] Disable CSS - content order makes sense
- [ ] Test on small viewport (320px width)
- [ ] Test in high contrast mode (Windows High Contrast)

#### Color and Contrast
- [ ] Use browser dev tools or axe DevTools
- [ ] Check all text against background
- [ ] Check all interactive elements (buttons, links, inputs)
- [ ] Check focus indicators
- [ ] Test in grayscale (simulate color blindness)

---

## Browser and Tool Testing

### Required Browsers
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (macOS/iOS)

### Accessibility Tools
- [ ] **axe DevTools** - Browser extension for automated testing
- [ ] **WAVE** - Browser extension for visual feedback
- [ ] **Lighthouse** - Chrome DevTools accessibility audit
- [ ] **Color Contrast Analyzer** - Desktop app for contrast checking
- [ ] **Screen Reader** - Test with NVDA, JAWS, or VoiceOver

---

## Definition of Done

A feature is accessibility-ready when:
- [ ] All automated tests pass (jest-axe)
- [ ] Manual keyboard testing completed
- [ ] Screen reader testing completed (at least one reader)
- [ ] Color contrast verified
- [ ] Zoom testing completed (200%)
- [ ] Documentation updated
- [ ] Team reviewed accessibility considerations
- [ ] No critical or serious violations remain
- [ ] Moderate violations documented with remediation plan

---

## Resources

### WCAG 2.2 Guidelines
- [WCAG 2.2 Official Guidelines](https://www.w3.org/TR/WCAG22/)
- [WCAG 2.2 Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/)

### Testing Tools
- [jest-axe](https://github.com/nickcolley/jest-axe) - Automated testing library
- [axe DevTools](https://www.deque.com/axe/devtools/) - Browser extension
- [WAVE](https://wave.webaim.org/extension/) - Visual feedback tool
- [NVDA](https://www.nvaccess.org/) - Free screen reader (Windows)

### Learning Resources
- [WebAIM](https://webaim.org/) - Web accessibility guidance
- [A11y Project](https://www.a11yproject.com/) - Community-driven accessibility resources
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility) - Technical documentation

### ARIA Authoring Practices
- [ARIA Authoring Practices Guide (APG)](https://www.w3.org/WAI/ARIA/apg/) - Patterns for common widgets

---

## Contact

For accessibility questions or concerns:
- Review this checklist
- Consult the [Accessibility Testing Guide](./accessibility-testing.md)
- Review the [Accessible Patterns Guide](./accessible-patterns.md)
- Run automated tests with jest-axe
- Test with axe DevTools browser extension

Last updated: 2025-11-10
