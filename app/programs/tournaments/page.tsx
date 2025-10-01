"use client";

import { useState, useEffect } from "react";
import { Trophy, Medal, Award, Calendar } from "lucide-react";

const tournaments2024 = [
  {
    name: "Anthony Devas",
    place: "4th Place",
    image: "/images/camp/camp-1.jpg"
  },
  {
    name: "Ahmed Abo-Mahmood",
    place: "2nd Place",
    image: "/images/camp/camp-2.jpg"
  },
  {
    name: "Abdurahman Ismail",
    place: "3rd Place",
    image: "/images/camp/camp-3.jpg"
  },
  {
    name: "Asiya Ismail",
    place: "3rd Place",
    image: "/images/camp/camp-4.jpg"
  }
];

const results2023 = [
  {
    rank: 1,
    name: "Philipp Vojta",
    country: "United States",
    school: "White Dragon Judo",
    medal: "gold"
  },
  {
    rank: 2,
    name: "Jack Haarmann",
    country: "United States",
    school: "Katamedo Jujitsu",
    medal: "silver"
  },
  {
    rank: 3,
    name: "Dylan Phelps",
    country: "United States",
    school: "Jefferson City Judo Club",
    medal: "bronze"
  }
];

export default function TournamentsPage() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  useEffect(() => {
    // Set page title and description
    document.title = "Martial Arts Tournaments & Competitions | WWMAA Events";
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute("content", "Compete in WWMAA-sanctioned martial arts tournaments. National and international events for all belt ranks.");
    } else {
      const meta = document.createElement('meta');
      meta.name = 'description';
      meta.content = 'Compete in WWMAA-sanctioned martial arts tournaments. National and international events for all belt ranks.';
      document.head.appendChild(meta);
    }
  }, []);

  const getMedalColor = (medal: string) => {
    switch(medal) {
      case "gold": return "bg-gradient-to-br from-yellow-400 to-yellow-600";
      case "silver": return "bg-gradient-to-br from-gray-300 to-gray-500";
      case "bronze": return "bg-gradient-to-br from-amber-600 to-amber-800";
      default: return "bg-gray-200";
    }
  };

  const getPlaceColor = (place: string) => {
    if (place.includes("1st")) return "text-yellow-600";
    if (place.includes("2nd")) return "text-gray-500";
    if (place.includes("3rd") || place.includes("4th")) return "text-amber-700";
    return "text-gray-600";
  };

  return (
    <div className="min-h-screen">
      <section className="relative bg-gradient-to-r from-dojo-red via-dojo-orange to-yellow-500 py-32 overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjEpIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-30"></div>
        <div className="relative mx-auto max-w-7xl px-6">
          <div className="text-center">
            <h1 className="font-display text-5xl sm:text-6xl font-bold text-white mb-4">
              Tournament Media & Results
            </h1>
            <p className="text-2xl text-white/90">
              Celebrating our competitors and their achievements
            </p>
          </div>
        </div>
      </section>

      <section className="py-24 bg-white">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-16">
            <h2 className="font-display text-4xl font-bold text-dojo-navy mb-4">
              About WWMAA Tournaments
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              Our tournaments provide a platform for members to test their skills, demonstrate their discipline,
              and compete at the highest levels. We host regional and international competitions throughout the
              year, welcoming practitioners of all ages and skill levels.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-dojo-navy to-dojo-green mb-4">
                <Trophy className="w-10 h-10 text-white" />
              </div>
              <h3 className="font-display text-2xl font-bold text-dojo-navy mb-2">
                Competitive Excellence
              </h3>
              <p className="text-gray-600">
                Tournament divisions for all belt ranks and age categories
              </p>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-dojo-orange to-dojo-red mb-4">
                <Medal className="w-10 h-10 text-white" />
              </div>
              <h3 className="font-display text-2xl font-bold text-dojo-navy mb-2">
                Recognition & Awards
              </h3>
              <p className="text-gray-600">
                Medals, trophies, and certificates for top performers
              </p>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-dojo-green to-dojo-navy mb-4">
                <Award className="w-10 h-10 text-white" />
              </div>
              <h3 className="font-display text-2xl font-bold text-dojo-navy mb-2">
                Skill Development
              </h3>
              <p className="text-gray-600">
                Learn from competition and grow as a martial artist
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-24 bg-gradient-to-b from-white to-gray-50">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex items-center justify-center gap-3 mb-12">
            <Calendar className="w-8 h-8 text-dojo-navy" />
            <h2 className="font-display text-4xl font-bold text-dojo-navy">
              2024 Mid States Championship
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {tournaments2024.map((competitor, idx) => (
              <div
                key={idx}
                className="bg-white rounded-xl overflow-hidden shadow-hover border-2 border-border group cursor-pointer"
                onClick={() => setSelectedImage(competitor.image)}
              >
                <div className="aspect-[3/4] overflow-hidden">
                  <img
                    src={competitor.image}
                    alt={`${competitor.name} - ${competitor.place} at WWMAA 2024 Mid States Championship martial arts tournament`}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                  />
                </div>
                <div className="p-6 text-center">
                  <h3 className="font-display text-xl font-bold text-dojo-navy mb-2">
                    {competitor.name}
                  </h3>
                  <p className={`text-lg font-semibold ${getPlaceColor(competitor.place)}`}>
                    {competitor.place}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-24 bg-white">
        <div className="mx-auto max-w-5xl px-6">
          <div className="flex items-center justify-center gap-3 mb-12">
            <Calendar className="w-8 h-8 text-dojo-navy" />
            <h2 className="font-display text-4xl font-bold text-dojo-navy">
              2023 Freestyle Judo Winter Challenge
            </h2>
          </div>

          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-gray-700">
              <div className="flex items-center justify-between">
                <h3 className="font-display text-xl font-bold text-white">
                  MEN / INTERMEDIATE / ABOVE 17 / -85 KG / CHOKES & ARM LOCKS
                </h3>
                <span className="px-4 py-2 bg-gray-700 text-gray-300 text-sm font-semibold rounded-lg">
                  BRACKET
                </span>
              </div>
            </div>

            <div className="divide-y divide-gray-700">
              {results2023.map((result) => (
                <div
                  key={result.rank}
                  className="flex items-center gap-6 p-6 hover:bg-gray-800/50 transition-colors"
                >
                  <div className={`flex items-center justify-center w-14 h-14 rounded-full ${getMedalColor(result.medal)} flex-shrink-0`}>
                    <span className="text-2xl font-bold text-white">{result.rank}</span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <h4 className="font-display text-xl font-bold text-white">
                        {result.name}
                      </h4>
                      <span className="text-gray-400 text-sm">🇺🇸 {result.country}</span>
                    </div>
                    <p className="text-gray-400">{result.school}</p>
                  </div>

                  {result.rank === 1 && (
                    <Trophy className="w-8 h-8 text-yellow-500 flex-shrink-0" />
                  )}
                  {result.rank === 2 && (
                    <Medal className="w-8 h-8 text-gray-400 flex-shrink-0" />
                  )}
                  {result.rank === 3 && (
                    <Award className="w-8 h-8 text-amber-700 flex-shrink-0" />
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="mt-12 text-center">
            <p className="text-gray-600 mb-6">
              View complete tournament brackets and results
            </p>
            <a
              href="/events"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-dojo-navy to-dojo-green px-8 py-4 text-lg font-semibold text-white shadow-lg hover:shadow-xl transition-all"
            >
              View All Events
            </a>
          </div>
        </div>
      </section>

      <section className="py-16 bg-gradient-to-r from-dojo-orange to-dojo-red">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h2 className="font-display text-3xl sm:text-4xl font-bold text-white mb-6">
            Ready to Compete?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Register for upcoming tournaments and showcase your skills on the mat
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
              className="inline-flex items-center justify-center rounded-xl border-2 border-white px-8 py-4 text-lg font-semibold text-white hover:bg-white hover:text-dojo-orange transition-all"
            >
              Upcoming Tournaments
            </a>
          </div>
        </div>
      </section>

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
            src={selectedImage}
            alt="Tournament photo"
            className="max-w-full max-h-full object-contain"
          />
        </div>
      )}
    </div>
  );
}
