"use client";

import { useState, useEffect } from "react";
import { ResourceCard } from "@/components/ResourceCard";
import { resourceApi } from "@/lib/resource-api";
import { Resource, ResourceCategory } from "@/lib/types";

const CATEGORIES: { value: ResourceCategory | "all"; label: string }[] = [
  { value: "all", label: "All Resources" },
  { value: "video", label: "Videos" },
  { value: "document", label: "Documents" },
  { value: "pdf", label: "PDFs" },
  { value: "certification", label: "Certifications" },
  { value: "article", label: "Articles" },
  { value: "recording", label: "Recordings" },
];

export function ResourcesClient() {
  const [resources, setResources] = useState<Resource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<ResourceCategory | "all">("all");
  const [retrying, setRetrying] = useState(false);

  const fetchResources = async () => {
    setLoading(true);
    setError(null);
    setRetrying(false);

    try {
      const response = await resourceApi.getResources({
        category: selectedCategory === "all" ? undefined : selectedCategory,
        page: 1,
        page_size: 50,
      });
      setResources(response.resources);
    } catch (err) {
      console.error("Failed to fetch resources:", err);
      setError(err instanceof Error ? err.message : "Failed to load resources");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResources();
  }, [selectedCategory]);

  const handleRetry = () => {
    setRetrying(true);
    fetchResources();
  };

  // Loading state
  if (loading) {
    return (
      <section className="py-24 bg-white">
        <div className="mx-auto max-w-6xl px-6">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-dojo-green border-t-transparent mb-4"></div>
            <p className="text-gray-600 text-lg">Loading resources...</p>
          </div>
        </div>
      </section>
    );
  }

  // Error state
  if (error && !retrying) {
    return (
      <section className="py-24 bg-white">
        <div className="mx-auto max-w-6xl px-6">
          <div className="text-center max-w-2xl mx-auto">
            <div className="w-16 h-16 mx-auto mb-6 bg-red-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="font-display text-3xl font-bold text-dojo-navy mb-4">
              Unable to Load Resources
            </h2>
            <p className="text-gray-600 text-lg mb-8">
              {error}
            </p>
            <button
              onClick={handleRetry}
              className="inline-flex items-center gap-2 px-6 py-3 bg-dojo-green text-white font-semibold rounded-lg hover:bg-dojo-green/90 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Try Again
            </button>
          </div>
        </div>
      </section>
    );
  }

  // Empty state
  if (resources.length === 0) {
    return (
      <section className="py-24 bg-white">
        <div className="mx-auto max-w-6xl px-6">
          <div className="text-center max-w-2xl mx-auto">
            <div className="w-16 h-16 mx-auto mb-6 bg-dojo-navy/10 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-dojo-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h2 className="font-display text-3xl font-bold text-dojo-navy mb-4">
              No Resources Available Yet
            </h2>
            <p className="text-gray-600 text-lg mb-8">
              {selectedCategory === "all"
                ? "Training resources will be added soon. Check back later for videos, documents, and certifications."
                : `No ${selectedCategory} resources are currently available. Try viewing all categories.`}
            </p>
            {selectedCategory !== "all" && (
              <button
                onClick={() => setSelectedCategory("all")}
                className="inline-flex items-center gap-2 px-6 py-3 bg-dojo-green text-white font-semibold rounded-lg hover:bg-dojo-green/90 transition-colors"
              >
                View All Resources
              </button>
            )}
          </div>
        </div>
      </section>
    );
  }

  // Resources grid with filters
  return (
    <section className="py-24 bg-white">
      <div className="mx-auto max-w-6xl px-6">
        {/* Category Filter */}
        <div className="mb-12">
          <div className="flex flex-wrap gap-3 justify-center">
            {CATEGORIES.map((category) => (
              <button
                key={category.value}
                onClick={() => setSelectedCategory(category.value)}
                className={`px-5 py-2.5 rounded-lg font-semibold transition-all ${
                  selectedCategory === category.value
                    ? "bg-dojo-green text-white shadow-lg"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {category.label}
              </button>
            ))}
          </div>
        </div>

        {/* Resources count */}
        <div className="mb-8 text-center">
          <p className="text-gray-600">
            {resources.length} {resources.length === 1 ? "resource" : "resources"} found
          </p>
        </div>

        {/* Resources Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {resources.map((resource) => (
            <ResourceCard key={resource.id} resource={resource} />
          ))}
        </div>
      </div>
    </section>
  );
}
