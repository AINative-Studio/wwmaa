'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { applicationApi } from '@/lib/application-api';
import { Search, Loader2, AlertCircle } from 'lucide-react';

export default function ApplicationStatusLookupPage() {
  const router = useRouter();
  const [searchType, setSearchType] = useState<'id' | 'email'>('id');
  const [searchValue, setSearchValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!searchValue.trim()) {
      setError('Please enter an application ID or email address');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let application = null;

      if (searchType === 'id') {
        application = await applicationApi.getApplicationById(searchValue.trim());
      } else {
        application = await applicationApi.getApplicationByEmail(searchValue.trim());
      }

      if (!application) {
        setError(
          searchType === 'id'
            ? 'No application found with this ID'
            : 'No application found with this email address'
        );
        return;
      }

      // Redirect to the application detail page
      router.push(`/application-status/${application.id}`);
    } catch (err) {
      setError('An error occurred while searching. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchTypeChange = (type: 'id' | 'email') => {
    setSearchType(type);
    setSearchValue('');
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Check Application Status
          </h1>
          <p className="text-gray-600">
            Enter your application ID or email address to view your application status
          </p>
        </div>

        {/* Search Card */}
        <Card>
          <CardHeader>
            <CardTitle>Find Your Application</CardTitle>
            <CardDescription>
              Search by application ID or the email address you used when applying
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSearch} className="space-y-6">
              {/* Search Type Toggle */}
              <div className="flex gap-4 p-1 bg-gray-100 rounded-lg">
                <button
                  type="button"
                  onClick={() => handleSearchTypeChange('id')}
                  className={`flex-1 py-2 px-4 rounded-md font-medium transition-colors ${
                    searchType === 'id'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Application ID
                </button>
                <button
                  type="button"
                  onClick={() => handleSearchTypeChange('email')}
                  className={`flex-1 py-2 px-4 rounded-md font-medium transition-colors ${
                    searchType === 'email'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Email Address
                </button>
              </div>

              {/* Search Input */}
              <div className="space-y-2">
                <Label htmlFor="search">
                  {searchType === 'id' ? 'Application ID' : 'Email Address'}
                </Label>
                <Input
                  id="search"
                  type={searchType === 'email' ? 'email' : 'text'}
                  placeholder={
                    searchType === 'id'
                      ? 'e.g., app_123456'
                      : 'e.g., your.email@example.com'
                  }
                  value={searchValue}
                  onChange={(e) => {
                    setSearchValue(e.target.value);
                    setError(null);
                  }}
                  disabled={loading}
                  className="text-base"
                />
                {searchType === 'id' && (
                  <p className="text-xs text-gray-500">
                    Your application ID was sent to you via email when you submitted your application
                  </p>
                )}
              </div>

              {/* Error Alert */}
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {/* Submit Button */}
              <Button
                type="submit"
                className="w-full"
                disabled={loading || !searchValue.trim()}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="mr-2 h-4 w-4" />
                    Check Status
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Help Text */}
        <div className="mt-8 text-center space-y-4">
          <div className="bg-white rounded-lg border p-6">
            <h3 className="font-semibold text-gray-900 mb-2">Need Help?</h3>
            <p className="text-sm text-gray-600 mb-4">
              If you cannot find your application or have questions about the process,
              please contact our membership team.
            </p>
            <div className="space-y-2 text-sm">
              <p className="text-gray-600">
                Email:{' '}
                <a
                  href="mailto:membership@wwmaa.org"
                  className="text-blue-600 hover:text-blue-800 font-medium"
                >
                  membership@wwmaa.org
                </a>
              </p>
              <p className="text-gray-600">
                Phone:{' '}
                <a
                  href="tel:+1-555-0199"
                  className="text-blue-600 hover:text-blue-800 font-medium"
                >
                  +1-555-0199
                </a>
              </p>
            </div>
          </div>

          {/* Additional Information */}
          <div className="bg-blue-50 rounded-lg border border-blue-200 p-6 text-left">
            <h3 className="font-semibold text-blue-900 mb-3">Application Review Process</h3>
            <ul className="space-y-2 text-sm text-blue-800">
              <li className="flex gap-2">
                <span className="font-semibold min-w-[120px]">Submitted:</span>
                <span>Your application has been received and is pending review</span>
              </li>
              <li className="flex gap-2">
                <span className="font-semibold min-w-[120px]">Under Review:</span>
                <span>Board members are reviewing your application</span>
              </li>
              <li className="flex gap-2">
                <span className="font-semibold min-w-[120px]">Approved:</span>
                <span>Your application has been approved! Welcome to WWMAA</span>
              </li>
              <li className="flex gap-2">
                <span className="font-semibold min-w-[120px]">Rejected:</span>
                <span>Your application was not approved. You may reapply after the specified period</span>
              </li>
            </ul>
            <p className="text-xs text-blue-700 mt-4">
              Most applications are reviewed within 5-7 business days
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
