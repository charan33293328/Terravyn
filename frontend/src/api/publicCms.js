/**
 * Public CMS API – No authentication required.
 * Fetches published content from the backend with language resolution.
 */

const BASE = 'http://localhost:8000/api/public';

/**
 * Fetch homepage CMS data for the given language.
 * Falls back to English server-side if translation is missing.
 */
export async function fetchHomepage(lang = 'en') {
  try {
    const res = await fetch(`${BASE}/cms/homepage?lang=${lang}`, {
      cache: 'no-store', // always get fresh data
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

/**
 * Fetch all published FAQs for the given language.
 */
export async function fetchFAQs(lang = 'en') {
  try {
    const res = await fetch(`${BASE}/cms/faqs?lang=${lang}`, {
      cache: 'no-store',
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

/**
 * Fetch published blog posts.
 */
export async function fetchBlogPosts(lang = 'en', limit = 10, skip = 0) {
  try {
    const res = await fetch(`${BASE}/cms/blog?lang=${lang}&limit=${limit}&skip=${skip}`, {
      cache: 'no-store',
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

/**
 * Fetch a single published blog post by slug.
 */
export async function fetchBlogPost(slug, lang = 'en') {
  try {
    const res = await fetch(`${BASE}/cms/blog/${slug}?lang=${lang}`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

/**
 * Fetch a legal page (privacy-policy, terms-and-conditions, etc.)
 */
export async function fetchLegalPage(slug, lang = 'en') {
  try {
    const res = await fetch(`${BASE}/cms/legal/${slug}?lang=${lang}`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

/**
 * Fetch public platform settings (name, contact, etc.)
 */
export async function fetchPublicSettings() {
  try {
    const res = await fetch(`${BASE}/settings`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}
