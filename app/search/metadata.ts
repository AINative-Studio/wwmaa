import { Metadata } from 'next';

export function generateSearchMetadata(query?: string): Metadata {
  const title = query
    ? `Search Results for "${query}" | WWMAA`
    : 'Search | WWMAA - World Wing Martial Arts Association';

  const description = query
    ? `Find information about "${query}" in the WWMAA knowledge base`
    : 'Search the WWMAA knowledge base for martial arts information, techniques, history, and more';

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
    },
  };
}
