"use client";

import { useState } from "react";
import { Calendar, Users, Award, Clock } from "lucide-react";

const galleryImages = [
  {
    id: 1,
    url: "https://images.pexels.com/photos/7988754/pexels-photo-7988754.jpeg?auto=compress&cs=tinysrgb&w=800",
    alt: "Martial arts training session"
  },
  {
    id: 2,
    url: "https://images.pexels.com/photos/7988766/pexels-photo-7988766.jpeg?auto=compress&cs=tinysrgb&w=800",
    alt: "Students practicing forms"
  },
  {
    id: 3,
    url: "https://images.pexels.com/photos/7045702/pexels-photo-7045702.jpeg?auto=compress&cs=tinysrgb&w=800",
    alt: "Group training"
  },
  {
    id: 4,
    url: "https://images.pexels.com/photos/7045389/pexels-photo-7045389.jpeg?auto=compress&cs=tinysrgb&w=800",
    alt: "Instructor demonstration"
  },
  {
    id: 5,
    url: "https://images.pexels.com/photos/7045865/pexels-photo-7045865.jpeg?auto=compress&cs=tinysrgb&w=800",
    alt: "Belt ceremony"
  },
  {
    id: 6,
    url: "https://images.pexels.com/photos/7045697/pexels-photo-7045697.jpeg?auto=compress&cs=tinysrgb&w=800",
    alt: "Camp activities"
  }
];

export default function CampPage() {
  const [selectedImage, setSelectedImage] = useState<number | null>(null);

  return (
    <div className="min-h-screen">
      <section className="gradient-hero py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center">
            <h1 className="font-display text-5xl sm:text-6xl font-bold text-white mb-4">
              WWMAA Summer Camp
            </h1>
            <p className="text-2xl text-white/90">
              An immersive martial arts experience for all ages
            </p>
          </div>
        </div>
      </section>

      <section className="py-24 bg-white">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-16">
            <h2 className="font-display text-4xl font-bold text-dojo-navy mb-6 text-center">
              About the Camp
            </h2>
            <div className="prose prose-lg max-w-none">
              <p className="text-xl text-gray-700 leading-relaxed mb-6">
                Our annual WWMAA Summer Camp is a transformative experience where students from around the world gather to train under master instructors, build lasting friendships, and deepen their understanding of martial arts.
              </p>
              <p className="text-lg text-gray-600 leading-relaxed mb-6">
                The camp offers intensive training sessions in multiple disciplines including Karate, Ju-Jitsu, Kendo, and Self-Defense. Students participate in workshops, seminars, and hands-on training that challenge both body and mind while fostering the core values of respect, discipline, and perseverance.
              </p>
              <p className="text-lg text-gray-600 leading-relaxed">
                Each day is carefully structured to balance rigorous training with rest and recovery, ensuring students get the most out of their experience. From early morning warm-ups to evening reflection sessions, every moment is designed to help participants grow as martial artists and individuals.
              </p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-16">
            <div className="bg-gradient-to-br from-dojo-navy/5 to-dojo-navy/10 rounded-xl p-8">
              <Calendar className="w-12 h-12 text-dojo-navy mb-4" />
              <h3 className="font-display text-2xl font-bold text-dojo-navy mb-3">Duration</h3>
              <p className="text-gray-700">
                Three intensive days of training, typically held in July. Check our events calendar for exact dates.
              </p>
            </div>

            <div className="bg-gradient-to-br from-dojo-green/5 to-dojo-green/10 rounded-xl p-8">
              <Users className="w-12 h-12 text-dojo-green mb-4" />
              <h3 className="font-display text-2xl font-bold text-dojo-navy mb-3">Who Can Attend</h3>
              <p className="text-gray-700">
                Open to all WWMAA members of all skill levels, from beginners to advanced practitioners.
              </p>
            </div>

            <div className="bg-gradient-to-br from-dojo-orange/5 to-dojo-orange/10 rounded-xl p-8">
              <Clock className="w-12 h-12 text-dojo-orange mb-4" />
              <h3 className="font-display text-2xl font-bold text-dojo-navy mb-3">Schedule</h3>
              <p className="text-gray-700">
                Full-day sessions from 8 AM to 6 PM, with breaks for meals and rest. Evening activities available.
              </p>
            </div>

            <div className="bg-gradient-to-br from-dojo-red/5 to-dojo-red/10 rounded-xl p-8">
              <Award className="w-12 h-12 text-dojo-red mb-4" />
              <h3 className="font-display text-2xl font-bold text-dojo-navy mb-3">Certification</h3>
              <p className="text-gray-700">
                Participants receive a certificate of completion and may be eligible for rank advancement.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-24 bg-gradient-to-b from-white to-gray-50">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-12">
            <h2 className="font-display text-4xl font-bold text-dojo-navy mb-4">
              Camp Gallery
            </h2>
            <p className="text-xl text-gray-600">
              Moments from our previous summer camps
            </p>
          </div>

          {/* Google Photos Album Embed */}
          <div className="mb-16">
            <div className="relative w-full rounded-xl overflow-hidden shadow-2xl bg-white" style={{ paddingBottom: '75%' }}>
              <iframe
                src="https://photos.google.com/share/AF1QipNxryr6f_JMh1TwokLSW5tR7JQt1E-12OkYf1heEhbuP8Qgkz3EIwyuy3eOpBmhLw?key=UkltNkpDaUNSaE5mZVVVOC01amYtdXJaNFRyZ3Vn&hl=en"
                className="absolute top-0 left-0 w-full h-full border-0"
                allow="autoplay"
                title="WWMAA Summer Camp Photo Album"
              />
            </div>
            <div className="text-center mt-6">
              <a
                href="https://photos.google.com/share/AF1QipNxryr6f_JMh1TwokLSW5tR7JQt1E-12OkYf1heEhbuP8Qgkz3EIwyuy3eOpBmhLw?key=UkltNkpDaUNSaE5mZVVVOC01amYtdXJaNFRyZ3Vn"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-dojo-navy hover:text-dojo-green font-semibold transition-colors"
              >
                View Full Album on Google Photos
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            </div>
          </div>

          {/* Sample Gallery Images */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {galleryImages.map((image) => (
              <div
                key={image.id}
                className="relative aspect-[4/3] overflow-hidden rounded-xl cursor-pointer group"
                onClick={() => setSelectedImage(image.id)}
              >
                <img
                  src={image.url}
                  alt={image.alt}
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            ))}
          </div>

          {selectedImage && (
            <div
              className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
              onClick={() => setSelectedImage(null)}
            >
              <button
                className="absolute top-4 right-4 text-white text-4xl hover:text-gray-300 transition-colors"
                onClick={() => setSelectedImage(null)}
              >
                &times;
              </button>
              <img
                src={galleryImages.find(img => img.id === selectedImage)?.url}
                alt={galleryImages.find(img => img.id === selectedImage)?.alt}
                className="max-w-full max-h-full object-contain"
              />
            </div>
          )}
        </div>
      </section>

      <section className="py-16 bg-gradient-to-r from-dojo-navy to-dojo-green">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h2 className="font-display text-3xl sm:text-4xl font-bold text-white mb-6">
            Ready to Join Us?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Registration opens in the spring. Don't miss this incredible opportunity to train with the best!
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/membership"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-8 py-4 text-lg font-semibold text-dojo-navy shadow-lg hover:shadow-xl transition-all"
            >
              Become a Member
            </a>
            <a
              href="/events"
              className="inline-flex items-center justify-center rounded-xl border-2 border-white px-8 py-4 text-lg font-semibold text-white hover:bg-white hover:text-dojo-navy transition-all"
            >
              View Events
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
