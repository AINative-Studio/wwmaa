'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { FileText, Download, Printer } from 'lucide-react';

export default function TermsOfServicePage() {
  const handlePrint = () => {
    window.print();
  };

  const handleDownload = () => {
    const element = document.getElementById('terms-content');
    if (element) {
      const content = element.innerText;
      const blob = new Blob([content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'WWMAA-Terms-of-Service-v1.0.txt';
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
              Terms of Service
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
                  1. Acceptance of Terms
                </button>
                <button
                  onClick={() => scrollToSection('accounts')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  2. User Accounts and Responsibilities
                </button>
                <button
                  onClick={() => scrollToSection('membership')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  3. Membership Tiers and Benefits
                </button>
                <button
                  onClick={() => scrollToSection('payments')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  4. Payment Terms and Billing
                </button>
                <button
                  onClick={() => scrollToSection('refunds')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  5. Refund and Cancellation Policy
                </button>
                <button
                  onClick={() => scrollToSection('content')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  6. Content Ownership and License
                </button>
                <button
                  onClick={() => scrollToSection('conduct')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  7. Prohibited Conduct
                </button>
                <button
                  onClick={() => scrollToSection('availability')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  8. Service Availability and Maintenance
                </button>
                <button
                  onClick={() => scrollToSection('liability')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  9. Disclaimers and Limitation of Liability
                </button>
                <button
                  onClick={() => scrollToSection('indemnification')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  10. Indemnification
                </button>
                <button
                  onClick={() => scrollToSection('disputes')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  11. Dispute Resolution and Governing Law
                </button>
                <button
                  onClick={() => scrollToSection('termination')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  12. Account Termination
                </button>
                <button
                  onClick={() => scrollToSection('changes')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  13. Changes to Terms
                </button>
                <button
                  onClick={() => scrollToSection('contact')}
                  className="block text-sm text-primary hover:underline text-left"
                >
                  14. Contact Information
                </button>
              </nav>
            </CardContent>
          </Card>
        </div>

        {/* Content */}
        <div id="terms-content" className="prose prose-gray max-w-none" itemProp="articleBody">
          {/* Acceptance of Terms */}
          <section id="introduction" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">1. Acceptance of Terms</h2>
            <p className="mb-4">
              Welcome to the Worldwide Martial Arts Association (WWMAA). These Terms of Service
              (Terms) govern your access to and use of WWMAA&apos;s website, mobile applications,
              and related services (collectively, the Services).
            </p>
            <p className="mb-4">
              By creating an account, accessing, or using our Services, you agree to be bound by
              these Terms and our Privacy Policy. If you do not agree to these Terms, you may not
              use our Services.
            </p>
            <p className="mb-4">
              These Terms constitute a legally binding agreement between you and WWMAA. Please
              read them carefully before using our Services.
            </p>
          </section>

          {/* User Accounts */}
          <section id="accounts" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">
              2. User Accounts and Responsibilities
            </h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">2.1 Account Creation</h3>
            <p className="mb-4">To access certain features, you must create an account. You agree to:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Provide accurate, current, and complete information during registration</li>
              <li>Maintain and promptly update your account information</li>
              <li>Keep your password secure and confidential</li>
              <li>Notify us immediately of any unauthorized access to your account</li>
              <li>Be responsible for all activities that occur under your account</li>
              <li>Be at least 13 years old (users under 18 require parental consent)</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">2.2 Account Security</h3>
            <p className="mb-4">You are solely responsible for:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Maintaining the confidentiality of your login credentials</li>
              <li>All activities and transactions under your account</li>
              <li>Logging out at the end of each session</li>
              <li>Using strong, unique passwords</li>
            </ul>
            <p className="mb-4">
              WWMAA will never ask for your password via email, phone, or unsolicited
              communication. If you receive such a request, report it to security@wwmaa.org
              immediately.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">2.3 Account Verification</h3>
            <p className="mb-4">
              You must verify your email address to activate your account. Membership applications
              may require additional verification of your martial arts credentials and experience.
            </p>
          </section>

          {/* Membership Tiers */}
          <section id="membership" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">3. Membership Tiers and Benefits</h2>
            <p className="mb-4">WWMAA offers different membership tiers with varying benefits:</p>

            <div className="space-y-4">
              <Card>
                <CardContent className="pt-6">
                  <h3 className="text-lg font-semibold mb-2">Basic Membership (Free)</h3>
                  <ul className="list-disc pl-6 text-sm space-y-1">
                    <li>Browse public content and resources</li>
                    <li>View event listings</li>
                    <li>Access community forums (read-only)</li>
                    <li>Receive newsletter updates</li>
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <h3 className="text-lg font-semibold mb-2">Standard Membership</h3>
                  <p className="text-sm text-muted-foreground mb-2">$29.99/month or $299/year</p>
                  <ul className="list-disc pl-6 text-sm space-y-1">
                    <li>All Basic benefits</li>
                    <li>Access to on-demand training videos</li>
                    <li>Participation in live virtual training sessions</li>
                    <li>Register for in-person events (additional fees may apply)</li>
                    <li>Post in community forums</li>
                    <li>Access to member directory</li>
                    <li>Official WWMAA membership certificate</li>
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <h3 className="text-lg font-semibold mb-2">Premium Membership</h3>
                  <p className="text-sm text-muted-foreground mb-2">$99.99/month or $999/year</p>
                  <ul className="list-disc pl-6 text-sm space-y-1">
                    <li>All Standard benefits</li>
                    <li>Priority access to new courses and content</li>
                    <li>Discounted event registration (up to 20% off)</li>
                    <li>One-on-one instructor consultations (limited hours)</li>
                    <li>Advanced AI-powered training analytics</li>
                    <li>Exclusive Premium member events</li>
                    <li>Early access to certification programs</li>
                    <li>Premium badge and profile features</li>
                  </ul>
                </CardContent>
              </Card>
            </div>

            <p className="mt-4 text-sm text-muted-foreground">
              Membership benefits are subject to change. Members will be notified of material
              changes at least 30 days in advance.
            </p>
          </section>

          {/* Payment Terms */}
          <section id="payments" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">4. Payment Terms and Billing</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">4.1 Subscription Billing</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>
                <strong>Billing Cycles:</strong> Subscriptions are billed monthly or annually based
                on your selected plan
              </li>
              <li>
                <strong>Auto-Renewal:</strong> Subscriptions automatically renew at the end of each
                billing period unless canceled
              </li>
              <li>
                <strong>Payment Methods:</strong> We accept major credit cards, debit cards, and
                other payment methods via Stripe
              </li>
              <li>
                <strong>Billing Date:</strong> You will be charged on the same day each billing
                period (monthly or annually)
              </li>
              <li>
                <strong>Price Changes:</strong> We reserve the right to modify subscription prices
                with 30 days notice
              </li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">4.2 Payment Processing</h3>
            <p className="mb-4">
              All payments are processed securely through Stripe, a PCI-DSS Level 1 certified
              payment processor. We do not store your complete credit card information on our
              servers.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">4.3 Failed Payments</h3>
            <p className="mb-4">If a payment fails:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>We will attempt to process the payment up to 3 times</li>
              <li>You will receive email notifications of failed payment attempts</li>
              <li>Your account may be downgraded or suspended after repeated failures</li>
              <li>You are responsible for any outstanding balances</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">4.4 Taxes</h3>
            <p className="mb-4">
              Prices shown do not include applicable taxes. You are responsible for paying all
              taxes, duties, and government-imposed fees associated with your subscription.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">4.5 Event Fees</h3>
            <p className="mb-4">
              Some events may require separate registration fees. Event fees are non-refundable
              unless the event is canceled by WWMAA (see Section 5.3).
            </p>
          </section>

          {/* Refunds and Cancellations */}
          <section id="refunds" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">5. Refund and Cancellation Policy</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">5.1 Membership Cancellation</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>You may cancel your subscription at any time from your account settings</li>
              <li>Cancellations take effect at the end of the current billing period</li>
              <li>You will retain access to paid features until the end of the billing period</li>
              <li>No partial refunds are provided for unused time in the current billing period</li>
              <li>Annual subscriptions canceled mid-year are not eligible for prorated refunds</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">5.2 30-Day Money-Back Guarantee</h3>
            <p className="mb-4">
              New subscribers (first-time purchasers only) are eligible for a full refund within
              30 days of their initial subscription purchase if:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>This is your first paid subscription with WWMAA</li>
              <li>The request is made within 30 days of your initial payment</li>
              <li>You contact support@wwmaa.org to request the refund</li>
            </ul>
            <p className="mb-4">
              This guarantee does not apply to renewals, upgrades from free to paid tiers, or
              additional purchases.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">5.3 Event Cancellations</h3>
            <p className="mb-4">
              <strong>If you cancel your event registration:</strong>
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>More than 14 days before event: Full refund minus 10% processing fee</li>
              <li>7-14 days before event: 50% refund</li>
              <li>Less than 7 days before event: No refund</li>
            </ul>

            <p className="mb-4">
              <strong>If WWMAA cancels an event:</strong>
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Full refund of event registration fees</li>
              <li>Option to transfer registration to a future event</li>
              <li>WWMAA is not responsible for travel, accommodation, or other related expenses</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">5.4 Refund Processing</h3>
            <p className="mb-4">
              Approved refunds are processed within 5-10 business days and returned to your
              original payment method. Contact support@wwmaa.org with refund inquiries.
            </p>
          </section>

          {/* Content Ownership */}
          <section id="content" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">6. Content Ownership and License</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">6.1 WWMAA Content</h3>
            <p className="mb-4">
              All content provided through our Services, including but not limited to videos,
              articles, images, logos, training materials, and software (WWMAA Content), is owned
              by WWMAA or our licensors and is protected by copyright, trademark, and other
              intellectual property laws.
            </p>
            <p className="mb-4">
              We grant you a limited, non-exclusive, non-transferable, revocable license to access
              and use WWMAA Content for your personal, non-commercial use only. You may not:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Copy, reproduce, distribute, or create derivative works</li>
              <li>Sell, rent, lease, or sublicense the content</li>
              <li>Download videos or training materials (except where explicitly permitted)</li>
              <li>Remove copyright or proprietary notices</li>
              <li>Use content for commercial purposes without written permission</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">6.2 User-Generated Content</h3>
            <p className="mb-4">
              You retain ownership of content you create and post on WWMAA (User Content), such as
              forum posts, comments, and feedback. However, by posting User Content, you grant
              WWMAA a worldwide, non-exclusive, royalty-free, perpetual, irrevocable license to:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Use, reproduce, modify, and display your content</li>
              <li>Distribute your content across our Services</li>
              <li>Create derivative works for promotional purposes</li>
              <li>Sublicense these rights to service providers</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">6.3 Content Representations</h3>
            <p className="mb-4">By posting User Content, you represent and warrant that:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>You own or have the necessary rights to the content</li>
              <li>The content does not violate any third-party rights</li>
              <li>The content complies with these Terms and applicable laws</li>
              <li>WWMAA may use the content as described above</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">6.4 Content Removal</h3>
            <p className="mb-4">
              WWMAA reserves the right to remove any User Content that violates these Terms,
              infringes rights, or is otherwise objectionable, without notice.
            </p>
          </section>

          {/* Prohibited Conduct */}
          <section id="conduct" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">7. Prohibited Conduct</h2>
            <p className="mb-4">When using WWMAA Services, you agree NOT to:</p>

            <h3 className="text-xl font-semibold mb-3 mt-6">7.1 Illegal Activities</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Violate any local, state, national, or international law</li>
              <li>Infringe on intellectual property rights of others</li>
              <li>Engage in fraud, money laundering, or other financial crimes</li>
              <li>Share or promote illegal content</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">7.2 Harmful Behavior</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Harass, bully, threaten, or intimidate other users</li>
              <li>Post hateful, discriminatory, or offensive content</li>
              <li>Share explicit, violent, or disturbing content</li>
              <li>Impersonate others or misrepresent your identity</li>
              <li>Dox or share others private information without consent</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">7.3 Platform Abuse</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Spam, send unsolicited messages, or engage in excessive self-promotion</li>
              <li>Use automated systems (bots, scrapers) without permission</li>
              <li>Attempt to hack, disrupt, or compromise our systems</li>
              <li>Reverse engineer or decompile our software</li>
              <li>Circumvent security measures or access restrictions</li>
              <li>Create multiple accounts to evade restrictions</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">7.4 Commercial Misuse</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Use Services for unauthorized commercial purposes</li>
              <li>Sell or transfer your account to others</li>
              <li>Share login credentials with multiple users</li>
              <li>Redistribute WWMAA content without permission</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">7.5 Consequences</h3>
            <p className="mb-4">
              Violation of these rules may result in:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Warning or content removal</li>
              <li>Temporary or permanent account suspension</li>
              <li>Termination without refund</li>
              <li>Legal action if necessary</li>
            </ul>
          </section>

          {/* Service Availability */}
          <section id="availability" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">8. Service Availability and Maintenance</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">8.1 Uptime Commitment</h3>
            <p className="mb-4">
              We strive to maintain 99.9% uptime for our Services. However, we do not guarantee
              uninterrupted access and are not liable for downtime caused by:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Scheduled maintenance (announced in advance when possible)</li>
              <li>Emergency maintenance or security updates</li>
              <li>Third-party service failures (hosting, CDN, payment processors)</li>
              <li>Internet connectivity issues beyond our control</li>
              <li>Force majeure events (natural disasters, government actions, etc.)</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">8.2 Service Modifications</h3>
            <p className="mb-4">
              WWMAA reserves the right to:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Modify, suspend, or discontinue any feature or service</li>
              <li>Change system requirements or supported platforms</li>
              <li>Update software and APIs</li>
              <li>Remove or limit access to content</li>
            </ul>
            <p className="mb-4">
              We will provide reasonable notice of material changes, but are not required to
              maintain any particular feature indefinitely.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">8.3 Beta Features</h3>
            <p className="mb-4">
              We may offer beta or experimental features. These are provided as-is without
              warranties and may be changed or discontinued at any time.
            </p>
          </section>

          {/* Liability Limitations */}
          <section id="liability" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">
              9. Disclaimers and Limitation of Liability
            </h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">9.1 No Warranty</h3>
            <p className="mb-4 uppercase font-semibold">
              WWMAA SERVICES ARE PROVIDED AS IS AND AS AVAILABLE WITHOUT WARRANTIES OF ANY KIND,
              EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Warranties of merchantability or fitness for a particular purpose</li>
              <li>Warranties of accuracy, reliability, or completeness</li>
              <li>Warranties that services will be uninterrupted or error-free</li>
              <li>Warranties regarding security or freedom from viruses</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">9.2 Training and Safety Disclaimer</h3>
            <p className="mb-4 font-semibold">
              MARTIAL ARTS TRAINING INVOLVES PHYSICAL ACTIVITY AND CARRIES INHERENT RISKS:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Consult a physician before beginning any training program</li>
              <li>WWMAA is not responsible for injuries during training</li>
              <li>Follow all safety guidelines and use appropriate protective equipment</li>
              <li>Training content is for educational purposes only</li>
              <li>Always train under qualified supervision when learning new techniques</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">9.3 Limitation of Liability</h3>
            <p className="mb-4 uppercase font-semibold">
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, WWMAA SHALL NOT BE LIABLE FOR:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Indirect, incidental, special, consequential, or punitive damages</li>
              <li>Loss of profits, revenue, data, or goodwill</li>
              <li>Service interruptions or data loss</li>
              <li>Actions of other users or third parties</li>
              <li>Unauthorized access to your account or data</li>
            </ul>
            <p className="mb-4">
              IN NO EVENT SHALL WWMAA&apos;S TOTAL LIABILITY EXCEED THE AMOUNT YOU PAID TO WWMAA IN
              THE 12 MONTHS PRECEDING THE CLAIM, OR $100, WHICHEVER IS GREATER.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">9.4 Basis of the Bargain</h3>
            <p className="mb-4">
              These limitations reflect the allocation of risk between you and WWMAA. Our pricing
              reflects these limitations, and we would not provide Services without them.
            </p>
          </section>

          {/* Indemnification */}
          <section id="indemnification" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">10. Indemnification</h2>
            <p className="mb-4">
              You agree to indemnify, defend, and hold harmless WWMAA, its officers, directors,
              employees, agents, and affiliates from any claims, damages, losses, liabilities, and
              expenses (including reasonable attorneys fees) arising from:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Your use or misuse of the Services</li>
              <li>Your violation of these Terms</li>
              <li>Your violation of any rights of third parties</li>
              <li>Your User Content</li>
              <li>Any negligent or wrongful conduct</li>
            </ul>
            <p className="mb-4">
              This indemnification obligation survives termination of your account and these Terms.
            </p>
          </section>

          {/* Dispute Resolution */}
          <section id="disputes" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">
              11. Dispute Resolution and Governing Law
            </h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">11.1 Informal Resolution</h3>
            <p className="mb-4">
              Before filing a claim, you agree to contact us at legal@wwmaa.org to seek an
              informal resolution. We will attempt to resolve disputes amicably within 60 days.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">11.2 Binding Arbitration</h3>
            <p className="mb-4">
              If informal resolution fails, disputes will be resolved through binding arbitration
              rather than in court, except where prohibited by law. Arbitration will be conducted
              by the American Arbitration Association (AAA) under its Commercial Arbitration Rules.
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Arbitration will be held in [State], United States</li>
              <li>The arbitrator&apos;s decision is final and binding</li>
              <li>Each party pays its own costs and attorneys fees unless the arbitrator decides
                otherwise</li>
              <li>Class actions and jury trials are waived</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">11.3 Exceptions to Arbitration</h3>
            <p className="mb-4">Either party may seek relief in small claims court for disputes
              within that court&apos;s jurisdiction. WWMAA may also seek injunctive relief in court
              to protect intellectual property rights.</p>

            <h3 className="text-xl font-semibold mb-3 mt-6">11.4 Governing Law</h3>
            <p className="mb-4">
              These Terms are governed by the laws of the State of [State], United States, without
              regard to conflict of law principles. Federal law governs intellectual property and
              arbitration matters.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">11.5 Venue</h3>
            <p className="mb-4">
              For any disputes not subject to arbitration, you consent to the exclusive
              jurisdiction of state and federal courts located in [County], [State], United States.
            </p>
          </section>

          {/* Termination */}
          <section id="termination" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">12. Account Termination</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">12.1 Termination by You</h3>
            <p className="mb-4">
              You may terminate your account at any time by:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Canceling your subscription from account settings</li>
              <li>Contacting support@wwmaa.org to request account deletion</li>
            </ul>
            <p className="mb-4">
              Upon account deletion, you will lose access to all content, data, and membership
              benefits. Some information may be retained as described in our Privacy Policy.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">12.2 Termination by WWMAA</h3>
            <p className="mb-4">
              WWMAA may suspend or terminate your account immediately, without notice or refund, if:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>You violate these Terms or our policies</li>
              <li>You engage in fraudulent or illegal activities</li>
              <li>You abuse or harm other users</li>
              <li>Your account has been inactive for over 2 years</li>
              <li>Required by law or legal process</li>
              <li>We decide to discontinue Services (with reasonable notice)</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">12.3 Effect of Termination</h3>
            <p className="mb-4">Upon termination:</p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Your right to access Services immediately ceases</li>
              <li>Sections 6-11 of these Terms survive termination</li>
              <li>Outstanding payment obligations remain due</li>
              <li>WWMAA may delete your data (backup copies may persist)</li>
            </ul>
          </section>

          {/* Changes to Terms */}
          <section id="changes" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">13. Changes to These Terms</h2>
            <p className="mb-4">
              WWMAA may modify these Terms at any time. When we make changes, we will:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2">
              <li>Update the Last Updated date at the top</li>
              <li>Increment the version number</li>
              <li>Notify you via email for material changes</li>
              <li>Display a prominent notice on our website</li>
              <li>Require acceptance on your next login (for material changes)</li>
            </ul>
            <p className="mb-4">
              Your continued use of Services after changes are posted constitutes acceptance of the
              modified Terms. If you do not agree to the changes, you must stop using our Services
              and cancel your account.
            </p>
            <p className="mb-4">
              Material changes take effect 30 days after notice (or immediately for legal/security
              reasons). Non-material changes take effect immediately upon posting.
            </p>
          </section>

          {/* Contact Information */}
          <section id="contact" className="mb-8 scroll-mt-4">
            <h2 className="text-2xl font-semibold mb-4">14. Contact Information</h2>
            <p className="mb-4">
              If you have questions about these Terms of Service, please contact us:
            </p>

            <Card>
              <CardContent className="pt-6">
                <div className="space-y-3">
                  <div>
                    <strong>Legal Department</strong>
                    <p className="text-sm text-muted-foreground">
                      Worldwide Martial Arts Association
                    </p>
                  </div>

                  <div>
                    <strong>Email:</strong>
                    <p>
                      <a
                        href="mailto:legal@wwmaa.org"
                        className="text-primary hover:underline"
                      >
                        legal@wwmaa.org
                      </a>
                    </p>
                  </div>

                  <div>
                    <strong>Support Email:</strong>
                    <p>
                      <a
                        href="mailto:support@wwmaa.org"
                        className="text-primary hover:underline"
                      >
                        support@wwmaa.org
                      </a>
                    </p>
                  </div>

                  <div>
                    <strong>Mailing Address:</strong>
                    <p className="text-sm">
                      WWMAA Legal Department
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
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Footer Notice */}
          <div className="mt-12 p-6 bg-muted rounded-lg">
            <p className="text-sm text-center text-muted-foreground">
              These Terms of Service were last updated on January 1, 2025 (Version 1.0).
              <br />
              <strong>
                By using WWMAA Services, you acknowledge that you have read, understood, and agree
                to be bound by these Terms and our Privacy Policy.
              </strong>
            </p>
          </div>
        </div>
      </div>
    </article>
  );
}
