import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Calendar, ArrowLeft, Search } from "lucide-react";

export default function EventNotFound() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-4xl px-6 py-24 text-center">
        <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-dojo-green to-dojo-navy mb-8">
          <Calendar className="w-12 h-12 text-white" />
        </div>

        <h1 className="font-display text-5xl font-bold text-dojo-navy mb-4">
          Event Not Found
        </h1>

        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          The event you're looking for doesn't exist or may have been removed.
          It could be canceled, deleted, or the link might be incorrect.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/events">
            <Button className="gradient-green gap-2">
              <Search className="h-5 w-5" />
              Browse All Events
            </Button>
          </Link>
          <Link href="/">
            <Button variant="outline" className="gap-2">
              <ArrowLeft className="h-5 w-5" />
              Back to Home
            </Button>
          </Link>
        </div>

        <div className="mt-12 p-6 bg-white rounded-xl shadow-sm max-w-2xl mx-auto">
          <h2 className="font-semibold text-gray-900 mb-4">
            Looking for something specific?
          </h2>
          <p className="text-gray-600 mb-4">
            You can explore our upcoming events, training sessions, and
            tournaments on the events page.
          </p>
          <Link
            href="/contact"
            className="text-dojo-green hover:text-dojo-green/80 font-medium"
          >
            Contact us if you need assistance
          </Link>
        </div>
      </div>
    </main>
  );
}
