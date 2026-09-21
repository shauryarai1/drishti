// One place for the canonical production site used by metadata, robots and
// the sitemap. Local development keeps working because metadata URLs are only
// consumed by crawlers/OG consumers.
export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://kavachtoday.com';
export const SITE_NAME = 'KAVACH';
