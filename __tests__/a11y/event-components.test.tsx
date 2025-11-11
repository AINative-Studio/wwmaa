/**
 * Accessibility Tests for Event Components
 * Tests WCAG 2.2 AA compliance for event-related components
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import { runAxeTest } from '../utils/a11y'
import { EventCard } from '@/components/events/event-card'
import { ViewToggle } from '@/components/events/view-toggle'
import { EventItem } from '@/lib/types'

// Mock Next.js Image component
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => {
    // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
    return <img {...props} />
  },
}))

// Mock Next.js Link component
jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, ...props }: any) => <a {...props}>{children}</a>,
}))

// Mock event data
const mockEvent: EventItem = {
  id: '1',
  title: 'Beginner Karate Class',
  teaser: 'Learn the fundamentals of traditional Karate',
  description: 'A comprehensive introduction to Karate for beginners',
  type: 'live_training',
  location_type: 'in_person',
  location: 'Main Dojo, 123 Martial Arts Way',
  start: '2025-12-15T10:00:00Z',
  end: '2025-12-15T12:00:00Z',
  price: 25,
  visibility: 'public',
  instructor: 'Sensei John Smith',
  max_participants: 20,
  current_participants: 15,
  image: '/images/karate-class.jpg',
  created_at: '2025-11-01T00:00:00Z',
  updated_at: '2025-11-01T00:00:00Z',
}

describe('Event Components - Accessibility', () => {
  describe('EventCard', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(<EventCard event={mockEvent} />)
      const results = await runAxeTest(container)
      expect(results).toHaveNoViolations()
    })

    it('should have accessible link with descriptive aria-label', () => {
      render(<EventCard event={mockEvent} />)
      const link = screen.getByRole('link', { name: /view details for beginner karate class/i })
      expect(link).toBeInTheDocument()
      expect(link).toHaveAccessibleName()
    })

    it('should have proper alt text for event image', () => {
      render(<EventCard event={mockEvent} />)
      const image = screen.getByAltText('Beginner Karate Class')
      expect(image).toBeInTheDocument()
    })

    it('should handle events without image gracefully', async () => {
      const eventWithoutImage = { ...mockEvent, image: null }
      const { container } = render(<EventCard event={eventWithoutImage} />)
      const results = await runAxeTest(container)
      expect(results).toHaveNoViolations()
    })

    it('should handle free events accessibly', async () => {
      const freeEvent = { ...mockEvent, price: 0 }
      const { container } = render(<EventCard event={freeEvent} />)
      const results = await runAxeTest(container)
      expect(results).toHaveNoViolations()
      expect(screen.getByText('Free')).toBeInTheDocument()
    })

    it('should handle full events accessibly', async () => {
      const fullEvent = { ...mockEvent, current_participants: 20 }
      const { container } = render(<EventCard event={fullEvent} />)
      const results = await runAxeTest(container)
      expect(results).toHaveNoViolations()
      expect(screen.getByText('Full')).toBeInTheDocument()
    })

    it('should handle members-only events accessibly', async () => {
      const membersOnlyEvent = { ...mockEvent, visibility: 'members_only' as const }
      const { container } = render(<EventCard event={membersOnlyEvent} />)
      const results = await runAxeTest(container)
      expect(results).toHaveNoViolations()
      expect(screen.getByText('Members Only')).toBeInTheDocument()
    })
  })

  describe('ViewToggle', () => {
    it('should have no accessibility violations', async () => {
      const mockOnViewChange = jest.fn()
      const { container } = render(
        <ViewToggle view="list" onViewChange={mockOnViewChange} />
      )
      const results = await runAxeTest(container)
      expect(results).toHaveNoViolations()
    })

    it('should have accessible buttons with aria-label', () => {
      const mockOnViewChange = jest.fn()
      render(<ViewToggle view="list" onViewChange={mockOnViewChange} />)

      // Verify buttons have aria-label attributes
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBe(2)

      // Check that buttons have aria-label
      buttons.forEach(button => {
        expect(button).toHaveAttribute('aria-label')
      })
    })
  })

  describe('Event Components - Color Contrast', () => {
    it('should meet color contrast requirements', async () => {
      const { container } = render(<EventCard event={mockEvent} />)
      const results = await runAxeTest(container)

      // Axe will check color contrast automatically
      const contrastViolations = results.violations.filter(
        v => v.id === 'color-contrast'
      )
      expect(contrastViolations.length).toBe(0)
    })
  })

  describe('Event Components - Screen Reader Support', () => {
    it('should announce event details properly', () => {
      render(<EventCard event={mockEvent} />)

      // Verify main link has accessible name
      const link = screen.getByRole('link', { name: /view details for beginner karate class/i })
      expect(link).toHaveAccessibleName()
    })

    it('should have proper heading structure', () => {
      render(<EventCard event={mockEvent} />)

      // EventCard uses h3 for title
      const heading = screen.getByRole('heading', { level: 3 })
      expect(heading).toBeInTheDocument()
      expect(heading).toHaveTextContent('Beginner Karate Class')
    })
  })
})
