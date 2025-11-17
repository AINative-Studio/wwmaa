# Modal Styling Reference Guide

## Quick Overview

All modals in the WWMAA application now follow consistent styling guidelines for optimal user experience across all devices.

## Base Modal Styling

### Standard Modal (components/ui/dialog.tsx)

```tsx
<Dialog>
  <DialogContent className="sm:max-w-[500px]">
    {/* Your modal content */}
  </DialogContent>
</Dialog>
```

**Default Features:**
- ✅ Solid white background (`bg-white`)
- ✅ Dark backdrop overlay (80% black with blur)
- ✅ Shadow effect (`shadow-xl`)
- ✅ Rounded corners on all devices (`rounded-lg`)
- ✅ Proper mobile margins (`w-[calc(100%-2rem)]`)
- ✅ Centered positioning
- ✅ Close button (top-right)
- ✅ Smooth animations

### Scrollable Modal (for long content)

```tsx
<Dialog>
  <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
    {/* Your long form content */}
  </DialogContent>
</Dialog>
```

**When to use:**
- Forms with many fields (5+ inputs)
- Content that may exceed viewport height
- Mobile-first designs
- Dynamic content with unknown height

### Wide Modal (for tables/complex layouts)

```tsx
<Dialog>
  <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
    {/* Your wide content */}
  </DialogContent>
</Dialog>
```

**Common widths:**
- `sm:max-w-[500px]` - Default (forms, simple content)
- `max-w-2xl` - Wide (tables, complex forms)
- `max-w-4xl` - Extra wide (dashboards, data views)
- `max-w-7xl` - Full-screen-like (image galleries, media)

### Full-Screen Modal (for immersive content)

```tsx
<Dialog>
  <DialogContent className="max-w-7xl w-full h-[90vh] p-0">
    {/* Your immersive content */}
  </DialogContent>
</Dialog>
```

**Example:** Image lightbox, video player, embedded documents

## Styling Components

### Backdrop/Overlay
```css
bg-black/80 backdrop-blur-sm
```
- 80% opacity black background
- Slight blur effect on background content
- Draws focus to modal
- Still shows context behind modal

### Modal Container
```css
bg-white border border-gray-200 shadow-xl rounded-lg
```
- Pure white background (no transparency)
- Light gray border for definition
- Strong shadow for depth
- Rounded corners for modern look

### Mobile Handling
```css
w-[calc(100%-2rem)] sm:w-full
```
- 1rem (16px) margin on mobile
- Full width on desktop (within max-width)
- Prevents edge-to-edge modals
- Better touch targets

### Height Constraints
```css
max-h-[90vh] overflow-y-auto
```
- Maximum 90% of viewport height
- Automatic scrolling when needed
- Leaves space for browser chrome
- Prevents content overflow

## Common Patterns

### Simple Alert/Confirmation

```tsx
<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <DialogContent className="sm:max-w-[400px]">
    <DialogHeader>
      <DialogTitle>Confirm Action</DialogTitle>
      <DialogDescription>
        Are you sure you want to proceed?
      </DialogDescription>
    </DialogHeader>
    <DialogFooter>
      <Button variant="outline" onClick={() => setIsOpen(false)}>
        Cancel
      </Button>
      <Button onClick={handleConfirm}>
        Confirm
      </Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### Form Modal

```tsx
<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
    <DialogHeader>
      <DialogTitle>Create New Item</DialogTitle>
      <DialogDescription>
        Fill in the details below
      </DialogDescription>
    </DialogHeader>
    <div className="space-y-4 py-4">
      {/* Form fields */}
    </div>
    <DialogFooter>
      <Button variant="outline" onClick={() => setIsOpen(false)}>
        Cancel
      </Button>
      <Button onClick={handleSubmit}>
        Create
      </Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### Data View Modal

```tsx
<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
    <DialogHeader>
      <DialogTitle>View Details</DialogTitle>
      <DialogDescription>
        Complete information about this item
      </DialogDescription>
    </DialogHeader>
    <div className="space-y-6 py-4">
      {/* Tables, charts, complex layouts */}
    </div>
    <DialogFooter>
      <Button variant="outline" onClick={() => setIsOpen(false)}>
        Close
      </Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

## Responsive Breakpoints

### Mobile (< 640px)
- Modal: `w-[calc(100%-2rem)]` (viewport width minus 2rem)
- Max Width: Ignored (full available width)
- Padding: 1rem on each side

### Tablet (640px - 1024px)
- Modal: `w-full` (within max-width constraint)
- Max Width: Applied (e.g., 500px)
- Padding: Natural based on max-width

### Desktop (> 1024px)
- Modal: `w-full` (within max-width constraint)
- Max Width: Applied (e.g., 500px)
- Padding: Centered with backdrop

## Accessibility Features

### Keyboard Navigation
- `Esc` - Close modal
- `Tab` - Navigate between focusable elements
- `Enter` - Activate buttons/links
- `Space` - Toggle checkboxes/switches

### Screen Reader Support
- Proper ARIA labels
- Descriptive titles and descriptions
- Close button with "Close" label
- Focus management (modal traps focus)

### Visual Features
- High contrast (80% backdrop)
- Clear borders and shadows
- Visible focus indicators
- Adequate touch targets (44px minimum)

## Best Practices

### DO ✅
- Use descriptive titles and descriptions
- Add max-height for scrollable content
- Include cancel/close actions
- Provide clear primary action
- Test on mobile devices
- Ensure keyboard accessibility
- Handle loading states in forms

### DON'T ❌
- Create modals within modals (nested)
- Make modals edge-to-edge on mobile
- Use very small max-widths (< 320px)
- Omit close button
- Use transparent backgrounds
- Create modals taller than viewport
- Block all user interactions indefinitely

## Examples in Codebase

### Admin Dashboard Modals
Location: `app/dashboard/admin/page.tsx`

1. **Add Member Modal** (Line 1402)
2. **Add Instructor Modal** (Line 1451)
3. **Create Event Modal** (Line 1485) ⭐ Primary example
4. **Edit Tier Modal** (Line 1618)

### Cookie Settings Modal
Location: `components/cookie-consent/cookie-settings-modal.tsx`

- Wide modal with scrolling
- Complex nested content
- Multiple sections

### Image Gallery Modal
Location: `components/search/image-gallery.tsx`

- Full-screen lightbox style
- Dark background (intentional)
- Custom styling for images

## Custom Styling

If you need to override default styles:

```tsx
<DialogContent className="sm:max-w-[500px] bg-gradient-to-b from-blue-50 to-white">
  {/* Custom background gradient */}
</DialogContent>
```

**Note:** The `className` prop is merged with base styles using `cn()` utility, so you can override specific properties while keeping others.

## Testing Checklist

When creating a new modal:

- [ ] Looks good on mobile (< 640px)
- [ ] Looks good on tablet (640px - 1024px)
- [ ] Looks good on desktop (> 1024px)
- [ ] Scrolls properly when content is tall
- [ ] Close button works
- [ ] Click outside closes modal (if desired)
- [ ] Esc key closes modal
- [ ] Focus is trapped in modal
- [ ] Accessible to screen readers
- [ ] Loading states handled
- [ ] Error states handled
- [ ] Form validation (if applicable)

## Support

For questions or issues with modal styling:
1. Check this reference guide
2. Review existing modal examples in codebase
3. Test in browser DevTools with responsive mode
4. Refer to shadcn/ui dialog documentation
