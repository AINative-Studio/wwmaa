import React from 'react';

interface LegalSectionProps {
  /**
   * Unique ID for the section (used for anchor links)
   */
  id: string;

  /**
   * Section title (h2)
   */
  title: string;

  /**
   * Section content
   */
  children: React.ReactNode;

  /**
   * Custom class name for the section
   */
  className?: string;
}

/**
 * Legal Section Component
 *
 * Wrapper component for legal document sections with consistent styling
 * and scroll margin for smooth anchor navigation.
 *
 * Features:
 * - Semantic HTML structure
 * - Scroll margin for anchor links
 * - Consistent spacing
 * - Accessible headings
 *
 * @example
 * ```tsx
 * <LegalSection id="introduction" title="1. Introduction">
 *   <p>This is the introduction section...</p>
 * </LegalSection>
 * ```
 */
export function LegalSection({
  id,
  title,
  children,
  className = '',
}: LegalSectionProps) {
  return (
    <section id={id} className={`mb-8 scroll-mt-4 ${className}`} tabIndex={-1}>
      <h2 className="text-2xl font-semibold mb-4">{title}</h2>
      {children}
    </section>
  );
}

interface LegalSubsectionProps {
  /**
   * Unique ID for the subsection (used for anchor links)
   */
  id?: string;

  /**
   * Subsection title (h3)
   */
  title: string;

  /**
   * Subsection content
   */
  children: React.ReactNode;

  /**
   * Custom class name for the subsection
   */
  className?: string;
}

/**
 * Legal Subsection Component
 *
 * Wrapper component for subsections within legal document sections.
 *
 * @example
 * ```tsx
 * <LegalSection id="data-collected" title="2. Information We Collect">
 *   <LegalSubsection id="data-provided" title="2.1 Information You Provide">
 *     <p>We collect information you provide...</p>
 *   </LegalSubsection>
 * </LegalSection>
 * ```
 */
export function LegalSubsection({
  id,
  title,
  children,
  className = '',
}: LegalSubsectionProps) {
  return (
    <div id={id} className={`mt-6 scroll-mt-4 ${className}`} tabIndex={id ? -1 : undefined}>
      <h3 className="text-xl font-semibold mb-3">{title}</h3>
      {children}
    </div>
  );
}

interface LegalParagraphProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Legal Paragraph Component
 *
 * Styled paragraph for legal documents with consistent spacing.
 */
export function LegalParagraph({ children, className = '' }: LegalParagraphProps) {
  return <p className={`mb-4 ${className}`}>{children}</p>;
}

interface LegalListProps {
  /**
   * List items
   */
  items: React.ReactNode[];

  /**
   * List type
   * @default "unordered"
   */
  type?: 'ordered' | 'unordered';

  /**
   * Custom class name
   */
  className?: string;
}

/**
 * Legal List Component
 *
 * Styled list for legal documents with consistent spacing.
 *
 * @example
 * ```tsx
 * <LegalList
 *   items={[
 *     'First item',
 *     'Second item',
 *     <><strong>Bold:</strong> Third item with formatting</>,
 *   ]}
 * />
 * ```
 */
export function LegalList({ items, type = 'unordered', className = '' }: LegalListProps) {
  const ListTag = type === 'ordered' ? 'ol' : 'ul';
  const listClass = type === 'ordered' ? 'list-decimal' : 'list-disc';

  return (
    <ListTag className={`${listClass} pl-6 mb-4 space-y-2 ${className}`}>
      {items.map((item, index) => (
        <li key={index}>{item}</li>
      ))}
    </ListTag>
  );
}

interface LegalHighlightProps {
  children: React.ReactNode;
  variant?: 'warning' | 'info' | 'important';
  className?: string;
}

/**
 * Legal Highlight Component
 *
 * Highlighted box for important legal notices.
 *
 * @example
 * ```tsx
 * <LegalHighlight variant="warning">
 *   <p>This is an important legal notice.</p>
 * </LegalHighlight>
 * ```
 */
export function LegalHighlight({
  children,
  variant = 'info',
  className = '',
}: LegalHighlightProps) {
  const variantStyles = {
    warning: 'bg-amber-50 border-amber-200 dark:bg-amber-950 dark:border-amber-800',
    info: 'bg-blue-50 border-blue-200 dark:bg-blue-950 dark:border-blue-800',
    important: 'bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800',
  };

  return (
    <div className={`border-l-4 pl-4 my-4 ${variantStyles[variant]} ${className}`}>
      {children}
    </div>
  );
}

interface LegalContactBoxProps {
  title: string;
  organization: string;
  email: string;
  supportEmail?: string;
  mailingAddress?: {
    line1: string;
    line2?: string;
    city: string;
    state: string;
    zip: string;
    country?: string;
  };
  responseTime?: string;
  className?: string;
}

/**
 * Legal Contact Box Component
 *
 * Formatted contact information box for legal documents.
 *
 * @example
 * ```tsx
 * <LegalContactBox
 *   title="Privacy Officer"
 *   organization="WWMAA"
 *   email="privacy@wwmaa.org"
 *   supportEmail="support@wwmaa.org"
 *   mailingAddress={{
 *     line1: "123 Main St",
 *     city: "New York",
 *     state: "NY",
 *     zip: "10001",
 *     country: "United States"
 *   }}
 *   responseTime="We will respond within 30 days"
 * />
 * ```
 */
export function LegalContactBox({
  title,
  organization,
  email,
  supportEmail,
  mailingAddress,
  responseTime,
  className = '',
}: LegalContactBoxProps) {
  return (
    <div className={`border rounded-lg p-6 bg-muted/50 ${className}`}>
      <div className="space-y-3">
        <div>
          <strong>{title}</strong>
          <p className="text-sm text-muted-foreground">{organization}</p>
        </div>

        <div>
          <strong>Email:</strong>
          <p>
            <a href={`mailto:${email}`} className="text-primary hover:underline">
              {email}
            </a>
          </p>
        </div>

        {supportEmail && (
          <div>
            <strong>Support Email:</strong>
            <p>
              <a href={`mailto:${supportEmail}`} className="text-primary hover:underline">
                {supportEmail}
              </a>
            </p>
          </div>
        )}

        {mailingAddress && (
          <div>
            <strong>Mailing Address:</strong>
            <p className="text-sm">
              {mailingAddress.line1}
              <br />
              {mailingAddress.line2 && (
                <>
                  {mailingAddress.line2}
                  <br />
                </>
              )}
              {mailingAddress.city}, {mailingAddress.state} {mailingAddress.zip}
              <br />
              {mailingAddress.country || 'United States'}
            </p>
          </div>
        )}

        {responseTime && (
          <div className="pt-3 border-t">
            <strong>Response Time:</strong>
            <p className="text-sm text-muted-foreground">{responseTime}</p>
          </div>
        )}
      </div>
    </div>
  );
}
