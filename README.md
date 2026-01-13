# Guardian Reinsurance Brokers Zambia - Static Site

A modern static website reconstructed from the WordPress database of Guardian Reinsurance Brokers Zambia Limited.

## Tech Stack

- **Framework**: [Astro](https://astro.build) v4.x
- **Styling**: [Tailwind CSS](https://tailwindcss.com) v3.x with Typography plugin
- **Content**: MDX files with frontmatter (exported from WordPress)
- **Search**: Client-side search powered by [Fuse.js](https://fusejs.io)
- **Output**: Static HTML/CSS/JS (no server runtime required)

## Project Structure

```
guardian-site-reconstruction/
├── content/                    # Exported WordPress content
│   ├── _raw/                   # Raw JSON exports
│   ├── posts/                  # Transformed post MDX files
│   ├── pages/                  # Transformed page MDX files
│   └── media-manifest.json     # List of all media files
├── public/                     # Static assets
│   ├── favicon.svg
│   ├── robots.txt
│   └── _redirects              # Netlify redirects
├── scripts/                    # WordPress export/transform scripts
│   ├── wp_discover.py          # Database discovery
│   ├── wp_export.py            # Content export to JSON
│   └── wp_transform.py         # Transform to MDX
├── src/
│   ├── components/             # Astro components
│   ├── content/                # Astro content collections
│   │   └── config.ts           # Collection schemas
│   ├── layouts/                # Page layouts
│   ├── lib/                    # Utilities
│   ├── pages/                  # Routes
│   └── styles/                 # Global CSS
├── astro.config.mjs            # Astro configuration
├── tailwind.config.mjs         # Tailwind configuration
└── package.json
```

## Quick Start

### Prerequisites

- Node.js 18+ and npm/pnpm
- Python 3.8+ (for export scripts)
- MySQL access (for initial export)

### Installation

```bash
# Clone/navigate to project
cd guardian-site-reconstruction

# Install Node dependencies
npm install
# or
pnpm install

# Install Python dependencies (for export scripts)
pip install mysql-connector-python python-dotenv
```

### Configuration

Create a `.env` file in the project root:

```env
# WordPress MySQL Database Credentials
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=your_mysql_user
DB_PASS=your_mysql_password
DB_NAME=guardianre
```

### Export Content from WordPress

If you need to re-export content from the database:

```bash
# Step 1: Discover database structure
python3 scripts/wp_discover.py

# Step 2: Export content to JSON
python3 scripts/wp_export.py

# Step 3: Transform to MDX
python3 scripts/wp_transform.py
```

### Development

```bash
# Start development server
npm run dev
# or
pnpm dev

# The site will be available at http://localhost:4321
```

### Production Build

```bash
# Build static site
npm run build
# or
pnpm build

# Preview production build
npm run preview
# or
pnpm preview
```

## Deployment

### Netlify

1. Connect your repository to Netlify
2. Set build command: `npm run build`
3. Set publish directory: `dist`
4. Deploy!

The `_redirects` file is already configured for Netlify.

### Vercel

1. Connect your repository to Vercel
2. Framework preset: Astro
3. Deploy!

### Manual / S3 / Cloudflare Pages

Build the site and upload the `dist/` directory to your static hosting provider.

## Content Management

### Adding New Posts

Create a new MDX file in `src/content/posts/`:

```mdx
---
title: "Your Post Title"
slug: "your-post-slug"
date: "2024-01-15T12:00:00"
type: "post"
status: "publish"
excerpt: "Brief description"
categories: ["news"]
tags: ["reinsurance"]
readingTime: 3
---

Your post content here...
```

### Adding New Pages

Create a new MDX file in `src/content/pages/`:

```mdx
---
title: "Page Title"
slug: "page-slug"
date: "2024-01-15T12:00:00"
type: "page"
status: "publish"
menuOrder: 0
parentId: 0
---

Your page content here...
```

## Features

- **Responsive Design**: Mobile-first, works on all devices
- **Dark Mode**: Toggle between light and dark themes
- **Search**: Client-side fuzzy search across all content
- **SEO Optimized**: Meta tags, Open Graph, canonical URLs
- **RSS Feed**: Available at `/rss.xml`
- **Sitemap**: Auto-generated at `/sitemap-index.xml`
- **Accessibility**: Skip links, ARIA labels, keyboard navigation

## Routes

| Route | Description |
|-------|-------------|
| `/` | Home page |
| `/blog` | Blog index with pagination |
| `/blog/[slug]` | Individual blog post |
| `/category/[category]` | Posts by category |
| `/tag/[tag]` | Posts by tag |
| `/search` | Search page |
| `/[slug]` | Individual pages |
| `/rss.xml` | RSS feed |
| `/sitemap-index.xml` | Sitemap |

## Original WordPress Site

- **Site Name**: Guardian Reinsurance Brokers Zambia Limited
- **Original URL**: https://guardianreinsurance.co.zm
- **Database**: MySQL `guardianre`
- **Table Prefix**: `wp_`
- **Theme**: consulting

## Scripts Reference

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run discover` | Run WP database discovery |
| `npm run export` | Export WP content to JSON |
| `npm run transform` | Transform JSON to MDX |
| `npm run prepare-content` | Run export + transform |

## License

Copyright Guardian Reinsurance Brokers Zambia Limited. All rights reserved.

---

*Site reconstructed from WordPress database on January 2026*
