import { ContactForm } from "@/components/forms/contact-form";

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-bg to-white">
      <section className="gradient-hero py-24">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <h1 className="font-display text-5xl sm:text-6xl font-bold text-white">
            Get in Touch
          </h1>
          <p className="mt-6 text-xl text-white/90 max-w-2xl mx-auto">
            Have questions? We're here to help you on your martial arts journey.
          </p>
        </div>
      </section>

      <section className="py-24 -mt-12">
        <div className="mx-auto max-w-4xl px-6">
          <div className="bg-white rounded-2xl shadow-glow p-8 md:p-12">
            <ContactForm />
          </div>
        </div>
      </section>
    </div>
  );
}
