export interface SearchResult {
  id: string;
  query: string;
  answer: string;
  sources?: SearchSource[];
  videoUrl?: string;
  images?: SearchImage[];
  relatedQueries?: string[];
  timestamp: string;
}

export interface SearchSource {
  id: string;
  title: string;
  url: string;
  description?: string;
  snippet?: string;
}

export interface SearchImage {
  id: string;
  url: string;
  alt: string;
  caption?: string;
  thumbnail?: string;
}

export interface FeedbackData {
  resultId: string;
  helpful: boolean;
  comment?: string;
}
