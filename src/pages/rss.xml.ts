import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

export async function GET(context: APIContext) {
  const posts = await getCollection('posts');

  // Sort posts by date (newest first)
  const sortedPosts = posts.sort(
    (a, b) => new Date(b.data.date).getTime() - new Date(a.data.date).getTime()
  );

  return rss({
    title: 'Guardian Reinsurance Brokers Zambia - News & Insights',
    description:
      'Stay informed with the latest news, insights, and updates from Guardian Reinsurance Brokers Zambia Limited.',
    site: context.site || 'https://guardianreinsurance.co.zm',
    items: sortedPosts.map((post) => ({
      title: post.data.title,
      pubDate: new Date(post.data.date),
      description: post.data.excerpt || '',
      link: `/insights/${post.slug}/`,
      categories: post.data.categories || [],
    })),
    customData: `<language>en-zm</language>`,
  });
}
