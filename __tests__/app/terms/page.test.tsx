import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TermsOfServicePage from '@/app/terms/page';

// Mock window.print
global.print = jest.fn();

// Mock URL methods
global.URL.createObjectURL = jest.fn(() => 'blob:mock-url');
global.URL.revokeObjectURL = jest.fn();

describe('Terms of Service Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders page title', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText('Terms of Service')).toBeInTheDocument();
  });

  it('displays version information', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/Version:/)).toBeInTheDocument();
    expect(screen.getByText(/1.0/)).toBeInTheDocument();
  });

  it('displays last updated date', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/Last Updated:/)).toBeInTheDocument();
    expect(screen.getByText(/January 1, 2025/)).toBeInTheDocument();
  });

  it('renders table of contents', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText('Table of Contents')).toBeInTheDocument();
  });

  it('renders all main sections in table of contents', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText('1. Acceptance of Terms')).toBeInTheDocument();
    expect(screen.getByText('2. User Accounts and Responsibilities')).toBeInTheDocument();
    expect(screen.getByText('3. Membership Tiers and Benefits')).toBeInTheDocument();
    expect(screen.getByText('4. Payment Terms and Billing')).toBeInTheDocument();
    expect(screen.getByText('5. Refund and Cancellation Policy')).toBeInTheDocument();
    expect(screen.getByText('6. Content Ownership and License')).toBeInTheDocument();
    expect(screen.getByText('7. Prohibited Conduct')).toBeInTheDocument();
    expect(screen.getByText('8. Service Availability and Maintenance')).toBeInTheDocument();
    expect(screen.getByText('9. Disclaimers and Limitation of Liability')).toBeInTheDocument();
    expect(screen.getByText('10. Indemnification')).toBeInTheDocument();
    expect(screen.getByText('11. Dispute Resolution and Governing Law')).toBeInTheDocument();
    expect(screen.getByText('12. Account Termination')).toBeInTheDocument();
    expect(screen.getByText('13. Changes to Terms')).toBeInTheDocument();
    expect(screen.getByText('14. Contact Information')).toBeInTheDocument();
  });

  it('renders Acceptance of Terms section', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/Welcome to the Worldwide Martial Arts Association/)).toBeInTheDocument();
    expect(screen.getByText(/legally binding agreement/i)).toBeInTheDocument();
  });

  it('describes membership tiers', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/Basic Membership/i)).toBeInTheDocument();
    expect(screen.getByText(/Standard Membership/i)).toBeInTheDocument();
    expect(screen.getByText(/Premium Membership/i)).toBeInTheDocument();
  });

  it('includes membership prices', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/\$29\.99\/month/)).toBeInTheDocument();
    expect(screen.getByText(/\$99\.99\/month/)).toBeInTheDocument();
  });

  it('describes payment terms', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/Billing Cycles:/)).toBeInTheDocument();
    expect(screen.getByText(/Auto-Renewal:/)).toBeInTheDocument();
    expect(screen.getByText(/Payment Methods:/)).toBeInTheDocument();
  });

  it('mentions Stripe for payment processing', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/Stripe/i)).toBeInTheDocument();
    expect(screen.getByText(/PCI-DSS Level 1/i)).toBeInTheDocument();
  });

  it('describes refund policy', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/30-Day Money-Back Guarantee/i)).toBeInTheDocument();
  });

  it('includes event cancellation policy', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/More than 14 days before event/i)).toBeInTheDocument();
    expect(screen.getByText(/7-14 days before event/i)).toBeInTheDocument();
  });

  it('describes prohibited conduct', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/Illegal Activities/i)).toBeInTheDocument();
    expect(screen.getByText(/Harmful Behavior/i)).toBeInTheDocument();
    expect(screen.getByText(/Platform Abuse/i)).toBeInTheDocument();
  });

  it('includes martial arts safety disclaimer', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/MARTIAL ARTS TRAINING INVOLVES PHYSICAL ACTIVITY/i)).toBeInTheDocument();
    expect(screen.getByText(/Consult a physician/i)).toBeInTheDocument();
  });

  it('includes liability limitations', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/AS IS AND AS AVAILABLE/i)).toBeInTheDocument();
    expect(screen.getByText(/\$100/)).toBeInTheDocument();
  });

  it('describes arbitration clause', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/Binding Arbitration/i)).toBeInTheDocument();
    expect(screen.getByText(/American Arbitration Association/i)).toBeInTheDocument();
  });

  it('includes account termination section', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/Termination by You/i)).toBeInTheDocument();
    expect(screen.getByText(/Termination by WWMAA/i)).toBeInTheDocument();
  });

  it('provides contact information', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/legal@wwmaa.org/)).toBeInTheDocument();
    expect(screen.getByText(/support@wwmaa.org/)).toBeInTheDocument();
  });

  it('renders Print button', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByRole('button', { name: /Print/i })).toBeInTheDocument();
  });

  it('renders Download button', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByRole('button', { name: /Download/i })).toBeInTheDocument();
  });

  it('triggers print when Print button is clicked', async () => {
    const user = userEvent.setup();
    render(<TermsOfServicePage />);

    const printButton = screen.getByRole('button', { name: /Print/i });
    await user.click(printButton);

    expect(window.print).toHaveBeenCalled();
  });

  it('triggers download when Download button is clicked', async () => {
    const user = userEvent.setup();
    const mockClick = jest.fn();
    const mockAppendChild = jest.spyOn(document.body, 'appendChild').mockImplementation(() => null as any);
    const mockRemoveChild = jest.spyOn(document.body, 'removeChild').mockImplementation(() => null as any);

    const originalCreateElement = document.createElement.bind(document);
    jest.spyOn(document, 'createElement').mockImplementation((tagName) => {
      const element = originalCreateElement(tagName);
      if (tagName === 'a') {
        element.click = mockClick;
      }
      return element;
    });

    render(<TermsOfServicePage />);

    const downloadButton = screen.getByRole('button', { name: /Download/i });
    await user.click(downloadButton);

    await waitFor(() => {
      expect(mockClick).toHaveBeenCalled();
    });

    mockAppendChild.mockRestore();
    mockRemoveChild.mockRestore();
  });

  it('has proper semantic HTML structure', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByRole('article')).toBeInTheDocument();
  });

  it('includes schema.org markup', () => {
    const { container } = render(<TermsOfServicePage />);

    const article = container.querySelector('article[itemScope][itemType]');
    expect(article).toHaveAttribute('itemType', 'https://schema.org/Article');
  });

  it('renders all section IDs for anchor navigation', () => {
    const { container } = render(<TermsOfServicePage />);

    expect(container.querySelector('#introduction')).toBeInTheDocument();
    expect(container.querySelector('#accounts')).toBeInTheDocument();
    expect(container.querySelector('#membership')).toBeInTheDocument();
    expect(container.querySelector('#payments')).toBeInTheDocument();
    expect(container.querySelector('#refunds')).toBeInTheDocument();
    expect(container.querySelector('#content')).toBeInTheDocument();
    expect(container.querySelector('#conduct')).toBeInTheDocument();
    expect(container.querySelector('#availability')).toBeInTheDocument();
    expect(container.querySelector('#liability')).toBeInTheDocument();
    expect(container.querySelector('#indemnification')).toBeInTheDocument();
    expect(container.querySelector('#disputes')).toBeInTheDocument();
    expect(container.querySelector('#termination')).toBeInTheDocument();
    expect(container.querySelector('#changes')).toBeInTheDocument();
    expect(container.querySelector('#contact')).toBeInTheDocument();
  });

  it('includes content ownership section', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/WWMAA Content/i)).toBeInTheDocument();
    expect(screen.getByText(/User-Generated Content/i)).toBeInTheDocument();
  });

  it('includes indemnification clause', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/indemnify, defend, and hold harmless/i)).toBeInTheDocument();
  });

  it('describes service availability', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/99.9% uptime/i)).toBeInTheDocument();
  });

  it('includes changes to terms section', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/Material changes take effect 30 days/i)).toBeInTheDocument();
  });

  it('has proper age requirement', () => {
    render(<TermsOfServicePage />);

    expect(screen.getByText(/at least 13 years old/i)).toBeInTheDocument();
    expect(screen.getByText(/users under 18 require parental consent/i)).toBeInTheDocument();
  });
});
