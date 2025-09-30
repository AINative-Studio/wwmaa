"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";

interface MembershipTier {
  id: string;
  name: string;
  price: number;
  benefits: string[];
}

const tiers: Record<string, MembershipTier> = {
  basic: {
    id: "t_basic",
    name: "Basic",
    price: 29,
    benefits: ["News & blog", "Public events"]
  },
  premium: {
    id: "t_premium",
    name: "Premium",
    price: 79,
    benefits: ["Belt recognition", "Member training", "Event discounts"]
  },
  instructor: {
    id: "t_instr",
    name: "Instructor",
    price: 149,
    benefits: ["Instructor pathway", "Advanced seminars", "Directory listing"]
  }
};

const cardBrands = {
  visa: /^4/,
  mastercard: /^5[1-5]/,
  amex: /^3[47]/,
  discover: /^6(?:011|5)/
};

export default function CheckoutPage() {
  const searchParams = useSearchParams();
  const tierParam = searchParams.get("tier") || "premium";
  const selectedTier = tiers[tierParam as keyof typeof tiers] || tiers.premium;

  const [cardNumber, setCardNumber] = useState("");
  const [cardBrand, setCardBrand] = useState<string | null>(null);
  const [expiry, setExpiry] = useState("");
  const [cvv, setCvv] = useState("");
  const [cardholderName, setCardholderName] = useState("");
  const [billingAddress, setBillingAddress] = useState("");
  const [city, setCity] = useState("");
  const [zipCode, setZipCode] = useState("");
  const [country, setCountry] = useState("US");
  const [isProcessing, setIsProcessing] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const subtotal = selectedTier.price;
  const tax = subtotal * 0.08; // 8% tax
  const total = subtotal + tax;

  useEffect(() => {
    const cleanNumber = cardNumber.replace(/\s/g, "");
    let brand: string | null = null;

    for (const [key, pattern] of Object.entries(cardBrands)) {
      if (pattern.test(cleanNumber)) {
        brand = key;
        break;
      }
    }
    setCardBrand(brand);
  }, [cardNumber]);

  const formatCardNumber = (value: string) => {
    const cleaned = value.replace(/\s/g, "");
    const chunks = cleaned.match(/.{1,4}/g) || [];
    return chunks.join(" ");
  };

  const formatExpiry = (value: string) => {
    const cleaned = value.replace(/\D/g, "");
    if (cleaned.length >= 2) {
      return cleaned.slice(0, 2) + "/" + cleaned.slice(2, 4);
    }
    return cleaned;
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!cardholderName.trim()) {
      newErrors.cardholderName = "Cardholder name is required";
    }

    const cleanNumber = cardNumber.replace(/\s/g, "");
    if (cleanNumber.length < 13 || cleanNumber.length > 19) {
      newErrors.cardNumber = "Invalid card number";
    }

    const expiryParts = expiry.split("/");
    if (expiryParts.length !== 2) {
      newErrors.expiry = "Invalid expiry date";
    } else {
      const month = parseInt(expiryParts[0]);
      const year = parseInt("20" + expiryParts[1]);
      const now = new Date();
      const currentYear = now.getFullYear();
      const currentMonth = now.getMonth() + 1;

      if (month < 1 || month > 12) {
        newErrors.expiry = "Invalid month";
      } else if (year < currentYear || (year === currentYear && month < currentMonth)) {
        newErrors.expiry = "Card has expired";
      }
    }

    if (cvv.length < 3 || cvv.length > 4) {
      newErrors.cvv = "Invalid CVV";
    }

    if (!zipCode.trim()) {
      newErrors.zipCode = "ZIP code is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsProcessing(true);

    // Simulate payment processing
    await new Promise(resolve => setTimeout(resolve, 2000));

    setIsProcessing(false);
    setShowSuccess(true);
  };

  if (showSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-bg to-white flex items-center justify-center px-6 py-12">
        <div className="max-w-md w-full text-center">
          <div className="bg-white rounded-2xl shadow-glow p-12">
            <div className="w-20 h-20 bg-success/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="font-display text-3xl font-bold text-dojo-navy mb-4">
              Payment Successful!
            </h1>
            <p className="text-lg text-gray-600 mb-2">
              Welcome to WWMAA {selectedTier.name} Membership
            </p>
            <p className="text-sm text-gray-500 mb-8">
              A confirmation email has been sent to your inbox.
            </p>
            <div className="bg-muted rounded-xl p-6 mb-8">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">Order Number:</span>
                <span className="font-semibold text-dojo-navy">ORD-{Date.now().toString().slice(-8)}</span>
              </div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">Membership:</span>
                <span className="font-semibold text-dojo-navy">{selectedTier.name}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Amount Paid:</span>
                <span className="font-semibold text-dojo-navy">${total.toFixed(2)}</span>
              </div>
            </div>
            <a
              href="/dashboard"
              className="inline-flex w-full justify-center items-center rounded-xl px-6 py-3.5 font-semibold gradient-navy text-white shadow-lg hover:shadow-xl transition-all"
            >
              Go to Dashboard
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-bg to-white py-12 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="font-display text-4xl font-bold text-dojo-navy">
            Complete Your Purchase
          </h1>
          <p className="mt-3 text-lg text-gray-600">
            Secure checkout powered by industry-standard encryption
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Payment Form */}
          <div className="lg:col-span-2">
            <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-card p-8">
              {/* Card Information */}
              <div className="mb-8">
                <h2 className="font-display text-2xl font-bold text-dojo-navy mb-6">
                  Payment Information
                </h2>

                {/* Card Number */}
                <div className="mb-6">
                  <label htmlFor="cardNumber" className="block text-sm font-semibold text-gray-700 mb-2">
                    Card Number
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      id="cardNumber"
                      value={cardNumber}
                      onChange={(e) => {
                        const value = e.target.value.replace(/\s/g, "");
                        if (/^\d*$/.test(value) && value.length <= 19) {
                          setCardNumber(formatCardNumber(value));
                        }
                      }}
                      placeholder="1234 5678 9012 3456"
                      className={`w-full px-4 py-3 border ${errors.cardNumber ? 'border-danger' : 'border-gray-300'} rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all`}
                      maxLength={23}
                    />
                    {cardBrand && (
                      <div className="absolute right-3 top-1/2 -translate-y-1/2">
                        <span className="text-xs font-semibold text-dojo-navy uppercase bg-muted px-2 py-1 rounded">
                          {cardBrand}
                        </span>
                      </div>
                    )}
                  </div>
                  {errors.cardNumber && (
                    <p className="mt-1 text-sm text-danger">{errors.cardNumber}</p>
                  )}
                </div>

                {/* Expiry and CVV */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div>
                    <label htmlFor="expiry" className="block text-sm font-semibold text-gray-700 mb-2">
                      Expiry Date
                    </label>
                    <input
                      type="text"
                      id="expiry"
                      value={expiry}
                      onChange={(e) => {
                        const value = e.target.value.replace(/\D/g, "");
                        if (value.length <= 4) {
                          setExpiry(formatExpiry(value));
                        }
                      }}
                      placeholder="MM/YY"
                      className={`w-full px-4 py-3 border ${errors.expiry ? 'border-danger' : 'border-gray-300'} rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all`}
                      maxLength={5}
                    />
                    {errors.expiry && (
                      <p className="mt-1 text-sm text-danger">{errors.expiry}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="cvv" className="block text-sm font-semibold text-gray-700 mb-2">
                      CVV
                    </label>
                    <input
                      type="text"
                      id="cvv"
                      value={cvv}
                      onChange={(e) => {
                        const value = e.target.value.replace(/\D/g, "");
                        if (value.length <= 4) {
                          setCvv(value);
                        }
                      }}
                      placeholder="123"
                      className={`w-full px-4 py-3 border ${errors.cvv ? 'border-danger' : 'border-gray-300'} rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all`}
                      maxLength={4}
                    />
                    {errors.cvv && (
                      <p className="mt-1 text-sm text-danger">{errors.cvv}</p>
                    )}
                  </div>
                </div>

                {/* Cardholder Name */}
                <div className="mb-6">
                  <label htmlFor="cardholderName" className="block text-sm font-semibold text-gray-700 mb-2">
                    Cardholder Name
                  </label>
                  <input
                    type="text"
                    id="cardholderName"
                    value={cardholderName}
                    onChange={(e) => setCardholderName(e.target.value)}
                    placeholder="John Doe"
                    className={`w-full px-4 py-3 border ${errors.cardholderName ? 'border-danger' : 'border-gray-300'} rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all`}
                  />
                  {errors.cardholderName && (
                    <p className="mt-1 text-sm text-danger">{errors.cardholderName}</p>
                  )}
                </div>
              </div>

              {/* Billing Address */}
              <div className="mb-8 pt-8 border-t border-gray-200">
                <h2 className="font-display text-2xl font-bold text-dojo-navy mb-6">
                  Billing Address
                </h2>

                <div className="mb-4">
                  <label htmlFor="billingAddress" className="block text-sm font-semibold text-gray-700 mb-2">
                    Street Address
                  </label>
                  <input
                    type="text"
                    id="billingAddress"
                    value={billingAddress}
                    onChange={(e) => setBillingAddress(e.target.value)}
                    placeholder="123 Main Street"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label htmlFor="city" className="block text-sm font-semibold text-gray-700 mb-2">
                      City
                    </label>
                    <input
                      type="text"
                      id="city"
                      value={city}
                      onChange={(e) => setCity(e.target.value)}
                      placeholder="New York"
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                    />
                  </div>

                  <div>
                    <label htmlFor="zipCode" className="block text-sm font-semibold text-gray-700 mb-2">
                      ZIP Code
                    </label>
                    <input
                      type="text"
                      id="zipCode"
                      value={zipCode}
                      onChange={(e) => setZipCode(e.target.value)}
                      placeholder="10001"
                      className={`w-full px-4 py-3 border ${errors.zipCode ? 'border-danger' : 'border-gray-300'} rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all`}
                    />
                    {errors.zipCode && (
                      <p className="mt-1 text-sm text-danger">{errors.zipCode}</p>
                    )}
                  </div>
                </div>

                <div className="mb-4">
                  <label htmlFor="country" className="block text-sm font-semibold text-gray-700 mb-2">
                    Country
                  </label>
                  <select
                    id="country"
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                  >
                    <option value="US">United States</option>
                    <option value="CA">Canada</option>
                    <option value="GB">United Kingdom</option>
                    <option value="JP">Japan</option>
                    <option value="AU">Australia</option>
                  </select>
                </div>
              </div>

              {/* Security Badges */}
              <div className="flex flex-wrap items-center justify-center gap-6 mb-6 pb-6 border-b border-gray-200">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <svg className="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <span className="font-semibold">256-bit SSL Encrypted</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <svg className="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span className="font-semibold">PCI Compliant</span>
                </div>
              </div>

              {/* Terms and Submit */}
              <div className="text-center text-sm text-gray-600 mb-6">
                By completing this purchase, you agree to our{" "}
                <a href="/terms" className="text-primary hover:underline font-semibold">
                  Terms of Service
                </a>{" "}
                and{" "}
                <a href="/privacy" className="text-primary hover:underline font-semibold">
                  Privacy Policy
                </a>
              </div>

              <button
                type="submit"
                disabled={isProcessing}
                className="w-full flex items-center justify-center gap-3 gradient-navy text-white px-8 py-4 rounded-xl font-semibold text-lg shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isProcessing ? (
                  <>
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing Payment...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    Pay ${total.toFixed(2)}
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-card p-8 sticky top-6">
              <h2 className="font-display text-2xl font-bold text-dojo-navy mb-6">
                Order Summary
              </h2>

              {/* Membership Tier Card */}
              <div className="mb-6 p-6 bg-gradient-accent rounded-xl border border-primary/20">
                <h3 className="font-display text-xl font-bold text-dojo-navy mb-3">
                  {selectedTier.name} Membership
                </h3>
                <p className="text-3xl font-bold text-dojo-navy mb-4">
                  ${selectedTier.price}
                  <span className="text-sm font-normal text-gray-600">/month</span>
                </p>
                <ul className="space-y-2">
                  {selectedTier.benefits.map((benefit, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                      <svg className="w-4 h-4 text-success flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                      {benefit}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Price Breakdown */}
              <div className="space-y-3 mb-6 pb-6 border-b border-gray-200">
                <div className="flex justify-between text-gray-700">
                  <span>Subtotal</span>
                  <span className="font-semibold">${subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-gray-700">
                  <span>Tax (8%)</span>
                  <span className="font-semibold">${tax.toFixed(2)}</span>
                </div>
              </div>

              <div className="flex justify-between text-lg font-bold text-dojo-navy mb-6">
                <span>Total</span>
                <span>${total.toFixed(2)}</span>
              </div>

              {/* Additional Info */}
              <div className="bg-muted rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-sm text-gray-700">
                    <p className="font-semibold mb-1">Recurring Billing</p>
                    <p className="text-gray-600">
                      You will be charged ${total.toFixed(2)} monthly. Cancel anytime from your dashboard.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
