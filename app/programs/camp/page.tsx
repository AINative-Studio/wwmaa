"use client";

import { useState } from "react";
import { Calendar, Users, Award, Clock } from "lucide-react";

const galleryImages = [
  {
    id: 1,
    url: "/images/camp/camp-1.jpg",
    alt: "Martial arts summer camp students practicing judo throws at WWMAA intensive training program"
  },
  {
    id: 2,
    url: "/images/camp/camp-2.jpg",
    alt: "WWMAA summer camp participants learning karate techniques from master instructors"
  },
  {
    id: 3,
    url: "/images/camp/camp-3.jpg",
    alt: "Group martial arts training activities at World Wide Martial Arts Association summer camp"
  },
  {
    id: 4,
    url: "/images/camp/camp-4.jpg",
    alt: "Expert martial arts instructor demonstrating advanced techniques at WWMAA camp"
  },
  {
    id: 5,
    url: "/images/camp/camp-5.jpg",
    alt: "Students practicing jiu-jitsu grappling techniques during WWMAA intensive training camp"
  },
  {
    id: 6,
    url: "/images/camp/camp-6.jpg",
    alt: "Martial arts camp participants from around the world training together at WWMAA"
  },
  {
    id: 7,
    url: "/images/camp/camp-7.jpg",
    alt: "Intensive martial arts training drills at WWMAA summer camp for all skill levels"
  },
  {
    id: 8,
    url: "/images/camp/camp-8.jpg",
    alt: "WWMAA summer camp activities including karate, judo, and self-defense training"
  },
  {
    id: 9,
    url: "/images/camp/camp-9.jpg",
    alt: "Group photo of martial arts students and instructors at WWMAA summer camp 2025"
  },
  {
    id: 10,
    url: "/images/camp/camp-10.jpg",
    alt: "Morning martial arts training session at World Wide Martial Arts Association camp"
  },
  {
    id: 11,
    url: "/images/camp/camp-11.jpg",
    alt: "Advanced martial arts practitioners training at WWMAA intensive summer program"
  },
  {
    id: 12,
    url: "/images/camp/camp-12.jpg",
    alt: "Memorable moments from WWMAA martial arts summer camp training and certification"
  }
];

const eventSchema = {
  "@context": "https://schema.org",
  "@type": "SportsEvent",
  "name": "WWMAA Summer Camp 2025",
  "description": "3-day intensive martial arts training camp featuring judo, karate, and jiu-jitsu instruction",
  "startDate": "2025-07-15T08:00:00-05:00",
  "endDate": "2025-07-17T18:00:00-05:00",
  "eventStatus": "https://schema.org/EventScheduled",
  "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
  "location": {
    "@type": "Place",
    "name": "WWMAA Training Center",
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "City",
      "addressRegion": "ST",
      "addressCountry": "US"
    }
  },
  "organizer": {
    "@type": "SportsOrganization",
    "name": "World Wide Martial Arts Association",
    "url": "https://wwmaa.ainative.studio"
  },
  "offers": {
    "@type": "Offer",
    "price": "299.00",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock",
    "url": "https://wwmaa.ainative.studio/programs/camp",
    "validFrom": "2025-01-01"
  },
  "performer": {
    "@type": "Person",
    "name": "Master Instructors",
    "description": "World-class martial arts instructors specializing in judo, karate, and jiu-jitsu"
  },
  "image": "https://wwmaa.ainative.studio/images/camp/camp-1.jpg"
};

export default function CampPage() {
  const [selectedImage, setSelectedImage] = useState<number | null>(null);

  return (
    <div className="min-h-screen">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(eventSchema) }}
      />
      <header className="gradient-hero py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center">
            <h1 className="font-display text-5xl sm:text-6xl font-bold text-white mb-4">
              Martial Arts Summer Camp
            </h1>
            <p className="text-2xl text-white/90">
              Intensive 3-day training program in judo, karate, and martial arts for all skill levels
            </p>
          </div>
        </div>
      </header>

      <section className="py-16 bg-white" aria-labelledby="about-camp-heading">
        <div className="mx-auto max-w-5xl px-6">
          <article className="mb-12">
            <h2 id="about-camp-heading" className="font-display text-4xl font-bold text-dojo-navy mb-6 text-center">
              About the Martial Arts Training Camp
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
          </article>

          <div className="grid md:grid-cols-2 gap-8">
            <article className="bg-gradient-to-br from-dojo-navy/5 to-dojo-navy/10 rounded-xl p-8">
              <Calendar className="w-12 h-12 text-dojo-navy mb-4" aria-hidden="true" />
              <h3 className="font-display text-2xl font-bold text-dojo-navy mb-3">Training Duration</h3>
              <p className="text-gray-700">
                Three intensive days of martial arts training, typically held in July. Check our events calendar for exact dates.
              </p>
            </article>

            <article className="bg-gradient-to-br from-dojo-green/5 to-dojo-green/10 rounded-xl p-8">
              <Users className="w-12 h-12 text-dojo-green mb-4" aria-hidden="true" />
              <h3 className="font-display text-2xl font-bold text-dojo-navy mb-3">Who Can Attend</h3>
              <p className="text-gray-700">
                Open to all WWMAA members of all skill levels, from beginners to advanced martial arts practitioners.
              </p>
            </article>

            <article className="bg-gradient-to-br from-dojo-orange/5 to-dojo-orange/10 rounded-xl p-8">
              <Clock className="w-12 h-12 text-dojo-orange mb-4" aria-hidden="true" />
              <h3 className="font-display text-2xl font-bold text-dojo-navy mb-3">Daily Schedule</h3>
              <p className="text-gray-700">
                Full-day martial arts training sessions from 8 AM to 6 PM, with breaks for meals and rest. Evening activities available.
              </p>
            </article>

            <article className="bg-gradient-to-br from-dojo-red/5 to-dojo-red/10 rounded-xl p-8">
              <Award className="w-12 h-12 text-dojo-red mb-4" aria-hidden="true" />
              <h3 className="font-display text-2xl font-bold text-dojo-navy mb-3">Martial Arts Certification</h3>
              <p className="text-gray-700">
                Participants receive a certificate of completion and may be eligible for belt rank advancement.
              </p>
            </article>
          </div>
        </div>
      </section>

      <section className="py-16 bg-gradient-to-b from-white to-gray-50" aria-labelledby="gallery-heading">
        <div className="mx-auto max-w-7xl px-6">
          <header className="text-center mb-12">
            <h2 id="gallery-heading" className="font-display text-4xl font-bold text-dojo-navy mb-4">
              Martial Arts Training Camp Gallery
            </h2>
            <p className="text-xl text-gray-600">
              Moments from our previous summer camps
            </p>
          </header>

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
