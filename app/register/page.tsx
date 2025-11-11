'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { TermsAcceptanceCheckbox } from '@/components/legal/terms-acceptance-checkbox';

type Step = 1 | 2 | 3;

interface FormData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
  tier: string;
  cardNumber: string;
  cardExpiry: string;
  cardCvc: string;
  cardName: string;
  termsAccepted: boolean;
}

const membershipTiers = [
  {
    id: 't_basic',
    name: 'Basic',
    price: 29,
    benefits: ['News & blog', 'Public events'],
  },
  {
    id: 't_premium',
    name: 'Premium',
    price: 79,
    benefits: ['Belt recognition', 'Member training', 'Event discounts'],
    featured: true,
  },
  {
    id: 't_instr',
    name: 'Instructor',
    price: 149,
    benefits: ['Instructor pathway', 'Advanced seminars', 'Directory listing'],
  },
];

export default function RegisterPage() {
  const [currentStep, setCurrentStep] = useState<Step>(1);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    tier: 't_premium',
    cardNumber: '',
    cardExpiry: '',
    cardCvc: '',
    cardName: '',
    termsAccepted: false,
  });
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});

  const updateField = (field: keyof FormData, value: string | boolean) => {
    setFormData({ ...formData, [field]: value });
    if (errors[field]) {
      setErrors({ ...errors, [field]: undefined });
    }
  };

  const validateStep1 = () => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};

    if (!formData.name) {
      newErrors.name = 'Name is required';
    }

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = () => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};

    if (!formData.tier) {
      newErrors.tier = 'Please select a membership tier';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep3 = () => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};

    if (!formData.cardNumber) {
      newErrors.cardNumber = 'Card number is required';
    } else if (!/^\d{16}$/.test(formData.cardNumber.replace(/\s/g, ''))) {
      newErrors.cardNumber = 'Please enter a valid 16-digit card number';
    }

    if (!formData.cardExpiry) {
      newErrors.cardExpiry = 'Expiry date is required';
    } else if (!/^(0[1-9]|1[0-2])\/\d{2}$/.test(formData.cardExpiry)) {
      newErrors.cardExpiry = 'Format: MM/YY';
    }

    if (!formData.cardCvc) {
      newErrors.cardCvc = 'CVC is required';
    } else if (!/^\d{3,4}$/.test(formData.cardCvc)) {
      newErrors.cardCvc = 'Please enter a valid 3 or 4-digit CVC';
    }

    if (!formData.cardName) {
      newErrors.cardName = 'Cardholder name is required';
    }

    if (!formData.termsAccepted) {
      newErrors.termsAccepted = 'You must accept the terms and conditions';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    let isValid = false;

    if (currentStep === 1) {
      isValid = validateStep1();
    } else if (currentStep === 2) {
      isValid = validateStep2();
    }

    if (isValid && currentStep < 3) {
      setCurrentStep((currentStep + 1) as Step);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep((currentStep - 1) as Step);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateStep3()) {
      return;
    }

    setIsLoading(true);

    // Simulate API call
    setTimeout(() => {
      console.log('Registration data:', formData);
      setIsLoading(false);
    }, 2000);
  };

  const formatCardNumber = (value: string) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    const matches = v.match(/\d{4,16}/g);
    const match = (matches && matches[0]) || '';
    const parts = [];

    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }

    if (parts.length) {
      return parts.join(' ');
    } else {
      return value;
    }
  };

  const formatExpiry = (value: string) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    if (v.length >= 2) {
      return v.slice(0, 2) + '/' + v.slice(2, 4);
    }
    return v;
  };

  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-dojo-navy/5 via-bg to-dojo-green/5">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="font-display text-4xl font-bold text-dojo-navy mb-2">Join WWMAA</h1>
          <p className="text-gray-600">Create your account and start your martial arts journey</p>
        </div>

        {/* Progress Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-center">
            {[1, 2, 3].map((step, idx) => (
              <div key={step} className="flex items-center">
                <div className="flex flex-col items-center">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all ${
                      currentStep === step
                        ? 'gradient-navy text-white shadow-lg scale-110'
                        : currentStep > step
                        ? 'bg-success text-white'
                        : 'bg-gray-200 text-gray-500'
                    }`}
                  >
                    {currentStep > step ? (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      step
                    )}
                  </div>
                  <span className="mt-2 text-xs font-medium text-gray-600">
                    {step === 1 ? 'Personal Info' : step === 2 ? 'Membership' : 'Payment'}
                  </span>
                </div>
                {idx < 2 && (
                  <div
                    className={`w-16 h-1 mx-2 mb-6 transition-all ${
                      currentStep > step ? 'bg-success' : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-card p-8">
          <form onSubmit={handleSubmit}>
            {/* Step 1: Personal Information */}
            {currentStep === 1 && (
              <div className="space-y-6">
                <div>
                  <Label htmlFor="name" className="text-dojo-navy">Full Name</Label>
                  <Input
                    id="name"
                    type="text"
                    value={formData.name}
                    onChange={(e) => updateField('name', e.target.value)}
                    className={`mt-1.5 ${errors.name ? 'border-danger focus-visible:ring-danger' : ''}`}
                    placeholder="John Doe"
                  />
                  {errors.name && <p className="mt-1.5 text-sm text-danger">{errors.name}</p>}
                </div>

                <div>
                  <Label htmlFor="email" className="text-dojo-navy">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => updateField('email', e.target.value)}
                    className={`mt-1.5 ${errors.email ? 'border-danger focus-visible:ring-danger' : ''}`}
                    placeholder="you@example.com"
                  />
                  {errors.email && <p className="mt-1.5 text-sm text-danger">{errors.email}</p>}
                </div>

                <div>
                  <Label htmlFor="password" className="text-dojo-navy">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={formData.password}
                    onChange={(e) => updateField('password', e.target.value)}
                    className={`mt-1.5 ${errors.password ? 'border-danger focus-visible:ring-danger' : ''}`}
                    placeholder="Create a strong password"
                  />
                  {errors.password && <p className="mt-1.5 text-sm text-danger">{errors.password}</p>}
                </div>

                <div>
                  <Label htmlFor="confirmPassword" className="text-dojo-navy">Confirm Password</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    value={formData.confirmPassword}
                    onChange={(e) => updateField('confirmPassword', e.target.value)}
                    className={`mt-1.5 ${errors.confirmPassword ? 'border-danger focus-visible:ring-danger' : ''}`}
                    placeholder="Re-enter your password"
                  />
                  {errors.confirmPassword && (
                    <p className="mt-1.5 text-sm text-danger">{errors.confirmPassword}</p>
                  )}
                </div>
              </div>
            )}

            {/* Step 2: Membership Tier Selection */}
            {currentStep === 2 && (
              <div className="space-y-6">
                <div>
                  <h2 className="font-display text-2xl font-bold text-dojo-navy mb-4">Choose Your Membership</h2>
                  <p className="text-gray-600 mb-6">Select the tier that best fits your martial arts journey</p>

                  <RadioGroup value={formData.tier} onValueChange={(value) => updateField('tier', value)}>
                    <div className="grid gap-4 md:grid-cols-3">
                      {membershipTiers.map((tier) => (
                        <div key={tier.id} className="relative">
                          <label
                            htmlFor={tier.id}
                            className={`block cursor-pointer rounded-xl border-2 p-6 transition-all ${
                              formData.tier === tier.id
                                ? 'border-dojo-orange bg-dojo-orange/5 shadow-lg'
                                : 'border-gray-200 hover:border-dojo-navy/30 hover:shadow-md'
                            } ${tier.featured ? 'ring-2 ring-dojo-orange' : ''}`}
                          >
                            {tier.featured && (
                              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                                <span className="inline-flex rounded-full gradient-orange px-3 py-1 text-xs font-semibold text-white shadow-lg">
                                  Most Popular
                                </span>
                              </div>
                            )}
                            <div className="flex items-start gap-3">
                              <RadioGroupItem value={tier.id} id={tier.id} className="mt-1" />
                              <div className="flex-1">
                                <h3 className="font-display text-xl font-bold text-dojo-navy mb-2">{tier.name}</h3>
                                <div className="flex items-baseline gap-1 mb-3">
                                  <span className="text-3xl font-bold text-dojo-navy">${tier.price}</span>
                                  <span className="text-sm text-gray-600">/month</span>
                                </div>
                                <ul className="space-y-2">
                                  {tier.benefits.map((benefit, idx) => (
                                    <li key={idx} className="flex items-start gap-2 text-sm">
                                      <svg
                                        className="w-4 h-4 text-dojo-green flex-shrink-0 mt-0.5"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                      >
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                                      </svg>
                                      <span className="text-gray-700">{benefit}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                          </label>
                        </div>
                      ))}
                    </div>
                  </RadioGroup>
                  {errors.tier && <p className="mt-3 text-sm text-danger">{errors.tier}</p>}
                </div>
              </div>
            )}

            {/* Step 3: Payment Information */}
            {currentStep === 3 && (
              <div className="space-y-6">
                <div>
                  <h2 className="font-display text-2xl font-bold text-dojo-navy mb-2">Payment Information</h2>
                  <p className="text-gray-600 mb-6">Enter your payment details to complete registration</p>
                </div>

                <div className="bg-dojo-navy/5 rounded-xl p-4 mb-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Selected Plan</p>
                      <p className="font-display text-xl font-bold text-dojo-navy">
                        {membershipTiers.find((t) => t.id === formData.tier)?.name}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-3xl font-bold text-dojo-navy">
                        ${membershipTiers.find((t) => t.id === formData.tier)?.price}
                      </p>
                      <p className="text-sm text-gray-600">per month</p>
                    </div>
                  </div>
                </div>

                <div>
                  <Label htmlFor="cardNumber" className="text-dojo-navy">Card Number</Label>
                  <Input
                    id="cardNumber"
                    type="text"
                    value={formData.cardNumber}
                    onChange={(e) => updateField('cardNumber', formatCardNumber(e.target.value))}
                    className={`mt-1.5 ${errors.cardNumber ? 'border-danger focus-visible:ring-danger' : ''}`}
                    placeholder="1234 5678 9012 3456"
                    maxLength={19}
                  />
                  {errors.cardNumber && <p className="mt-1.5 text-sm text-danger">{errors.cardNumber}</p>}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="cardExpiry" className="text-dojo-navy">Expiry Date</Label>
                    <Input
                      id="cardExpiry"
                      type="text"
                      value={formData.cardExpiry}
                      onChange={(e) => updateField('cardExpiry', formatExpiry(e.target.value))}
                      className={`mt-1.5 ${errors.cardExpiry ? 'border-danger focus-visible:ring-danger' : ''}`}
                      placeholder="MM/YY"
                      maxLength={5}
                    />
                    {errors.cardExpiry && <p className="mt-1.5 text-sm text-danger">{errors.cardExpiry}</p>}
                  </div>

                  <div>
                    <Label htmlFor="cardCvc" className="text-dojo-navy">CVC</Label>
                    <Input
                      id="cardCvc"
                      type="text"
                      value={formData.cardCvc}
                      onChange={(e) => updateField('cardCvc', e.target.value.replace(/\D/g, ''))}
                      className={`mt-1.5 ${errors.cardCvc ? 'border-danger focus-visible:ring-danger' : ''}`}
                      placeholder="123"
                      maxLength={4}
                    />
                    {errors.cardCvc && <p className="mt-1.5 text-sm text-danger">{errors.cardCvc}</p>}
                  </div>
                </div>

                <div>
                  <Label htmlFor="cardName" className="text-dojo-navy">Cardholder Name</Label>
                  <Input
                    id="cardName"
                    type="text"
                    value={formData.cardName}
                    onChange={(e) => updateField('cardName', e.target.value)}
                    className={`mt-1.5 ${errors.cardName ? 'border-danger focus-visible:ring-danger' : ''}`}
                    placeholder="John Doe"
                  />
                  {errors.cardName && <p className="mt-1.5 text-sm text-danger">{errors.cardName}</p>}
                </div>

                <div className="pt-4 border-t">
                  <TermsAcceptanceCheckbox
                    checked={formData.termsAccepted}
                    onCheckedChange={(checked) => updateField('termsAccepted', checked)}
                    showError={!!errors.termsAccepted}
                    errorMessage={errors.termsAccepted}
                    id="terms"
                  />
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="mt-8 flex items-center justify-between gap-4">
              {currentStep > 1 ? (
                <button
                  type="button"
                  onClick={handleBack}
                  className="px-6 py-3 rounded-xl border-2 border-dojo-navy text-dojo-navy font-semibold hover:bg-dojo-navy hover:text-white transition-all"
                >
                  Back
                </button>
              ) : (
                <div />
              )}

              {currentStep < 3 ? (
                <button
                  type="button"
                  onClick={handleNext}
                  className="ml-auto px-8 py-3 rounded-xl gradient-navy text-white font-semibold shadow-lg hover:shadow-xl transition-all"
                >
                  Next
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={isLoading}
                  className="ml-auto px-8 py-3 rounded-xl gradient-orange text-white font-semibold shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {isLoading ? (
                    <>
                      <svg
                        className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        ></path>
                      </svg>
                      Processing...
                    </>
                  ) : (
                    'Complete Registration'
                  )}
                </button>
              )}
            </div>
          </form>

          <div className="mt-6 pt-6 border-t text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <Link href="/login" className="font-semibold text-dojo-navy hover:text-dojo-orange transition-colors">
                Sign in
              </Link>
            </p>
          </div>
        </div>

        <div className="mt-6 text-center">
          <Link href="/" className="text-sm text-gray-600 hover:text-dojo-navy transition-colors">
            Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}
