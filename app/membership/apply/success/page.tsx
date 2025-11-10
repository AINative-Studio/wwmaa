"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { CheckCircle2, FileText, Home, Mail } from "lucide-react";

export default function ApplicationSuccessPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [applicationId, setApplicationId] = useState<string | null>(null);

  useEffect(() => {
    const id = searchParams.get("id");
    if (!id) {
      // Redirect to home if no application ID is provided
      router.push("/");
    } else {
      setApplicationId(id);
    }
  }, [searchParams, router]);

  if (!applicationId) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        {/* Success Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 mb-4">
            <CheckCircle2 className="w-12 h-12 text-green-600" />
          </div>
          <h1 className="text-4xl font-bold text-dojo-navy mb-2">
            Application Submitted Successfully!
          </h1>
          <p className="text-gray-600 text-lg">
            Thank you for applying to join WWMAA
          </p>
        </div>

        {/* Application Details Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Application Confirmation</CardTitle>
            <CardDescription>
              Your application has been received and is being processed
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  Application ID
                </span>
                <span className="text-lg font-bold text-dojo-navy">
                  {applicationId}
                </span>
              </div>
            </div>

            <Alert>
              <Mail className="h-4 w-4" />
              <AlertTitle>Check Your Email</AlertTitle>
              <AlertDescription>
                A confirmation email has been sent to your registered email
                address with your application details and next steps.
              </AlertDescription>
            </Alert>

            <div className="space-y-3 pt-4 border-t">
              <h3 className="font-semibold text-gray-900">What Happens Next?</h3>
              <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700">
                <li>
                  Our membership committee will review your application within
                  5-7 business days
                </li>
                <li>
                  We will contact your references to verify your martial arts
                  background
                </li>
                <li>
                  You will receive an email notification about your application
                  status
                </li>
                <li>
                  If approved, you will receive instructions for completing your
                  membership registration and payment
                </li>
                <li>
                  Once payment is received, you will gain full access to all
                  member benefits
                </li>
              </ol>
            </div>

            <div className="space-y-3 pt-4 border-t">
              <h3 className="font-semibold text-gray-900">
                Application Review Timeline
              </h3>
              <div className="space-y-2">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-2 h-2 mt-2 rounded-full bg-green-500"></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      Submitted
                    </p>
                    <p className="text-xs text-gray-500">Today</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-2 h-2 mt-2 rounded-full bg-gray-300"></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-700">
                      Under Review
                    </p>
                    <p className="text-xs text-gray-500">1-3 business days</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-2 h-2 mt-2 rounded-full bg-gray-300"></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-700">
                      Reference Verification
                    </p>
                    <p className="text-xs text-gray-500">3-5 business days</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-2 h-2 mt-2 rounded-full bg-gray-300"></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-700">
                      Final Decision
                    </p>
                    <p className="text-xs text-gray-500">5-7 business days</p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              What would you like to do next?
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button asChild className="w-full" variant="outline">
              <Link href={`/application-status?id=${applicationId}`}>
                <FileText className="mr-2 h-4 w-4" />
                Check Application Status
              </Link>
            </Button>

            <Button asChild className="w-full" variant="outline">
              <Link href="/membership">
                <FileText className="mr-2 h-4 w-4" />
                Learn More About Membership
              </Link>
            </Button>

            <Button asChild className="w-full" variant="outline">
              <Link href="/">
                <Home className="mr-2 h-4 w-4" />
                Return to Home
              </Link>
            </Button>
          </CardContent>
        </Card>

        {/* Contact Information */}
        <Card className="mt-6">
          <CardContent className="pt-6">
            <div className="text-center text-sm text-gray-600">
              <p className="mb-2">
                Questions about your application?
              </p>
              <p>
                Contact us at{" "}
                <a
                  href="mailto:membership@wwmaa.org"
                  className="text-dojo-navy hover:text-dojo-green font-medium"
                >
                  membership@wwmaa.org
                </a>
              </p>
              <p className="mt-2">
                Please include your Application ID: <strong>{applicationId}</strong>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
