import React from 'react';
import { render, screen } from '@testing-library/react';
import {
  LegalSection,
  LegalSubsection,
  LegalParagraph,
  LegalList,
  LegalHighlight,
  LegalContactBox,
} from '@/components/legal/legal-section';

describe('LegalSection', () => {
  it('renders with id and title', () => {
    render(
      <LegalSection id="test-section" title="Test Section">
        <p>Content</p>
      </LegalSection>
    );

    expect(screen.getByText('Test Section')).toBeInTheDocument();
    const section = screen.getByText('Content').closest('section');
    expect(section).toHaveAttribute('id', 'test-section');
  });

  it('renders children content', () => {
    render(
      <LegalSection id="test" title="Title">
        <p>First paragraph</p>
        <p>Second paragraph</p>
      </LegalSection>
    );

    expect(screen.getByText('First paragraph')).toBeInTheDocument();
    expect(screen.getByText('Second paragraph')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(
      <LegalSection id="test" title="Title" className="custom-class">
        <p>Content</p>
      </LegalSection>
    );

    const section = screen.getByText('Content').closest('section');
    expect(section).toHaveClass('custom-class');
  });

  it('has scroll margin for anchor links', () => {
    render(
      <LegalSection id="test" title="Title">
        <p>Content</p>
      </LegalSection>
    );

    const section = screen.getByText('Content').closest('section');
    expect(section).toHaveClass('scroll-mt-4');
  });

  it('is focusable with tabIndex -1', () => {
    render(
      <LegalSection id="test" title="Title">
        <p>Content</p>
      </LegalSection>
    );

    const section = screen.getByText('Content').closest('section');
    expect(section).toHaveAttribute('tabIndex', '-1');
  });
});

describe('LegalSubsection', () => {
  it('renders with title and content', () => {
    render(
      <LegalSubsection title="Subsection Title">
        <p>Subsection content</p>
      </LegalSubsection>
    );

    expect(screen.getByText('Subsection Title')).toBeInTheDocument();
    expect(screen.getByText('Subsection content')).toBeInTheDocument();
  });

  it('renders with optional id', () => {
    const { container } = render(
      <LegalSubsection id="subsection-id" title="Title">
        <p>Content</p>
      </LegalSubsection>
    );

    const subsection = container.firstChild;
    expect(subsection).toHaveAttribute('id', 'subsection-id');
  });

  it('renders without id', () => {
    const { container } = render(
      <LegalSubsection title="Title">
        <p>Content</p>
      </LegalSubsection>
    );

    const subsection = container.firstChild;
    expect(subsection).not.toHaveAttribute('id');
  });

  it('applies custom className', () => {
    const { container } = render(
      <LegalSubsection title="Title" className="custom-sub">
        <p>Content</p>
      </LegalSubsection>
    );

    const subsection = container.firstChild;
    expect(subsection).toHaveClass('custom-sub');
  });
});

describe('LegalParagraph', () => {
  it('renders children content', () => {
    render(<LegalParagraph>Test paragraph content</LegalParagraph>);

    expect(screen.getByText('Test paragraph content')).toBeInTheDocument();
  });

  it('applies default margin', () => {
    const { container } = render(<LegalParagraph>Content</LegalParagraph>);

    const paragraph = container.firstChild;
    expect(paragraph).toHaveClass('mb-4');
  });

  it('applies custom className', () => {
    const { container } = render(
      <LegalParagraph className="custom-para">Content</LegalParagraph>
    );

    const paragraph = container.firstChild;
    expect(paragraph).toHaveClass('custom-para');
  });
});

describe('LegalList', () => {
  const items = ['First item', 'Second item', 'Third item'];

  it('renders unordered list by default', () => {
    render(<LegalList items={items} />);

    expect(screen.getByText('First item')).toBeInTheDocument();
    expect(screen.getByText('Second item')).toBeInTheDocument();
    expect(screen.getByText('Third item')).toBeInTheDocument();

    const listItems = screen.getAllByRole('listitem');
    expect(listItems).toHaveLength(3);
  });

  it('renders ordered list when type is ordered', () => {
    const { container } = render(<LegalList items={items} type="ordered" />);

    const orderedList = container.querySelector('ol');
    expect(orderedList).toBeInTheDocument();
    expect(orderedList).toHaveClass('list-decimal');
  });

  it('renders unordered list when type is unordered', () => {
    const { container } = render(<LegalList items={items} type="unordered" />);

    const unorderedList = container.querySelector('ul');
    expect(unorderedList).toBeInTheDocument();
    expect(unorderedList).toHaveClass('list-disc');
  });

  it('handles items with JSX content', () => {
    const jsxItems = [
      'Plain text',
      <><strong>Bold</strong> text</>,
      <>Text with <em>emphasis</em></>,
    ];

    render(<LegalList items={jsxItems} />);

    expect(screen.getByText('Bold')).toBeInTheDocument();
    expect(screen.getByText('emphasis')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <LegalList items={items} className="custom-list" />
    );

    const list = container.querySelector('ul');
    expect(list).toHaveClass('custom-list');
  });

  it('handles empty items array', () => {
    render(<LegalList items={[]} />);

    const listItems = screen.queryAllByRole('listitem');
    expect(listItems).toHaveLength(0);
  });
});

describe('LegalHighlight', () => {
  it('renders with default info variant', () => {
    const { container } = render(
      <LegalHighlight>
        <p>Highlighted content</p>
      </LegalHighlight>
    );

    expect(screen.getByText('Highlighted content')).toBeInTheDocument();
    const highlight = container.firstChild;
    expect(highlight).toHaveClass('bg-blue-50');
  });

  it('renders with warning variant', () => {
    const { container } = render(
      <LegalHighlight variant="warning">
        <p>Warning content</p>
      </LegalHighlight>
    );

    const highlight = container.firstChild;
    expect(highlight).toHaveClass('bg-amber-50');
  });

  it('renders with important variant', () => {
    const { container } = render(
      <LegalHighlight variant="important">
        <p>Important content</p>
      </LegalHighlight>
    );

    const highlight = container.firstChild;
    expect(highlight).toHaveClass('bg-red-50');
  });

  it('applies custom className', () => {
    const { container } = render(
      <LegalHighlight className="custom-highlight">
        <p>Content</p>
      </LegalHighlight>
    );

    const highlight = container.firstChild;
    expect(highlight).toHaveClass('custom-highlight');
  });

  it('has border styling', () => {
    const { container } = render(
      <LegalHighlight>
        <p>Content</p>
      </LegalHighlight>
    );

    const highlight = container.firstChild;
    expect(highlight).toHaveClass('border-l-4');
  });
});

describe('LegalContactBox', () => {
  const baseProps = {
    title: 'Privacy Officer',
    organization: 'Test Organization',
    email: 'privacy@test.com',
  };

  it('renders with required props only', () => {
    render(<LegalContactBox {...baseProps} />);

    expect(screen.getByText('Privacy Officer')).toBeInTheDocument();
    expect(screen.getByText('Test Organization')).toBeInTheDocument();
    expect(screen.getByText('privacy@test.com')).toBeInTheDocument();
  });

  it('renders email as link', () => {
    render(<LegalContactBox {...baseProps} />);

    const emailLink = screen.getByRole('link', { name: /privacy@test.com/i });
    expect(emailLink).toHaveAttribute('href', 'mailto:privacy@test.com');
  });

  it('renders support email when provided', () => {
    render(
      <LegalContactBox
        {...baseProps}
        supportEmail="support@test.com"
      />
    );

    expect(screen.getByText('support@test.com')).toBeInTheDocument();
    const supportLink = screen.getByRole('link', { name: /support@test.com/i });
    expect(supportLink).toHaveAttribute('href', 'mailto:support@test.com');
  });

  it('renders mailing address when provided', () => {
    render(
      <LegalContactBox
        {...baseProps}
        mailingAddress={{
          line1: '123 Main St',
          line2: 'Suite 100',
          city: 'New York',
          state: 'NY',
          zip: '10001',
          country: 'United States',
        }}
      />
    );

    expect(screen.getByText(/123 Main St/)).toBeInTheDocument();
    expect(screen.getByText(/Suite 100/)).toBeInTheDocument();
    expect(screen.getByText(/New York, NY 10001/)).toBeInTheDocument();
    expect(screen.getByText(/United States/)).toBeInTheDocument();
  });

  it('renders mailing address without line2', () => {
    render(
      <LegalContactBox
        {...baseProps}
        mailingAddress={{
          line1: '123 Main St',
          city: 'New York',
          state: 'NY',
          zip: '10001',
        }}
      />
    );

    expect(screen.getByText(/123 Main St/)).toBeInTheDocument();
    expect(screen.getByText(/New York, NY 10001/)).toBeInTheDocument();
  });

  it('defaults to United States when country not provided', () => {
    render(
      <LegalContactBox
        {...baseProps}
        mailingAddress={{
          line1: '123 Main St',
          city: 'New York',
          state: 'NY',
          zip: '10001',
        }}
      />
    );

    expect(screen.getByText(/United States/)).toBeInTheDocument();
  });

  it('renders response time when provided', () => {
    render(
      <LegalContactBox
        {...baseProps}
        responseTime="We will respond within 30 days"
      />
    );

    expect(screen.getByText('We will respond within 30 days')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <LegalContactBox {...baseProps} className="custom-contact" />
    );

    const contactBox = container.firstChild;
    expect(contactBox).toHaveClass('custom-contact');
  });

  it('has proper structure with border and background', () => {
    const { container } = render(<LegalContactBox {...baseProps} />);

    const contactBox = container.firstChild;
    expect(contactBox).toHaveClass('border', 'rounded-lg', 'p-6');
  });
});
