import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TermsAcceptanceCheckbox, useTermsAcceptance, TermsUpdateBanner } from '@/components/legal/terms-acceptance-checkbox';
import { renderHook, act } from '@testing-library/react';

describe('TermsAcceptanceCheckbox', () => {
  const mockOnCheckedChange = jest.fn();

  beforeEach(() => {
    mockOnCheckedChange.mockClear();
  });

  it('renders with default props', () => {
    render(
      <TermsAcceptanceCheckbox
        checked={false}
        onCheckedChange={mockOnCheckedChange}
      />
    );

    expect(screen.getByLabelText(/I accept the/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Terms of Service/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Privacy Policy/i })).toBeInTheDocument();
  });

  it('displays checked state correctly', () => {
    render(
      <TermsAcceptanceCheckbox
        checked={true}
        onCheckedChange={mockOnCheckedChange}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeChecked();
  });

  it('calls onCheckedChange when clicked', async () => {
    const user = userEvent.setup();
    render(
      <TermsAcceptanceCheckbox
        checked={false}
        onCheckedChange={mockOnCheckedChange}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    await user.click(checkbox);

    expect(mockOnCheckedChange).toHaveBeenCalledWith(true);
  });

  it('shows error message when showError is true and unchecked', () => {
    render(
      <TermsAcceptanceCheckbox
        checked={false}
        onCheckedChange={mockOnCheckedChange}
        showError={true}
      />
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText(/You must accept the Terms of Service/i)).toBeInTheDocument();
  });

  it('does not show error when showError is true but checked', () => {
    render(
      <TermsAcceptanceCheckbox
        checked={true}
        onCheckedChange={mockOnCheckedChange}
        showError={true}
      />
    );

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('displays custom error message', () => {
    const customError = 'Custom error message';
    render(
      <TermsAcceptanceCheckbox
        checked={false}
        onCheckedChange={mockOnCheckedChange}
        showError={true}
        errorMessage={customError}
      />
    );

    expect(screen.getByText(customError)).toBeInTheDocument();
  });

  it('shows version numbers when showVersions is true', () => {
    render(
      <TermsAcceptanceCheckbox
        checked={false}
        onCheckedChange={mockOnCheckedChange}
        showVersions={true}
        termsVersion="2.0"
        privacyVersion="2.1"
      />
    );

    expect(screen.getByText(/Terms of Service/i).textContent).toContain('(v2.0)');
    expect(screen.getByText(/Privacy Policy/i).textContent).toContain('(v2.1)');
  });

  it('opens links in new tab', () => {
    render(
      <TermsAcceptanceCheckbox
        checked={false}
        onCheckedChange={mockOnCheckedChange}
      />
    );

    const termsLink = screen.getByRole('link', { name: /Terms of Service/i });
    const privacyLink = screen.getByRole('link', { name: /Privacy Policy/i });

    expect(termsLink).toHaveAttribute('target', '_blank');
    expect(termsLink).toHaveAttribute('rel', 'noopener noreferrer');
    expect(privacyLink).toHaveAttribute('target', '_blank');
    expect(privacyLink).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('is disabled when disabled prop is true', () => {
    render(
      <TermsAcceptanceCheckbox
        checked={false}
        onCheckedChange={mockOnCheckedChange}
        disabled={true}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeDisabled();
  });

  it('has proper ARIA attributes', () => {
    render(
      <TermsAcceptanceCheckbox
        checked={false}
        onCheckedChange={mockOnCheckedChange}
        showError={true}
        id="custom-id"
      />
    );

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toHaveAttribute('aria-invalid', 'true');
    expect(checkbox).toHaveAttribute('aria-describedby', 'custom-id-error');
  });

  it('uses custom id when provided', () => {
    render(
      <TermsAcceptanceCheckbox
        checked={false}
        onCheckedChange={mockOnCheckedChange}
        id="custom-checkbox-id"
      />
    );

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toHaveAttribute('id', 'custom-checkbox-id');
  });

  it('displays helper text', () => {
    render(
      <TermsAcceptanceCheckbox
        checked={false}
        onCheckedChange={mockOnCheckedChange}
      />
    );

    expect(screen.getByText(/By checking this box, you acknowledge/i)).toBeInTheDocument();
  });
});

describe('useTermsAcceptance hook', () => {
  it('initializes with default values', () => {
    const { result } = renderHook(() => useTermsAcceptance());

    expect(result.current.termsAccepted).toBe(false);
    expect(result.current.showError).toBe(false);
  });

  it('updates termsAccepted when setTermsAccepted is called', () => {
    const { result } = renderHook(() => useTermsAcceptance());

    act(() => {
      result.current.setTermsAccepted(true);
    });

    expect(result.current.termsAccepted).toBe(true);
  });

  it('clears error when terms are accepted', () => {
    const { result } = renderHook(() => useTermsAcceptance());

    // First, trigger error
    act(() => {
      result.current.validate();
    });

    expect(result.current.showError).toBe(true);

    // Then accept terms
    act(() => {
      result.current.setTermsAccepted(true);
    });

    expect(result.current.showError).toBe(false);
  });

  it('validate returns false and shows error when not accepted', () => {
    const { result } = renderHook(() => useTermsAcceptance());

    let isValid: boolean = true;
    act(() => {
      isValid = result.current.validate();
    });

    expect(isValid).toBe(false);
    expect(result.current.showError).toBe(true);
  });

  it('validate returns true when accepted', () => {
    const { result } = renderHook(() => useTermsAcceptance());

    act(() => {
      result.current.setTermsAccepted(true);
    });

    let isValid: boolean = false;
    act(() => {
      isValid = result.current.validate();
    });

    expect(isValid).toBe(true);
    expect(result.current.showError).toBe(false);
  });

  it('reset clears acceptance and errors', () => {
    const { result } = renderHook(() => useTermsAcceptance());

    act(() => {
      result.current.setTermsAccepted(true);
      result.current.validate();
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.termsAccepted).toBe(false);
    expect(result.current.showError).toBe(false);
  });
});

describe('TermsUpdateBanner', () => {
  const mockOnAccept = jest.fn();
  const mockOnDismiss = jest.fn();

  beforeEach(() => {
    mockOnAccept.mockClear().mockResolvedValue(undefined);
    mockOnDismiss.mockClear();
  });

  it('renders with updated terms message', () => {
    render(
      <TermsUpdateBanner
        onAccept={mockOnAccept}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByText(/Updated Terms of Service and Privacy Policy/i)).toBeInTheDocument();
    expect(screen.getByText(/Please review and accept the changes/i)).toBeInTheDocument();
  });

  it('displays version numbers', () => {
    render(
      <TermsUpdateBanner
        onAccept={mockOnAccept}
        newTermsVersion="2.0"
        newPrivacyVersion="2.1"
      />
    );

    expect(screen.getByText(/\(v2\.0\)/)).toBeInTheDocument();
    expect(screen.getByText(/\(v2\.1\)/)).toBeInTheDocument();
  });

  it('shows Accept & Continue button', () => {
    render(
      <TermsUpdateBanner
        onAccept={mockOnAccept}
      />
    );

    expect(screen.getByRole('button', { name: /Accept & Continue/i })).toBeInTheDocument();
  });

  it('shows Remind Me Later button when onDismiss is provided', () => {
    render(
      <TermsUpdateBanner
        onAccept={mockOnAccept}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByRole('button', { name: /Remind Me Later/i })).toBeInTheDocument();
  });

  it('does not show Remind Me Later when onDismiss is not provided', () => {
    render(
      <TermsUpdateBanner
        onAccept={mockOnAccept}
      />
    );

    expect(screen.queryByRole('button', { name: /Remind Me Later/i })).not.toBeInTheDocument();
  });

  it('requires checkbox to be checked before accepting', async () => {
    const user = userEvent.setup();
    render(
      <TermsUpdateBanner
        onAccept={mockOnAccept}
      />
    );

    const acceptButton = screen.getByRole('button', { name: /Accept & Continue/i });
    await user.click(acceptButton);

    expect(mockOnAccept).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('calls onAccept when checkbox is checked and button clicked', async () => {
    const user = userEvent.setup();
    render(
      <TermsUpdateBanner
        onAccept={mockOnAccept}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    await user.click(checkbox);

    const acceptButton = screen.getByRole('button', { name: /Accept & Continue/i });
    await user.click(acceptButton);

    await waitFor(() => {
      expect(mockOnAccept).toHaveBeenCalledTimes(1);
    });
  });

  it('calls onDismiss when Remind Me Later is clicked', async () => {
    const user = userEvent.setup();
    render(
      <TermsUpdateBanner
        onAccept={mockOnAccept}
        onDismiss={mockOnDismiss}
      />
    );

    const dismissButton = screen.getByRole('button', { name: /Remind Me Later/i });
    await user.click(dismissButton);

    expect(mockOnDismiss).toHaveBeenCalledTimes(1);
  });

  it('shows loading state while accepting', async () => {
    const user = userEvent.setup();
    const slowOnAccept = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(
      <TermsUpdateBanner
        onAccept={slowOnAccept}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    await user.click(checkbox);

    const acceptButton = screen.getByRole('button', { name: /Accept & Continue/i });
    await user.click(acceptButton);

    expect(screen.getByRole('button', { name: /Accepting.../i })).toBeInTheDocument();

    await waitFor(() => {
      expect(slowOnAccept).toHaveBeenCalled();
    });
  });

  it('disables buttons while accepting', async () => {
    const user = userEvent.setup();
    const slowOnAccept = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(
      <TermsUpdateBanner
        onAccept={slowOnAccept}
        onDismiss={mockOnDismiss}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    await user.click(checkbox);

    const acceptButton = screen.getByRole('button', { name: /Accept & Continue/i });
    await user.click(acceptButton);

    expect(acceptButton).toBeDisabled();
    expect(screen.getByRole('button', { name: /Remind Me Later/i })).toBeDisabled();

    await waitFor(() => {
      expect(slowOnAccept).toHaveBeenCalled();
    });
  });
});
