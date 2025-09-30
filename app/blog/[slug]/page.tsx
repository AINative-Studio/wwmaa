import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { blogPosts } from "@/lib/blog-posts";
import { generateBlogPostingSchema } from "@/lib/schema";

export async function generateStaticParams() {
  return Object.keys(blogPosts).map((slug) => ({
    slug: slug,
  }));
}

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const post = blogPosts[params.slug];

  if (!post) {
    return {
      title: "Post Not Found | WWMAA Blog",
    };
  }

  return {
    title: `${post.title} | WWMAA Blog`,
    description: post.excerpt,
    keywords: post.keywords,
    authors: [{ name: post.author }],
    openGraph: {
      title: post.title,
      description: post.excerpt,
      type: "article",
      publishedTime: post.publishDate,
      modifiedTime: post.modifiedDate,
      authors: [post.author],
    },
  };
}

export default function BlogPostPage({ params }: { params: { slug: string } }) {
  const post = blogPosts[params.slug];

  if (!post) {
    notFound();
  }

  // Generate BlogPosting schema using reusable utility function
  const blogSchema = generateBlogPostingSchema({
    headline: post.title,
    description: post.excerpt,
    slug: post.slug,
    author: {
      name: post.author,
      jobTitle: post.authorTitle,
    },
    publishedDate: post.publishDate,
    modifiedDate: post.modifiedDate,
    imageUrl: post.image,
    keywords: post.keywords,
    articleBody: post.content,
  });

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(blogSchema) }}
      />

      <article className="min-h-screen bg-gradient-to-b from-bg to-white">
        <header className="gradient-hero py-24">
          <div className="mx-auto max-w-4xl px-6">
            <div className="text-center">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full text-white/90 text-sm font-semibold mb-6">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                {post.category}
              </div>

              <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6">
                {post.title}
              </h1>

              <p className="text-xl text-white/90 max-w-2xl mx-auto mb-8">
                {post.excerpt}
              </p>

              <div className="flex flex-wrap items-center justify-center gap-6 text-white/80 text-sm">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  <span>{post.author}</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <time dateTime={post.publishDate}>
                    {new Date(post.publishDate).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                      day: "numeric"
                    })}
                  </time>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{post.readingTime}</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        <div className="py-16 -mt-8">
          <div className="mx-auto max-w-4xl px-6">
            <div className="bg-white rounded-2xl shadow-hover p-8 sm:p-12">
              <div
                className="prose prose-lg max-w-none
                  prose-headings:font-display prose-headings:font-bold prose-headings:text-dojo-navy
                  prose-h2:text-3xl prose-h2:mt-12 prose-h2:mb-6
                  prose-h3:text-2xl prose-h3:mt-8 prose-h3:mb-4
                  prose-p:text-gray-700 prose-p:leading-relaxed prose-p:mb-6
                  prose-a:text-dojo-green prose-a:font-semibold prose-a:no-underline hover:prose-a:text-dojo-orange
                  prose-strong:text-dojo-navy prose-strong:font-bold
                  prose-ul:my-6 prose-li:my-2
                  prose-img:rounded-xl prose-img:shadow-lg"
                dangerouslySetInnerHTML={{ __html: post.content }}
              />

              <aside className="mt-12 pt-8 border-t border-gray-200">
                <div className="flex items-start gap-4 p-6 bg-dojo-navy/5 rounded-xl">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-dojo-navy to-dojo-green flex items-center justify-center text-white font-display text-2xl font-bold flex-shrink-0">
                    {post.author.split(" ").map(n => n[0]).join("")}
                  </div>
                  <div>
                    <h3 className="font-display text-xl font-bold text-dojo-navy">
                      {post.author}
                    </h3>
                    <p className="text-dojo-green font-semibold mb-2">
                      {post.authorTitle}
                    </p>
                    <p className="text-gray-600 text-sm leading-relaxed">
                      Contributing expert at the World Wide Martial Arts Association, dedicated to sharing knowledge and advancing martial arts excellence worldwide.
                    </p>
                  </div>
                </div>
              </aside>

              <div className="mt-8 flex flex-wrap gap-2">
                <span className="text-sm font-semibold text-gray-600">Tags:</span>
                {post.keywords.map((keyword) => (
                  <span
                    key={keyword}
                    className="px-3 py-1 bg-dojo-navy/10 text-dojo-navy text-sm font-medium rounded-full"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>

            <section className="mt-12 bg-gradient-to-br from-dojo-navy to-dojo-green rounded-2xl p-8 text-white text-center">
              <h2 className="font-display text-3xl font-bold mb-4">
                Ready to Begin Your Martial Arts Journey?
              </h2>
              <p className="text-white/90 text-lg mb-6 max-w-2xl mx-auto">
                Join thousands of martial artists worldwide who train with WWMAA. Access exclusive training resources, compete in sanctioned tournaments, and advance your belt rank with guidance from master instructors.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <a
                  href="/membership"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-dojo-orange text-white font-bold rounded-lg hover:bg-dojo-orange/90 transition-colors text-lg"
                >
                  Become a Member
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </a>
                <a
                  href="/programs"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-dojo-navy font-bold rounded-lg hover:bg-white/90 transition-colors text-lg"
                >
                  Explore Programs
                </a>
              </div>
            </section>

            <nav className="mt-12" aria-label="Related articles">
              <h2 className="font-display text-2xl font-bold text-dojo-navy mb-6">
                Continue Reading
              </h2>
              <div className="grid gap-6 sm:grid-cols-2">
                {Object.values(blogPosts)
                  .filter(p => p.slug !== post.slug)
                  .slice(0, 2)
                  .map((relatedPost) => (
                    <a
                      key={relatedPost.slug}
                      href={`/blog/${relatedPost.slug}`}
                      className="group bg-white rounded-xl p-6 shadow-hover"
                    >
                      <div className="text-xs font-semibold text-dojo-orange uppercase mb-2">
                        {relatedPost.category}
                      </div>
                      <h3 className="font-display text-xl font-bold text-dojo-navy group-hover:text-dojo-green transition-colors mb-2">
                        {relatedPost.title}
                      </h3>
                      <p className="text-gray-600 text-sm line-clamp-2 mb-3">
                        {relatedPost.excerpt}
                      </p>
                      <div className="inline-flex items-center gap-2 text-sm font-semibold text-dojo-orange">
                        Read Article
                        <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </a>
                  ))}
              </div>
            </nav>
          </div>
        </div>
      </article>
    </>
  );
}
