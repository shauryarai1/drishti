import type { MetadataRoute } from 'next';
import { SITE_URL } from '../lib/site';

const PUBLIC_ROUTES = ['', '/your-week', '/life-summary', '/daily', '/kundli', '/panchang', '/ask', '/privacy', '/terms'];

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();
  return PUBLIC_ROUTES.map((route) => ({
    url: `${SITE_URL}${route}`,
    lastModified,
    changeFrequency: route === '' ? 'weekly' : 'monthly',
    priority: route === '' ? 1 : 0.8,
  }));
}
