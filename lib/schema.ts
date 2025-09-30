/**
 * Schema.org Structured Data Utilities
 *
 * This file provides reusable functions for generating Schema.org JSON-LD
 * structured data following the WWMAA SEO strategy plan.
 */

/**
 * BlogPosting Schema Generator
 *
 * Creates a structured data object for blog posts following Schema.org BlogPosting spec.
 * This schema helps search engines understand blog content and can enable rich results.
 *
 * @param options - Blog post metadata
 * @returns Schema.org BlogPosting JSON-LD object
 *
 * @example
 * ```tsx
 * const schema = generateBlogPostingSchema({
 *   headline: "5 Essential Techniques for Belt Advancement",
 *   description: "Learn the key techniques you need to master for your next belt rank",
 *   slug: "belt-advancement-techniques",
 *   author: { name: "Master Johnson", jobTitle: "Chief Instructor" },
 *   publishedDate: "2025-09-15",
 *   modifiedDate: "2025-09-20",
 *   imageUrl: "/images/blog/belt-techniques.jpg",
 *   keywords: ["martial arts", "belt advancement", "training techniques"]
 * });
 * ```
 */
export function generateBlogPostingSchema(options: {
  headline: string;
  description: string;
  slug: string;
  author: {
    name: string;
    jobTitle?: string;
  };
  publishedDate: string;
  modifiedDate?: string;
  imageUrl?: string;
  keywords?: string[];
  articleBody?: string;
}) {
  const {
    headline,
    description,
    slug,
    author,
    publishedDate,
    modifiedDate,
    imageUrl,
    keywords,
    articleBody,
  } = options;

  const baseUrl = "https://wwmaa.ainative.studio";
  const fullUrl = `${baseUrl}/blog/${slug}`;
  const fullImageUrl = imageUrl
    ? imageUrl.startsWith("http")
      ? imageUrl
      : `${baseUrl}${imageUrl}`
    : `${baseUrl}/images/logo.png`;

  return {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline,
    description,
    url: fullUrl,
    image: fullImageUrl,
    author: {
      "@type": "Person",
      name: author.name,
      ...(author.jobTitle && { jobTitle: author.jobTitle }),
    },
    publisher: {
      "@type": "SportsOrganization",
      name: "World Wide Martial Arts Association",
      alternateName: "WWMAA",
      logo: {
        "@type": "ImageObject",
        url: `${baseUrl}/images/logo.png`,
      },
    },
    datePublished: publishedDate,
    dateModified: modifiedDate || publishedDate,
    ...(articleBody && { articleBody }),
    ...(keywords && keywords.length > 0 && { keywords: keywords.join(", ") }),
    mainEntityOfPage: {
      "@type": "WebPage",
      "@id": fullUrl,
    },
    inLanguage: "en-US",
  };
}

/**
 * FAQPage Schema Generator
 *
 * Creates structured data for FAQ pages with question/answer pairs.
 * This can enable FAQ rich results in search engines.
 *
 * @param faqs - Array of question and answer pairs
 * @returns Schema.org FAQPage JSON-LD object
 *
 * @example
 * ```tsx
 * const schema = generateFAQSchema([
 *   {
 *     question: "What martial arts disciplines does WWMAA teach?",
 *     answer: "WWMAA offers training in Judo, Karate, Jiu-Jitsu, Kendo, and various self-defense techniques."
 *   },
 *   {
 *     question: "How much does WWMAA membership cost?",
 *     answer: "We offer three tiers: Basic ($99/year), Premium ($199/year), and Instructor ($299/year)."
 *   }
 * ]);
 * ```
 */
export function generateFAQSchema(
  faqs: Array<{ question: string; answer: string }>
) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqs.map((faq) => ({
      "@type": "Question",
      name: faq.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: faq.answer,
      },
    })),
  };
}

/**
 * SportsEvent Schema Generator
 *
 * Creates structured data for martial arts events, tournaments, and seminars.
 *
 * @param options - Event details
 * @returns Schema.org SportsEvent JSON-LD object
 *
 * @example
 * ```tsx
 * const schema = generateSportsEventSchema({
 *   name: "WWMAA National Judo Championships 2025",
 *   description: "Annual national judo tournament featuring competitors from across the country",
 *   startDate: "2025-10-15T09:00:00-05:00",
 *   endDate: "2025-10-17T18:00:00-05:00",
 *   location: {
 *     name: "Chicago Convention Center",
 *     address: {
 *       city: "Chicago",
 *       region: "IL",
 *       postalCode: "60601",
 *       country: "US"
 *     }
 *   },
 *   price: 50,
 *   eventUrl: "/events/national-championships"
 * });
 * ```
 */
export function generateSportsEventSchema(options: {
  name: string;
  description: string;
  startDate: string;
  endDate: string;
  location: {
    name: string;
    address?: {
      street?: string;
      city?: string;
      region?: string;
      postalCode?: string;
      country: string;
    };
  };
  price?: number;
  eventUrl?: string;
  imageUrl?: string;
  eventStatus?: "scheduled" | "cancelled" | "postponed" | "rescheduled";
  attendanceMode?: "offline" | "online" | "mixed";
}) {
  const {
    name,
    description,
    startDate,
    endDate,
    location,
    price,
    eventUrl,
    imageUrl,
    eventStatus = "scheduled",
    attendanceMode = "offline",
  } = options;

  const baseUrl = "https://wwmaa.ainative.studio";
  const statusMap = {
    scheduled: "https://schema.org/EventScheduled",
    cancelled: "https://schema.org/EventCancelled",
    postponed: "https://schema.org/EventPostponed",
    rescheduled: "https://schema.org/EventRescheduled",
  };

  const attendanceModeMap = {
    offline: "https://schema.org/OfflineEventAttendanceMode",
    online: "https://schema.org/OnlineEventAttendanceMode",
    mixed: "https://schema.org/MixedEventAttendanceMode",
  };

  return {
    "@context": "https://schema.org",
    "@type": "SportsEvent",
    name,
    description,
    startDate,
    endDate,
    eventStatus: statusMap[eventStatus],
    eventAttendanceMode: attendanceModeMap[attendanceMode],
    location: {
      "@type": "Place",
      name: location.name,
      ...(location.address && {
        address: {
          "@type": "PostalAddress",
          ...(location.address.street && {
            streetAddress: location.address.street,
          }),
          ...(location.address.city && {
            addressLocality: location.address.city,
          }),
          ...(location.address.region && {
            addressRegion: location.address.region,
          }),
          ...(location.address.postalCode && {
            postalCode: location.address.postalCode,
          }),
          addressCountry: location.address.country,
        },
      }),
    },
    organizer: {
      "@type": "SportsOrganization",
      name: "World Wide Martial Arts Association",
      url: baseUrl,
    },
    ...(price !== undefined && {
      offers: {
        "@type": "Offer",
        price: price.toFixed(2),
        priceCurrency: "USD",
        availability: "https://schema.org/InStock",
        url: eventUrl ? `${baseUrl}${eventUrl}` : baseUrl,
      },
    }),
    ...(imageUrl && { image: imageUrl.startsWith("http") ? imageUrl : `${baseUrl}${imageUrl}` }),
  };
}

/**
 * Course Schema Generator
 *
 * Creates structured data for martial arts training programs and courses.
 *
 * @param options - Course details
 * @returns Schema.org Course JSON-LD object
 */
export function generateCourseSchema(options: {
  name: string;
  description: string;
  courseMode?: "online" | "offline" | "blended";
  duration?: string; // ISO 8601 duration format, e.g., "P6M" for 6 months
  price?: number;
  educationalCredential?: string;
}) {
  const {
    name,
    description,
    courseMode = "blended",
    duration,
    price,
    educationalCredential,
  } = options;

  const courseModeMap = {
    online: "Online",
    offline: "Onsite",
    blended: "Blended",
  };

  return {
    "@context": "https://schema.org",
    "@type": "Course",
    name,
    description,
    provider: {
      "@type": "SportsOrganization",
      name: "World Wide Martial Arts Association",
      url: "https://wwmaa.ainative.studio",
    },
    hasCourseInstance: {
      "@type": "CourseInstance",
      courseMode: courseModeMap[courseMode],
      ...(duration && { duration }),
    },
    ...(price !== undefined && {
      offers: {
        "@type": "Offer",
        price: price.toFixed(2),
        priceCurrency: "USD",
      },
    }),
    ...(educationalCredential && {
      educationalCredentialAwarded: educationalCredential,
    }),
  };
}

/**
 * Breadcrumb Schema Generator
 *
 * Creates breadcrumb navigation structured data for better SEO.
 *
 * @param breadcrumbs - Array of breadcrumb items
 * @returns Schema.org BreadcrumbList JSON-LD object
 *
 * @example
 * ```tsx
 * const schema = generateBreadcrumbSchema([
 *   { name: "Home", url: "/" },
 *   { name: "Programs", url: "/programs" },
 *   { name: "Karate", url: "/programs/karate" }
 * ]);
 * ```
 */
export function generateBreadcrumbSchema(
  breadcrumbs: Array<{ name: string; url: string }>
) {
  const baseUrl = "https://wwmaa.ainative.studio";

  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: breadcrumbs.map((crumb, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: crumb.name,
      item: crumb.url.startsWith("http") ? crumb.url : `${baseUrl}${crumb.url}`,
    })),
  };
}

/**
 * Utility function to get the props for a Schema.org JSON-LD script tag
 *
 * Use this in your Next.js components like:
 * <script {...getSchemaScriptProps(schema)} />
 *
 * @param schema - Any Schema.org object
 * @returns Props object for script tag
 *
 * @example
 * ```tsx
 * export default function BlogPost() {
 *   const schema = generateBlogPostingSchema({...});
 *   return (
 *     <article>
 *       <script {...getSchemaScriptProps(schema)} />
 *       <h1>Blog Post Title</h1>
 *       ...
 *     </article>
 *   );
 * }
 * ```
 */
export function getSchemaScriptProps(schema: Record<string, any>) {
  return {
    type: "application/ld+json" as const,
    dangerouslySetInnerHTML: { __html: JSON.stringify(schema) },
  };
}
