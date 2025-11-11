import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TableOfContents, CompactTableOfContents, TableOfContentsItem } from '@/components/legal/table-of-contents';

// Mock scrollIntoView
Element.prototype.scrollIntoView = jest.fn();

describe('TableOfContents', () => {
  const mockItems: TableOfContentsItem[] = [
    { id: 'section-1', title: '1. Introduction' },
    {
      id: 'section-2',
      title: '2. Main Content',
      subsections: [
        { id: 'section-2-1', title: '2.1 Subsection One' },
        { id: 'section-2-2', title: '2.2 Subsection Two' },
      ],
    },
    { id: 'section-3', title: '3. Conclusion' },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders with default title', () => {
    render(<TableOfContents items={mockItems} />);

    expect(screen.getByText('Table of Contents')).toBeInTheDocument();
  });

  it('renders with custom title', () => {
    render(<TableOfContents items={mockItems} title="Custom Title" />);

    expect(screen.getByText('Custom Title')).toBeInTheDocument();
  });

  it('renders all main sections', () => {
    render(<TableOfContents items={mockItems} />);

    expect(screen.getByText('1. Introduction')).toBeInTheDocument();
    expect(screen.getByText('2. Main Content')).toBeInTheDocument();
    expect(screen.getByText('3. Conclusion')).toBeInTheDocument();
  });

  it('renders subsections', () => {
    render(<TableOfContents items={mockItems} />);

    expect(screen.getByText('2.1 Subsection One')).toBeInTheDocument();
    expect(screen.getByText('2.2 Subsection Two')).toBeInTheDocument();
  });

  it('does not render when visible is false', () => {
    render(<TableOfContents items={mockItems} visible={false} />);

    expect(screen.queryByText('Table of Contents')).not.toBeInTheDocument();
  });

  it('scrolls to section when clicked', async () => {
    const user = userEvent.setup();
    const mockElement = document.createElement('div');
    mockElement.id = 'section-1';
    const mockFocus = jest.fn();
    Object.defineProperty(mockElement, 'focus', {
      writable: true,
      value: mockFocus,
    });
    document.body.appendChild(mockElement);

    render(<TableOfContents items={mockItems} />);

    const button = screen.getByText('1. Introduction');
    await user.click(button);

    expect(mockElement.scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'start',
    });
    expect(mockFocus).toHaveBeenCalledWith({ preventScroll: true });

    document.body.removeChild(mockElement);
  });

  it('scrolls to subsection when clicked', async () => {
    const user = userEvent.setup();
    const mockElement = document.createElement('div');
    mockElement.id = 'section-2-1';
    const mockFocus = jest.fn();
    Object.defineProperty(mockElement, 'focus', {
      writable: true,
      value: mockFocus,
    });
    document.body.appendChild(mockElement);

    render(<TableOfContents items={mockItems} />);

    const button = screen.getByText('2.1 Subsection One');
    await user.click(button);

    expect(mockElement.scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'start',
    });

    document.body.removeChild(mockElement);
  });

  it('handles missing section element gracefully', async () => {
    const user = userEvent.setup();
    render(<TableOfContents items={mockItems} />);

    const button = screen.getByText('1. Introduction');
    await user.click(button);

    // Should not throw error
    expect(true).toBe(true);
  });

  it('has proper ARIA attributes', () => {
    render(<TableOfContents items={mockItems} />);

    const nav = screen.getByRole('navigation', { name: /table of contents/i });
    expect(nav).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <TableOfContents items={mockItems} className="custom-class" />
    );

    const card = container.firstChild;
    expect(card).toHaveClass('custom-class');
  });

  it('renders section buttons with proper ARIA labels', () => {
    render(<TableOfContents items={mockItems} />);

    const button = screen.getByLabelText('Jump to 1. Introduction');
    expect(button).toBeInTheDocument();
  });

  it('has keyboard focus indicators', () => {
    render(<TableOfContents items={mockItems} />);

    const button = screen.getByText('1. Introduction');
    expect(button).toHaveClass('focus:outline-none', 'focus:ring-2', 'focus:ring-primary');
  });
});

describe('CompactTableOfContents', () => {
  const mockItems: TableOfContentsItem[] = [
    { id: 'section-1', title: '1. Introduction' },
    {
      id: 'section-2',
      title: '2. Main Content',
      subsections: [
        { id: 'section-2-1', title: '2.1 Subsection One' },
      ],
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders with default title', () => {
    render(<CompactTableOfContents items={mockItems} />);

    expect(screen.getByText('Table of Contents')).toBeInTheDocument();
  });

  it('renders with custom title', () => {
    render(<CompactTableOfContents items={mockItems} title="Quick Nav" />);

    expect(screen.getByText('Quick Nav')).toBeInTheDocument();
  });

  it('renders all sections', () => {
    render(<CompactTableOfContents items={mockItems} />);

    expect(screen.getByText('1. Introduction')).toBeInTheDocument();
    expect(screen.getByText('2. Main Content')).toBeInTheDocument();
  });

  it('renders subsections', () => {
    render(<CompactTableOfContents items={mockItems} />);

    expect(screen.getByText('2.1 Subsection One')).toBeInTheDocument();
  });

  it('scrolls to section when clicked', async () => {
    const user = userEvent.setup();
    const mockElement = document.createElement('div');
    mockElement.id = 'section-1';
    const mockFocus = jest.fn();
    Object.defineProperty(mockElement, 'focus', {
      writable: true,
      value: mockFocus,
    });
    document.body.appendChild(mockElement);

    render(<CompactTableOfContents items={mockItems} />);

    const button = screen.getByText('1. Introduction');
    await user.click(button);

    expect(mockElement.scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'start',
    });

    document.body.removeChild(mockElement);
  });

  it('applies custom className', () => {
    const { container } = render(
      <CompactTableOfContents items={mockItems} className="custom-compact" />
    );

    const div = container.firstChild;
    expect(div).toHaveClass('custom-compact');
  });

  it('has different styling than regular TableOfContents', () => {
    const { container: regularContainer } = render(
      <TableOfContents items={mockItems} />
    );
    const { container: compactContainer } = render(
      <CompactTableOfContents items={mockItems} />
    );

    // Regular has Card component
    expect(regularContainer.querySelector('[class*="rounded"]')).toBeTruthy();
    // Compact does not have Card
    expect(compactContainer.querySelector('[class*="border-l-2"]')).toBeTruthy();
  });

  it('has proper ARIA attributes', () => {
    render(<CompactTableOfContents items={mockItems} />);

    const nav = screen.getByRole('navigation', { name: /table of contents/i });
    expect(nav).toBeInTheDocument();
  });
});

describe('TableOfContents - Edge Cases', () => {
  it('handles empty items array', () => {
    render(<TableOfContents items={[]} />);

    expect(screen.getByText('Table of Contents')).toBeInTheDocument();
    // Should render but have no section buttons
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('handles items without subsections', () => {
    const items: TableOfContentsItem[] = [
      { id: 'section-1', title: '1. Section One' },
      { id: 'section-2', title: '2. Section Two' },
    ];

    render(<TableOfContents items={items} />);

    expect(screen.getByText('1. Section One')).toBeInTheDocument();
    expect(screen.getByText('2. Section Two')).toBeInTheDocument();
  });

  it('handles items with empty subsections array', () => {
    const items: TableOfContentsItem[] = [
      {
        id: 'section-1',
        title: '1. Section One',
        subsections: [],
      },
    ];

    render(<TableOfContents items={items} />);

    expect(screen.getByText('1. Section One')).toBeInTheDocument();
  });

  it('handles deeply nested items structure', () => {
    const items: TableOfContentsItem[] = [
      {
        id: 'section-1',
        title: '1. Main Section',
        subsections: [
          { id: 'sub-1', title: '1.1 Subsection' },
          { id: 'sub-2', title: '1.2 Subsection' },
          { id: 'sub-3', title: '1.3 Subsection' },
        ],
      },
    ];

    render(<TableOfContents items={items} />);

    expect(screen.getByText('1.1 Subsection')).toBeInTheDocument();
    expect(screen.getByText('1.2 Subsection')).toBeInTheDocument();
    expect(screen.getByText('1.3 Subsection')).toBeInTheDocument();
  });
});
