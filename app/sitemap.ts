export default function sitemap() {
  const base = "https://wwmaa.org";
  return [
    { url: `${base}/`, changefreq: "weekly", priority: 1.0 },
    { url: `${base}/membership`, changefreq: "monthly", priority: 0.8 },
    { url: `${base}/programs`, changefreq: "monthly", priority: 0.8 },
    { url: `${base}/events`, changefreq: "daily", priority: 0.9 },
    { url: `${base}/blog`, changefreq: "daily", priority: 0.6 },
    { url: `${base}/resources`, changefreq: "monthly", priority: 0.6 },
    { url: `${base}/about`, changefreq: "yearly", priority: 0.5 },
    { url: `${base}/contact`, changefreq: "yearly", priority: 0.4 },
  ];
}
