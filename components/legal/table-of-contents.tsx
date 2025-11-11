'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

export interface TableOfContentsItem {
  id: string;
  title: string;
  subsections?: TableOfContentsItem[];
}

interface TableOfContentsProps {
  /**
   * Array of section items to display in the table of contents
   */
  items: TableOfContentsItem[];

  /**
   * Title for the table of contents
   * @default "Table of Contents"
   */
  title?: string;

  /**
   * Whether to show the table of contents (useful for print hiding)
   * @default true
   */
  visible?: boolean;

  /**
   * Custom class name for the container
   */
  className?: string;
}

/**
 * Table of Contents Component
 *
 * Displays a navigable table of contents for legal documents with smooth scrolling.
 * Supports nested subsections and is automatically hidden when printing.
 *
 * Features:
 * - Smooth scrolling to sections
 * - Nested subsection support
 * - Keyboard accessible
 * - Automatically hidden when printing
 * - Responsive design
 *
 * @example
 * ```tsx
 * const sections = [
 *   { id: 'introduction', title: '1. Introduction' },
 *   {
 *     id: 'data-collected',
 *     title: '2. Information We Collect',
 *     subsections: [
 *       { id: 'data-provided', title: '2.1 Information You Provide' },
 *       { id: 'data-automatic', title: '2.2 Automatically Collected' },
 *     ]
 *   },
 * ];
 *
 * <TableOfContents items={sections} />
 * ```
 */
export function TableOfContents({
  items,
  title = 'Table of Contents',
  visible = true,
  className = '',
}: TableOfContentsProps) {
  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      // Add focus for accessibility
      element.focus({ preventScroll: true });
    }
  };

  if (!visible) {
    return null;
  }

  return (
    <Card className={`print:hidden ${className}`}>
      <CardContent className="pt-6">
        <h2 className="text-lg font-semibold mb-3">{title}</h2>
        <nav aria-label="Table of contents">
          <ul className="space-y-2">
            {items.map((item) => (
              <li key={item.id}>
                <button
                  onClick={() => scrollToSection(item.id)}
                  className="block text-sm text-primary hover:underline text-left w-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded px-2 py-1 -ml-2"
                  aria-label={`Jump to ${item.title}`}
                >
                  {item.title}
                </button>
                {item.subsections && item.subsections.length > 0 && (
                  <ul className="ml-4 mt-1 space-y-1">
                    {item.subsections.map((subsection) => (
                      <li key={subsection.id}>
                        <button
                          onClick={() => scrollToSection(subsection.id)}
                          className="block text-sm text-muted-foreground hover:text-primary hover:underline text-left w-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded px-2 py-1 -ml-2"
                          aria-label={`Jump to ${subsection.title}`}
                        >
                          {subsection.title}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </nav>
      </CardContent>
    </Card>
  );
}

/**
 * Compact Table of Contents Component
 *
 * A more compact version without the card wrapper, useful for sidebars.
 */
export function CompactTableOfContents({
  items,
  title = 'Table of Contents',
  className = '',
}: Omit<TableOfContentsProps, 'visible'>) {
  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      element.focus({ preventScroll: true });
    }
  };

  return (
    <div className={`print:hidden ${className}`}>
      <h2 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wider">
        {title}
      </h2>
      <nav aria-label="Table of contents">
        <ul className="space-y-1 border-l-2 border-border pl-4">
          {items.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => scrollToSection(item.id)}
                className="block text-sm text-foreground hover:text-primary text-left w-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary rounded py-1"
                aria-label={`Jump to ${item.title}`}
              >
                {item.title}
              </button>
              {item.subsections && item.subsections.length > 0 && (
                <ul className="ml-2 mt-1 space-y-1">
                  {item.subsections.map((subsection) => (
                    <li key={subsection.id}>
                      <button
                        onClick={() => scrollToSection(subsection.id)}
                        className="block text-xs text-muted-foreground hover:text-primary text-left w-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary rounded py-1"
                        aria-label={`Jump to ${subsection.title}`}
                      >
                        {subsection.title}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
