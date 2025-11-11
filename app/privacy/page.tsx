'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { FileText, Download, Printer } from 'lucide-react';

export default function PrivacyPolicyPage() {
  const handlePrint = () => {
    window.print();
  };

  const handleDownload = () => {
    // Create a downloadable version
    const element = document.getElementById('privacy-content');
    if (element) {
      const content = element.innerText;
      const blob = new Blob([content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'WWMAA-Privacy-Policy-v1.0.txt';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <article itemScope itemType="https://schema.org/Article">
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <FileText className="h-8 w-8 text-primary" />
            <h1 className="text-4xl font-bold" itemProp="headline">
              Privacy Policy
            </h1>
          </div>

          <div className="flex items-center justify-between flex-wrap gap-4 mb-6">
            <div className="text-sm text-muted-foreground">
              <p>
                <strong>Version:</strong> 1.0
              </p>
              <p>
                <strong>Last Updated:</strong>{' '}
                <time itemProp="dateModified" dateTime="2025-01-01">
                  January 1, 2025
                </time>
              </p>
              <p>
                <strong>Effective Date:</strong>{' '}
                <time itemProp="datePublished" dateTime="2025-01-01">
                  January 1, 2025
                </time>
              </p>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handlePrint}
                className="print:hidden"
              >
                <Printer className="h-4 w-4 mr-2" />
                Print
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownload}
                className="print:hidden"
              >
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
            </div>
          </div>

          {/* Table of Contents */}
          <Card className="print:hidden">
            <CardContent className="pt-6">
              <h2 className="text-lg font-semibold mb-3">Table of Contents</h2>
              <nav className="space-y-2">
                <button
                  onClick={() => scrollToSection('introduction')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  1. Introduction
                </button>
                <button
                  onClick={() => scrollToSection('data-collected')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  2. Information We Collect
                </button>
                <button
                  onClick={() => scrollToSection('how-we-use')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  3. How We Use Your Information
                </button>
                <button
                  onClick={() => scrollToSection('data-storage')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  4. Data Storage and Security
                </button>
                <button
                  onClick={() => scrollToSection('third-party')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  5. Third-Party Services
                </button>
                <button
                  onClick={() => scrollToSection('data-retention')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  6. Data Retention
                </button>
                <button
                  onClick={() => scrollToSection('your-rights')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  7. Your Rights and Choices
                </button>
                <button
                  onClick={() => scrollToSection('cookies')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  8. Cookies and Tracking
                </button>
                <button
                  onClick={() => scrollToSection('children')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  9. Children&apos;s Privacy
                </button>
                <button
                  onClick={() => scrollToSection('international')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  10. International Data Transfers
                </button>
                <button
                  onClick={() => scrollToSection('policy-updates')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  11. Policy Updates
                </button>
                <button
                  onClick={() => scrollToSection('contact')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  12. Contact Information
                </button>
              </nav>
            </CardContent>
          </Card>
        </div>

        {/* Content */}
        <div id="privacy-content" className="prose prose-gray max-w-none" itemProp="articleBody">
          {/* Introduction */}
          <section id="introduction" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">1. Introduction</h2>
            <p className="mb-4">
              Welcome to the Worldwide Martial Arts Association (WWMAA). We are committed to
              protecting your privacy and handling your personal information with care and respect.
              This Privacy Policy explains how we collect, use, store, and protect your information
              when you use our website and services.
            </p>
            <p className="mb-4">
              By using WWMAA services, you agree to the collection and use of information in
              accordance with this policy. If you do not agree with our policies and practices,
              please do not use our services.
            </p>
          </section>

          {/* Information We Collect */}
          <section id="data-collected" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">2. Information We Collect</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">2.1 Information You Provide</h3>
            <p className="mb-4">We collect information that you voluntarily provide to us:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>
                <strong>Account Information:</strong> Name, email address, phone number, password
                (encrypted), and profile photo
              </li>
              <li>
                <strong>Membership Applications:</strong> Martial arts experience, training history,
                instructor information, certifications, and references
              </li>
              <li>
                <strong>Payment Information:</strong> Billing address and payment method details
                (processed securely through Stripe - we do not store complete credit card numbers)
              </li>
              <li>
                <strong>Event Registration:</strong> RSVP information, dietary restrictions, and
                emergency contact details
              </li>
              <li>
                <strong>Communications:</strong> Messages, feedback, and support inquiries you send
                to us
              </li>
              <li>
                <strong>User-Generated Content:</strong> Comments, forum posts, and training session
                feedback
              </li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">2.2 Information Collected Automatically</h3>
            <p className="mb-4">When you use our services, we automatically collect:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>
                <strong>Usage Data:</strong> Pages visited, features used, time spent on site, and
                interaction patterns
              </li>
              <li>
                <strong>Device Information:</strong> Browser type, operating system, device type,
                and screen resolution
              </li>
              <li>
                <strong>Log Data:</strong> IP address, access times, referring URLs, and error logs
              </li>
              <li>
                <strong>Cookies and Tracking:</strong> Session cookies, preference cookies, and
                analytics cookies (see Section 8)
              </li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">2.3 Information from Third Parties</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>
                <strong>Payment Processors:</strong> Transaction confirmations and payment status
                from Stripe
              </li>
              <li>
                <strong>Email Service:</strong> Email delivery status and engagement metrics from
                Postmark and BeeHiiv
              </li>
              <li>
                <strong>Analytics Providers:</strong> Aggregated usage statistics from monitoring
                tools
              </li>
            </ul>
          </section>

          {/* How We Use Your Information */}
          <section id="how-we-use" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">3. How We Use Your Information</h2>
            <p className="mb-4">We use your information for the following purposes:</p>

            <h3 className="text-xl font-semibold mb-3 mt-6">3.1 Service Delivery</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Create and manage your user account</li>
              <li>Process membership applications and approvals</li>
              <li>Facilitate event registration and attendance tracking</li>
              <li>Provide access to training sessions and educational content</li>
              <li>Process payments and manage subscriptions</li>
              <li>Deliver customer support and respond to inquiries</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">3.2 Communications</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Send transactional emails (account verification, password resets, receipts)</li>
              <li>Notify you about upcoming events, training sessions, and important updates</li>
              <li>Send newsletters and promotional content (with your consent - you can opt out)</li>
              <li>Respond to your comments, questions, and support requests</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">3.3 Platform Improvement</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Analyze usage patterns to improve our services</li>
              <li>Conduct AI-powered semantic search to enhance content discovery</li>
              <li>Monitor system performance and troubleshoot technical issues</li>
              <li>Develop new features and enhance existing functionality</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">3.4 Legal and Security</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Comply with legal obligations and enforce our Terms of Service</li>
              <li>Detect, prevent, and address fraud, security risks, and technical issues</li>
              <li>Protect the rights, property, and safety of WWMAA, our users, and the public</li>
              <li>Maintain audit logs for security and compliance purposes</li>
            </ul>
          </section>

          {/* Data Storage and Security */}
          <section id="data-storage" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">4. Data Storage and Security</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">4.1 Storage Infrastructure</h3>
            <p className="mb-4">
              Your data is stored using <strong>ZeroDB</strong>, a secure cloud database service
              hosted in United States data centers. ZeroDB provides:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Encryption at rest using AES-256</li>
              <li>Encrypted data transmission using TLS 1.3</li>
              <li>Regular automated backups</li>
              <li>ISO 27001 certified infrastructure</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">4.2 Security Measures</h3>
            <p className="mb-4">We implement multiple layers of security:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>
                <strong>Password Security:</strong> Passwords are hashed using bcrypt with salt
              </li>
              <li>
                <strong>Authentication:</strong> JWT token-based authentication with automatic
                refresh and blacklisting
              </li>
              <li>
                <strong>Network Security:</strong> Cloudflare WAF (Web Application Firewall) for
                DDoS protection and threat mitigation
              </li>
              <li>
                <strong>Access Control:</strong> Role-based access control (RBAC) limiting data
                access to authorized personnel
              </li>
              <li>
                <strong>Monitoring:</strong> Real-time security monitoring using
                OpenTelemetry, Sentry, and Prometheus
              </li>
              <li>
                <strong>Audit Logging:</strong> Comprehensive audit trails for all sensitive operations
              </li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">4.3 Data Breach Response</h3>
            <p className="mb-4">
              In the event of a data breach, we will:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Notify affected users within 72 hours</li>
              <li>Report to relevant authorities as required by law</li>
              <li>Take immediate steps to contain and remediate the breach</li>
              <li>Provide guidance on protective measures you can take</li>
            </ul>
          </section>

          {/* Third-Party Services */}
          <section id="third-party" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">5. Third-Party Services</h2>
            <p className="mb-4">
              We use trusted third-party services to provide and enhance our platform. These
              services have their own privacy policies and data handling practices:
            </p>

            <div className="space-y-4">
              <div className="border-l-4 border-primary pl-4">
                <h4 className="font-semibold">Stripe (Payment Processing)</h4>
                <p className="text-sm text-muted-foreground mb-2">
                  Purpose: Process subscription payments and event fees
                </p>
                <p className="text-sm">
                  Stripe handles all payment processing. We do not store complete credit card
                  numbers. Stripe is PCI-DSS Level 1 certified.
                </p>
                <a
                  href="https://stripe.com/privacy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline"
                >
                  Stripe Privacy Policy
                </a>
              </div>

              <div className="border-l-4 border-primary pl-4">
                <h4 className="font-semibold">Cloudflare (CDN, Stream, Calls, WAF)</h4>
                <p className="text-sm text-muted-foreground mb-2">
                  Purpose: Content delivery, video streaming, video calls, and security
                </p>
                <p className="text-sm">
                  Cloudflare provides CDN services, hosts training videos (Cloudflare Stream),
                  powers video calls (Cloudflare Calls), and protects against attacks (WAF).
                </p>
                <a
                  href="https://www.cloudflare.com/privacypolicy/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline"
                >
                  Cloudflare Privacy Policy
                </a>
              </div>

              <div className="border-l-4 border-primary pl-4">
                <h4 className="font-semibold">AINative AI Registry (AI/ML Services)</h4>
                <p className="text-sm text-muted-foreground mb-2">
                  Purpose: Generate embeddings for semantic search functionality
                </p>
                <p className="text-sm">
                  We use AINative to process content and generate embeddings for our AI-powered
                  search feature. Content is sent to their API for processing.
                </p>
              </div>

              <div className="border-l-4 border-primary pl-4">
                <h4 className="font-semibold">BeeHiiv (Newsletter)</h4>
                <p className="text-sm text-muted-foreground mb-2">
                  Purpose: Deliver marketing newsletters and announcements
                </p>
                <p className="text-sm">
                  If you subscribe to our newsletter, your email is shared with BeeHiiv for
                  delivery. You can unsubscribe at any time.
                </p>
                <a
                  href="https://www.beehiiv.com/privacy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline"
                >
                  BeeHiiv Privacy Policy
                </a>
              </div>

              <div className="border-l-4 border-primary pl-4">
                <h4 className="font-semibold">Postmark (Transactional Email)</h4>
                <p className="text-sm text-muted-foreground mb-2">
                  Purpose: Send account emails (verification, password resets, receipts)
                </p>
                <p className="text-sm">
                  Postmark delivers all transactional emails. We share your email address and
                  name for delivery purposes only.
                </p>
                <a
                  href="https://postmarkapp.com/eu-privacy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline"
                >
                  Postmark Privacy Policy
                </a>
              </div>

              <div className="border-l-4 border-primary pl-4">
                <h4 className="font-semibold">
                  OpenTelemetry, Sentry, Prometheus (Monitoring)
                </h4>
                <p className="text-sm text-muted-foreground mb-2">
                  Purpose: Application monitoring, error tracking, and performance metrics
                </p>
                <p className="text-sm">
                  These services help us monitor application health and fix issues. They may
                  receive technical logs and error reports.
                </p>
              </div>
            </div>
          </section>

          {/* Data Retention */}
          <section id="data-retention" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">6. Data Retention</h2>
            <p className="mb-4">We retain your information for different periods based on data type:</p>

            <div className="space-y-3">
              <div className="flex justify-between items-start border-b pb-2">
                <div>
                  <strong>Account Data</strong>
                  <p className="text-sm text-muted-foreground">Profile, credentials, preferences</p>
                </div>
                <span className="text-sm font-medium">Until account deletion + 30 days</span>
              </div>

              <div className="flex justify-between items-start border-b pb-2">
                <div>
                  <strong>Application Records</strong>
                  <p className="text-sm text-muted-foreground">Membership applications, approvals</p>
                </div>
                <span className="text-sm font-medium">7 years (compliance requirement)</span>
              </div>

              <div className="flex justify-between items-start border-b pb-2">
                <div>
                  <strong>Payment Records</strong>
                  <p className="text-sm text-muted-foreground">Transaction history, invoices</p>
                </div>
                <span className="text-sm font-medium">7 years (tax/legal requirement)</span>
              </div>

              <div className="flex justify-between items-start border-b pb-2">
                <div>
                  <strong>Event Attendance</strong>
                  <p className="text-sm text-muted-foreground">RSVP records, check-ins</p>
                </div>
                <span className="text-sm font-medium">3 years</span>
              </div>

              <div className="flex justify-between items-start border-b pb-2">
                <div>
                  <strong>Communications</strong>
                  <p className="text-sm text-muted-foreground">Emails, support tickets</p>
                </div>
                <span className="text-sm font-medium">3 years</span>
              </div>

              <div className="flex justify-between items-start border-b pb-2">
                <div>
                  <strong>Audit Logs</strong>
                  <p className="text-sm text-muted-foreground">Security events, access logs</p>
                </div>
                <span className="text-sm font-medium">2 years</span>
              </div>

              <div className="flex justify-between items-start border-b pb-2">
                <div>
                  <strong>Analytics Data</strong>
                  <p className="text-sm text-muted-foreground">Usage statistics, anonymous metrics</p>
                </div>
                <span className="text-sm font-medium">1 year</span>
              </div>

              <div className="flex justify-between items-start">
                <div>
                  <strong>Cookie Data</strong>
                  <p className="text-sm text-muted-foreground">Session cookies, preferences</p>
                </div>
                <span className="text-sm font-medium">1 year or until cleared</span>
              </div>
            </div>

            <p className="mt-4 text-sm text-muted-foreground">
              After retention periods expire, data is permanently deleted or anonymized. Some
              data may be retained longer if required by law or for legitimate business purposes
              (e.g., dispute resolution).
            </p>
          </section>

          {/* Your Rights and Choices */}
          <section id="your-rights" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">7. Your Rights and Choices</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">7.1 GDPR Rights (EU/UK Residents)</h3>
            <p className="mb-4">
              If you are in the European Union or United Kingdom, you have the following rights:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>
                <strong>Right to Access:</strong> Request a copy of all personal data we hold
                about you
              </li>
              <li>
                <strong>Right to Rectification:</strong> Request correction of inaccurate or
                incomplete data
              </li>
              <li>
                <strong>Right to Erasure (Right to be Forgotten):</strong> Request deletion of
                your personal data
              </li>
              <li>
                <strong>Right to Data Portability:</strong> Receive your data in a
                machine-readable format
              </li>
              <li>
                <strong>Right to Restrict Processing:</strong> Limit how we use your data
              </li>
              <li>
                <strong>Right to Object:</strong> Object to processing based on legitimate
                interests
              </li>
              <li>
                <strong>Right to Withdraw Consent:</strong> Withdraw consent for marketing
                communications
              </li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">7.2 CCPA Rights (California Residents)</h3>
            <p className="mb-4">
              If you are a California resident, you have the following rights:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>
                <strong>Right to Know:</strong> Request disclosure of personal information
                collected, used, and shared
              </li>
              <li>
                <strong>Right to Delete:</strong> Request deletion of personal information
              </li>
              <li>
                <strong>Right to Opt-Out:</strong> Opt out of the sale of personal information
                (Note: We do not sell your personal information)
              </li>
              <li>
                <strong>Right to Non-Discrimination:</strong> You will not receive discriminatory
                treatment for exercising your rights
              </li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">7.3 How to Exercise Your Rights</h3>
            <p className="mb-4">To exercise any of these rights:</p>
            <ol className="list-decimal pl-6 mb-4 space-y-2">
              <li>
                Email us at <strong>privacy@wwmaa.org</strong> with your request
              </li>
              <li>Include your full name, email address, and specific request</li>
              <li>We will verify your identity before processing your request</li>
              <li>We will respond within 30 days (45 days for complex requests)</li>
            </ol>

            <h3 className="text-xl font-semibold mb-3 mt-6">7.4 Marketing Communications</h3>
            <p className="mb-4">You can opt out of marketing communications:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Click the unsubscribe link in any marketing email</li>
              <li>Update your email preferences in your account settings</li>
              <li>Contact us at privacy@wwmaa.org</li>
            </ul>
            <p className="text-sm text-muted-foreground">
              Note: You cannot opt out of transactional emails (account verification, receipts, etc.)
              as these are required for service delivery.
            </p>
          </section>

          {/* Cookies and Tracking */}
          <section id="cookies" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">8. Cookies and Tracking Technologies</h2>
            <p className="mb-4">
              We use cookies and similar technologies to improve your experience. For detailed
              information, please see our separate{' '}
              <a href="/cookie-policy" className="text-primary hover:underline">
                Cookie Policy
              </a>
              .
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">8.1 Types of Cookies We Use</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>
                <strong>Essential Cookies:</strong> Required for login, session management, and
                core functionality
              </li>
              <li>
                <strong>Functional Cookies:</strong> Remember your preferences and settings
              </li>
              <li>
                <strong>Analytics Cookies:</strong> Help us understand how you use our site
              </li>
              <li>
                <strong>Marketing Cookies:</strong> Used for targeted communications (with your
                consent)
              </li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">8.2 Cookie Management</h3>
            <p className="mb-4">You can control cookies through:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Our cookie consent banner (shown on first visit)</li>
              <li>Your browser settings (most browsers allow you to block or delete cookies)</li>
              <li>Your account preferences page</li>
            </ul>
          </section>

          {/* Children's Privacy */}
          <section id="children" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">9. Children&apos;s Privacy (COPPA Compliance)</h2>
            <p className="mb-4">
              WWMAA services are intended for users aged 13 and older. We do not knowingly
              collect personal information from children under 13 without verifiable parental
              consent.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">9.1 Parental Consent</h3>
            <p className="mb-4">
              For users aged 13-17, we require parental or guardian consent for membership
              applications. Parents/guardians can:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Review their child&apos;s information</li>
              <li>Request deletion of their child&apos;s data</li>
              <li>Refuse further collection or use of their child&apos;s information</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">9.2 If You Believe We Have Data from a Child Under 13</h3>
            <p className="mb-4">
              If you believe we have collected information from a child under 13 without proper
              consent, please contact us immediately at <strong>privacy@wwmaa.org</strong>. We
              will investigate and delete the information promptly.
            </p>
          </section>

          {/* International Data Transfers */}
          <section id="international" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">10. International Data Transfers</h2>
            <p className="mb-4">
              WWMAA is based in the United States. Your information is stored on servers located
              in the United States. If you access our services from outside the United States,
              your information will be transferred to, stored in, and processed in the United
              States.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">10.1 Data Protection Standards</h3>
            <p className="mb-4">
              The United States may not have the same data protection laws as your country. We
              take measures to ensure your data receives adequate protection:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>We comply with applicable data protection regulations (GDPR, CCPA)</li>
              <li>We use Standard Contractual Clauses for EU data transfers</li>
              <li>We implement technical and organizational security measures</li>
              <li>Third-party services we use are vetted for data protection compliance</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">10.2 EU-U.S. Data Privacy Framework</h3>
            <p className="mb-4">
              We comply with applicable data transfer frameworks and mechanisms approved by
              regulatory authorities.
            </p>
          </section>

          {/* Policy Updates */}
          <section id="policy-updates" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">11. Changes to This Privacy Policy</h2>
            <p className="mb-4">
              We may update this Privacy Policy from time to time to reflect changes in our
              practices, technology, legal requirements, or for other reasons.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">11.1 Notification of Changes</h3>
            <p className="mb-4">When we make changes, we will:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Update the Last Updated date at the top of this policy</li>
              <li>Increment the version number</li>
              <li>
                Notify you via email if changes are material (affect how we use your personal
                information)
              </li>
              <li>Display a prominent notice on our website</li>
              <li>
                Require you to accept updated terms on your next login (for material changes)
              </li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">11.2 Your Responsibility</h3>
            <p className="mb-4">
              Please review this Privacy Policy periodically. Your continued use of WWMAA services
              after changes are posted constitutes your acceptance of the updated policy.
            </p>
          </section>

          {/* Contact Information */}
          <section id="contact" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">12. Contact Information</h2>
            <p className="mb-4">
              If you have questions, concerns, or requests regarding this Privacy Policy or our
              data practices, please contact us:
            </p>

            <Card>
              <CardContent className="pt-6">
                <div className="space-y-3">
                  <div>
                    <strong>Privacy Officer</strong>
                    <p className="text-sm text-muted-foreground">
                      Worldwide Martial Arts Association
                    </p>
                  </div>

                  <div>
                    <strong>Email:</strong>
                    <p>
                      <a
                        href="mailto:privacy@wwmaa.org"
                        className="text-primary hover:underline"
                      >
                        privacy@wwmaa.org
                      </a>
                    </p>
                  </div>

                  <div>
                    <strong>Mailing Address:</strong>
                    <p className="text-sm">
                      WWMAA Privacy Team
                      <br />
                      [Address Line 1]
                      <br />
                      [Address Line 2]
                      <br />
                      [City, State ZIP]
                      <br />
                      United States
                    </p>
                  </div>

                  <div>
                    <strong>Response Time:</strong>
                    <p className="text-sm text-muted-foreground">
                      We will respond to privacy inquiries within 30 days
                    </p>
                  </div>

                  <div className="pt-3 border-t">
                    <p className="text-sm text-muted-foreground">
                      For general support inquiries, please contact{' '}
                      <a
                        href="mailto:support@wwmaa.org"
                        className="text-primary hover:underline"
                      >
                        support@wwmaa.org
                      </a>
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Footer Notice */}
          <div className="mt-12 p-6 bg-muted rounded-lg">
            <p className="text-sm text-center text-muted-foreground">
              This Privacy Policy was last updated on January 1, 2025 (Version 1.0).
              <br />
              <strong>Please review our Terms of Service for additional information about using
              WWMAA services.</strong>
            </p>
          </div>
        </div>
      </div>
    </article>
  );
}
