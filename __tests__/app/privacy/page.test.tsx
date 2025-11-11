import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PrivacyPolicyPage from '@/app/privacy/page';

// Mock window.print
global.print = jest.fn();

// Mock URL.createObjectURL and URL.revokeObjectURL
global.URL.createObjectURL = jest.fn(() => 'blob:mock-url');
global.URL.revokeObjectURL = jest.fn();

describe('Privacy Policy Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders page title', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText('Privacy Policy')).toBeInTheDocument();
  });

  it('displays version information', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText(/Version:/)).toBeInTheDocument();
    expect(screen.getByText(/1.0/)).toBeInTheDocument();
  });

  it('displays last updated date', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText(/Last Updated:/)).toBeInTheDocument();
    expect(screen.getByText(/January 1, 2025/)).toBeInTheDocument();
  });

  it('displays effective date', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText(/Effective Date:/)).toBeInTheDocument();
  });

  it('renders table of contents', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText('Table of Contents')).toBeInTheDocument();
  });

  it('renders all main sections in table of contents', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText('1. Introduction')).toBeInTheDocument();
    expect(screen.getByText('2. Information We Collect')).toBeInTheDocument();
    expect(screen.getByText('3. How We Use Your Information')).toBeInTheDocument();
    expect(screen.getByText('4. Data Storage and Security')).toBeInTheDocument();
    expect(screen.getByText('5. Third-Party Services')).toBeInTheDocument();
    expect(screen.getByText('6. Data Retention')).toBeInTheDocument();
    expect(screen.getByText('7. Your Rights and Choices')).toBeInTheDocument();
    expect(screen.getByText('8. Cookies and Tracking Technologies')).toBeInTheDocument();
    expect(screen.getByText(/9. Children/)).toBeInTheDocument();
    expect(screen.getByText('10. International Data Transfers')).toBeInTheDocument();
    expect(screen.getByText('11. Changes to This Privacy Policy')).toBeInTheDocument();
    expect(screen.getByText('12. Contact Information')).toBeInTheDocument();
  });

  it('renders Introduction section', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText(/Welcome to the Worldwide Martial Arts Association/)).toBeInTheDocument();
    expect(screen.getByText(/protecting your privacy/i)).toBeInTheDocument();
  });

  it('renders Information We Collect section', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText(/Account Information:/)).toBeInTheDocument();
    expect(screen.getByText(/Payment Information:/)).toBeInTheDocument();
    expect(screen.getByText(/Usage Data:/)).toBeInTheDocument();
  });

  it('mentions ZeroDB in Data Storage section', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText(/ZeroDB/)).toBeInTheDocument();
    expect(screen.getByText(/AES-256/)).toBeInTheDocument();
    expect(screen.getByText(/TLS 1.3/)).toBeInTheDocument();
  });

  it('lists third-party services', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText(/Stripe/i)).toBeInTheDocument();
    expect(screen.getByText(/Cloudflare/i)).toBeInTheDocument();
    expect(screen.getByText(/AINative/i)).toBeInTheDocument();
    expect(screen.getByText(/BeeHiiv/i)).toBeInTheDocument();
    expect(screen.getByText(/Postmark/i)).toBeInTheDocument();
  });

  it('includes links to third-party privacy policies', () => {
    render(<PrivacyPolicyPage />);

    const stripeLink = screen.getByRole('link', { name: /Stripe Privacy Policy/i });
    expect(stripeLink).toHaveAttribute('href', 'https://stripe.com/privacy');
    expect(stripeLink).toHaveAttribute('target', '_blank');
    expect(stripeLink).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('describes GDPR rights', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText(/Right to Access:/)).toBeInTheDocument();
    expect(screen.getByText(/Right to Erasure/)).toBeInTheDocument();
    expect(screen.getByText(/Right to Data Portability:/)).toBeInTheDocument();
  });

  it('describes CCPA rights', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText(/Right to Know:/)).toBeInTheDocument();
    expect(screen.getByText(/Right to Delete:/)).toBeInTheDocument();
    expect(screen.getByText(/Right to Opt-Out:/)).toBeInTheDocument();
  });

  it('provides contact information', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText(/privacy@wwmaa.org/)).toBeInTheDocument();
  });

  it('renders Print button', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByRole('button', { name: /Print/i })).toBeInTheDocument();
  });

  it('renders Download button', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByRole('button', { name: /Download/i })).toBeInTheDocument();
  });

  it('triggers print when Print button is clicked', async () => {
    const user = userEvent.setup();
    render(<PrivacyPolicyPage />);

    const printButton = screen.getByRole('button', { name: /Print/i });
    await user.click(printButton);

    expect(window.print).toHaveBeenCalled();
  });

  it('triggers download when Download button is clicked', async () => {
    const user = userEvent.setup();
    const mockClick = jest.fn();
    const mockAppendChild = jest.spyOn(document.body, 'appendChild').mockImplementation(() => null as any);
    const mockRemoveChild = jest.spyOn(document.body, 'removeChild').mockImplementation(() => null as any);

    // Mock createElement to return element with click method
    const originalCreateElement = document.createElement.bind(document);
    jest.spyOn(document, 'createElement').mockImplementation((tagName) => {
      const element = originalCreateElement(tagName);
      if (tagName === 'a') {
        element.click = mockClick;
      }
      return element;
    });

    render(<PrivacyPolicyPage />);

    const downloadButton = screen.getByRole('button', { name: /Download/i });
    await user.click(downloadButton);

    await waitFor(() => {
      expect(mockClick).toHaveBeenCalled();
    });

    expect(global.URL.createObjectURL).toHaveBeenCalled();
    expect(global.URL.revokeObjectURL).toHaveBeenCalled();

    mockAppendChild.mockRestore();
    mockRemoveChild.mockRestore();
  });

  it('has proper semantic HTML structure', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByRole('article')).toBeInTheDocument();
  });

  it('includes schema.org markup', () => {
    const { container } = render(<PrivacyPolicyPage />);

    const article = container.querySelector('article[itemScope][itemType]');
    expect(article).toHaveAttribute('itemType', 'https://schema.org/Article');
  });

  it('includes data retention information', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText(/Account Data/)).toBeInTheDocument();
    expect(screen.getByText(/Payment Records/)).toBeInTheDocument();
    expect(screen.getByText(/7 years/i)).toBeInTheDocument();
  });

  it('includes COPPA compliance information', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText(/users aged 13 and older/i)).toBeInTheDocument();
  });

  it('includes breach response information', () => {
    render(<PrivacyPolicyPage />);

    expect(screen.getByText(/within 72 hours/i)).toBeInTheDocument();
  });

  it('renders all section IDs for anchor navigation', () => {
    const { container } = render(<PrivacyPolicyPage />);

    expect(container.querySelector('#introduction')).toBeInTheDocument();
    expect(container.querySelector('#data-collected')).toBeInTheDocument();
    expect(container.querySelector('#how-we-use')).toBeInTheDocument();
    expect(container.querySelector('#data-storage')).toBeInTheDocument();
    expect(container.querySelector('#third-party')).toBeInTheDocument();
    expect(container.querySelector('#data-retention')).toBeInTheDocument();
    expect(container.querySelector('#your-rights')).toBeInTheDocument();
    expect(container.querySelector('#cookies')).toBeInTheDocument();
    expect(container.querySelector('#children')).toBeInTheDocument();
    expect(container.querySelector('#international')).toBeInTheDocument();
    expect(container.querySelector('#policy-updates')).toBeInTheDocument();
    expect(container.querySelector('#contact')).toBeInTheDocument();
  });

  it('includes cookie policy link', () => {
    render(<PrivacyPolicyPage />);

    const cookiePolicyLink = screen.getByRole('link', { name: /Cookie Policy/i });
    expect(cookiePolicyLink).toHaveAttribute('href', '/cookie-policy');
  });
});
