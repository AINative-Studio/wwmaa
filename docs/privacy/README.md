# Privacy & Legal Documentation

This directory contains documentation for WWMAA's privacy and legal compliance features.

## Documents

### US-075: Privacy Policy & Terms of Service
Complete implementation of legal pages including:
- Privacy Policy page
- Terms of Service page
- Terms acceptance tracking
- Reusable legal components
- Comprehensive test suite

**Status:** Completed
**Date:** 2025-01-10
**File:** [US-075-Privacy-Policy-Terms-of-Service.md](./US-075-Privacy-Policy-Terms-of-Service.md)

## Quick Links

### Legal Pages
- [Privacy Policy](/privacy) - `/app/privacy/page.tsx`
- [Terms of Service](/terms) - `/app/terms/page.tsx`

### Components
- **TermsAcceptanceCheckbox** - `/components/legal/terms-acceptance-checkbox.tsx`
- **TableOfContents** - `/components/legal/table-of-contents.tsx`
- **LegalSection Components** - `/components/legal/legal-section.tsx`

### Backend
- **User Model** - `/backend/models/schemas.py` (terms acceptance fields)
- **Registration Route** - `/backend/routes/auth.py` (terms validation)

### Tests
- Component tests: `__tests__/components/legal/`
- Page tests: `__tests__/app/privacy/`, `__tests__/app/terms/`
- **Total test cases:** 105+
- **Coverage:** 60%+

## Legal Compliance

WWMAA's legal documentation covers:

### GDPR (EU)
- Right to access
- Right to erasure (right to be forgotten)
- Right to data portability
- Right to restrict processing
- Right to object
- Right to withdraw consent

### CCPA (California)
- Right to know
- Right to delete
- Right to opt-out
- Right to non-discrimination

### COPPA (Children)
- Age requirement: 13+
- Parental consent for 13-17
- No data collection from under-13

## Third-Party Services

Privacy Policy documents the following services:

- **Stripe** - Payment processing (PCI-DSS Level 1)
- **Cloudflare** - CDN, Stream, Calls, WAF
- **AINative AI Registry** - AI/ML embeddings
- **BeeHiiv** - Newsletter delivery
- **Postmark** - Transactional emails
- **OpenTelemetry, Sentry, Prometheus** - Monitoring

## Data Storage

### ZeroDB
- Encryption at rest: AES-256
- Encryption in transit: TLS 1.3
- ISO 27001 certified infrastructure
- US-based data centers

### Data Retention Periods
- Account data: Until deletion + 30 days
- Payment records: 7 years (legal requirement)
- Event attendance: 3 years
- Audit logs: 2 years
- Analytics: 1 year
- Cookies: 1 year or until cleared

## Terms Acceptance Tracking

### Database Fields
```typescript
{
  terms_accepted_at: DateTime | null
  terms_version_accepted: string | null
  privacy_accepted_at: DateTime | null
  privacy_version_accepted: string | null
}
```

### Registration Flow
1. User completes registration form
2. Must check terms acceptance box
3. Cannot submit without acceptance
4. Backend validates terms_accepted === true
5. Timestamp and version saved to database

### Version Management
- Current version: 1.0
- Last updated: January 1, 2025
- Version tracking enables re-acceptance for updates

## Updating Legal Documents

When updating Privacy Policy or Terms of Service:

1. **Update the page**
   - Modify content in `/app/privacy/page.tsx` or `/app/terms/page.tsx`
   - Increment version number
   - Update "Last Updated" date

2. **Update version constants**
   - Default version in `TermsAcceptanceCheckbox`
   - Backend validation schema

3. **Notify users**
   - Use `TermsUpdateBanner` component
   - Send email notifications
   - Require re-acceptance for material changes

4. **Document changes**
   - Add changelog entry
   - Update documentation
   - Notify legal team

## Contact Information

### Privacy Inquiries
**Email:** privacy@wwmaa.org
**Response Time:** 30 days

### Legal Questions
**Email:** legal@wwmaa.org
**Response Time:** 30 days

### General Support
**Email:** support@wwmaa.org
**Response Time:** 24-48 hours

## Development

### Running Tests
```bash
# All legal tests
npm test -- __tests__/components/legal/ --coverage

# Specific test files
npm test -- __tests__/components/legal/terms-acceptance-checkbox.test.tsx
npm test -- __tests__/app/privacy/page.test.tsx
npm test -- __tests__/app/terms/page.test.tsx
```

### Component Usage

#### Terms Acceptance Checkbox
```tsx
import { TermsAcceptanceCheckbox } from '@/components/legal/terms-acceptance-checkbox';

<TermsAcceptanceCheckbox
  checked={termsAccepted}
  onCheckedChange={setTermsAccepted}
  showError={showError}
  errorMessage="Custom error message"
/>
```

#### Table of Contents
```tsx
import { TableOfContents } from '@/components/legal/table-of-contents';

const sections = [
  { id: 'intro', title: '1. Introduction' },
  {
    id: 'data',
    title: '2. Data Collection',
    subsections: [
      { id: 'data-personal', title: '2.1 Personal Data' }
    ]
  }
];

<TableOfContents items={sections} />
```

#### Legal Section Components
```tsx
import {
  LegalSection,
  LegalSubsection,
  LegalParagraph,
  LegalList,
  LegalHighlight,
  LegalContactBox
} from '@/components/legal/legal-section';

<LegalSection id="privacy" title="Privacy">
  <LegalParagraph>We take privacy seriously.</LegalParagraph>

  <LegalSubsection title="Data Collection">
    <LegalList items={['Email', 'Name', 'Phone']} />
  </LegalSubsection>

  <LegalHighlight variant="warning">
    Important notice about data usage
  </LegalHighlight>

  <LegalContactBox
    title="Privacy Officer"
    organization="WWMAA"
    email="privacy@wwmaa.org"
  />
</LegalSection>
```

## Accessibility

All legal components meet WCAG 2.1 AA standards:
- Semantic HTML
- Keyboard navigation
- Screen reader support
- Proper ARIA labels
- Focus indicators
- Color contrast compliance

## Security

- Terms acceptance validated on backend
- Cannot bypass client-side validation
- Immutable acceptance records
- Audit trail for compliance
- Version tracking for legal purposes

## Deployment Checklist

Before deploying to production:

- [ ] Have attorney review all legal content
- [ ] Update placeholder addresses
- [ ] Specify state/jurisdiction for legal matters
- [ ] Verify third-party service list is current
- [ ] Confirm data retention periods comply with regulations
- [ ] Review arbitration clauses
- [ ] Test terms acceptance flow end-to-end
- [ ] Verify database fields are created
- [ ] Test error handling
- [ ] Validate accessibility
- [ ] Check mobile responsiveness
- [ ] Test print functionality
- [ ] Verify SEO markup
- [ ] Run all tests
- [ ] Update contact emails to production addresses

## Legal Disclaimer

**IMPORTANT:** The legal documents provided are templates. WWMAA must have qualified legal counsel review and approve all legal content before production deployment. These documents should be customized for your specific business needs and jurisdiction.

## Support

For questions about privacy compliance or legal documentation:
- Technical issues: Open a GitHub issue
- Legal questions: Contact legal@wwmaa.org
- Privacy concerns: Contact privacy@wwmaa.org

## Resources

- [GDPR Compliance Guide](https://gdpr.eu/)
- [CCPA Overview](https://oag.ca.gov/privacy/ccpa)
- [COPPA Rules](https://www.ftc.gov/business-guidance/resources/childrens-online-privacy-protection-rule-six-step-compliance-plan-your-business)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

## License

Legal documentation is proprietary to WWMAA. All rights reserved.
