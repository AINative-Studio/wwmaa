"use client";

import { Resource } from "@/lib/types";
import { resourceApi } from "@/lib/resource-api";
import { useState } from "react";

interface ResourceCardProps {
  resource: Resource;
}

export function ResourceCard({ resource }: ResourceCardProps) {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleView = async () => {
    if (resource.external_url) {
      await resourceApi.trackView(resource.id);
      window.open(resource.external_url, "_blank", "noopener,noreferrer");
    } else if (resource.file_url) {
      await resourceApi.trackView(resource.id);
      window.open(resource.file_url, "_blank", "noopener,noreferrer");
    }
  };

  const handleDownload = async () => {
    if (!resource.file_url) return;

    setIsDownloading(true);
    try {
      await resourceApi.trackDownload(resource.id);
      const link = document.createElement("a");
      link.href = resource.file_url;
      link.download = resource.file_name || "download";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Download failed:", error);
    } finally {
      setIsDownloading(false);
    }
  };

  const categoryLabel = resourceApi.getCategoryLabel(resource.category);
  const categoryIconPath = resourceApi.getCategoryIcon(resource.category);
  const isVideo = resource.category === "video" || resource.category === "recording";
  const hasFile = Boolean(resource.file_url);
  const hasExternalUrl = Boolean(resource.external_url);

  return (
    <div className="group bg-white rounded-2xl overflow-hidden shadow-hover transition-all duration-300 hover:shadow-xl">
      {/* Header with category icon */}
      <div className="h-32 bg-gradient-to-br from-dojo-navy to-dojo-green relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjA1KSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-30"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={categoryIconPath} />
          </svg>
        </div>
        {resource.is_featured && (
          <div className="absolute top-3 right-3 bg-dojo-orange text-white text-xs font-bold px-3 py-1 rounded-full">
            Featured
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Category badge */}
        <div className="flex items-center gap-2 mb-3">
          <span className="inline-block px-3 py-1 bg-dojo-navy/10 text-dojo-navy text-xs font-semibold rounded-full">
            {categoryLabel}
          </span>
          {resource.discipline && (
            <span className="inline-block px-3 py-1 bg-dojo-green/10 text-dojo-green text-xs font-semibold rounded-full">
              {resource.discipline}
            </span>
          )}
        </div>

        {/* Title */}
        <h3 className="font-display text-xl font-bold text-dojo-navy mb-3 group-hover:text-dojo-green transition-colors line-clamp-2">
          {resource.title}
        </h3>

        {/* Description */}
        {resource.description && (
          <p className="text-gray-600 text-sm leading-relaxed mb-4 line-clamp-3">
            {resource.description}
          </p>
        )}

        {/* Metadata */}
        <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 mb-4">
          {isVideo && resource.video_duration_seconds && (
            <div className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{resourceApi.formatDuration(resource.video_duration_seconds)}</span>
            </div>
          )}
          {hasFile && resource.file_size_bytes && (
            <div className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              <span>{resourceApi.formatFileSize(resource.file_size_bytes)}</span>
            </div>
          )}
          {resource.view_count > 0 && (
            <div className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <span>{resource.view_count} views</span>
            </div>
          )}
        </div>

        {/* Tags */}
        {resource.tags && resource.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {resource.tags.slice(0, 3).map((tag, index) => (
              <span
                key={index}
                className="inline-block px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
              >
                {tag}
              </span>
            ))}
            {resource.tags.length > 3 && (
              <span className="inline-block px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                +{resource.tags.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={handleView}
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-dojo-green text-white font-semibold rounded-lg hover:bg-dojo-green/90 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {hasExternalUrl ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              )}
            </svg>
            <span>{hasExternalUrl ? "Open" : "View"}</span>
          </button>
          {hasFile && !hasExternalUrl && (
            <button
              onClick={handleDownload}
              disabled={isDownloading}
              className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-dojo-orange text-white font-semibold rounded-lg hover:bg-dojo-orange/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              {isDownloading ? "..." : ""}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
