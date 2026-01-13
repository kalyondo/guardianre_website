#!/usr/bin/env python3
"""
WordPress Content Transform Script
Converts WordPress content (Gutenberg blocks, Visual Composer, shortcodes) to clean MDX.
"""

import os
import re
import json
import html
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import unicodedata

# Paths
BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / 'content' / '_raw'
OUTPUT_DIR = BASE_DIR / 'content'
POSTS_DIR = OUTPUT_DIR / 'posts'
PAGES_DIR = OUTPUT_DIR / 'pages'

# Track unknown shortcodes for reporting
unknown_shortcodes = set()
conversion_issues = []

def load_json(filename: str) -> dict:
    """Load JSON file from raw directory."""
    with open(RAW_DIR / filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text

def estimate_reading_time(content: str) -> int:
    """Estimate reading time in minutes based on word count."""
    # Strip HTML and count words
    text = re.sub(r'<[^>]+>', '', content)
    words = len(text.split())
    # Average reading speed: 200 words per minute
    return max(1, round(words / 200))

def html_to_markdown(html_content: str) -> str:
    """Convert HTML to Markdown for MDX compatibility."""
    if not html_content:
        return ''

    content = html_content

    # Remove HTML comments (not valid in MDX)
    content = re.sub(r'<!--[^>]*-->', '', content)

    # Remove CSS blocks (/*! ... */ or /* ... */)
    content = re.sub(r'/\*!?[^*]*\*+(?:[^/*][^*]*\*+)*/', '', content)

    # Remove inline style blocks
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)

    # Remove script blocks
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)

    # Remove Elementor CSS classes inline
    content = re.sub(r'\.elementor[^{]*\{[^}]*\}', '', content)

    # Remove any remaining CSS-like selectors
    content = re.sub(r'\.[a-zA-Z_-]+[^{]*\{[^}]*\}', '', content)

    # Convert headings to Markdown
    content = re.sub(r'<h1[^>]*>\s*(.*?)\s*</h1>', r'# \1\n', content, flags=re.DOTALL)
    content = re.sub(r'<h2[^>]*>\s*(.*?)\s*</h2>', r'## \1\n', content, flags=re.DOTALL)
    content = re.sub(r'<h3[^>]*>\s*(.*?)\s*</h3>', r'### \1\n', content, flags=re.DOTALL)
    content = re.sub(r'<h4[^>]*>\s*(.*?)\s*</h4>', r'#### \1\n', content, flags=re.DOTALL)
    content = re.sub(r'<h5[^>]*>\s*(.*?)\s*</h5>', r'##### \1\n', content, flags=re.DOTALL)
    content = re.sub(r'<h6[^>]*>\s*(.*?)\s*</h6>', r'###### \1\n', content, flags=re.DOTALL)

    # Convert paragraphs
    content = re.sub(r'<p[^>]*>\s*(.*?)\s*</p>', r'\1\n\n', content, flags=re.DOTALL)

    # Convert links
    content = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>\s*(.*?)\s*</a>', r'[\2](\1)', content, flags=re.DOTALL)

    # Convert bold
    content = re.sub(r'<strong[^>]*>\s*(.*?)\s*</strong>', r'**\1**', content, flags=re.DOTALL)
    content = re.sub(r'<b[^>]*>\s*(.*?)\s*</b>', r'**\1**', content, flags=re.DOTALL)

    # Convert italic
    content = re.sub(r'<em[^>]*>\s*(.*?)\s*</em>', r'*\1*', content, flags=re.DOTALL)
    content = re.sub(r'<i[^>]*>\s*(.*?)\s*</i>', r'*\1*', content, flags=re.DOTALL)

    # Convert blockquotes
    content = re.sub(r'<blockquote[^>]*>\s*(.*?)\s*</blockquote>', r'> \1\n', content, flags=re.DOTALL)

    # Convert list items
    content = re.sub(r'<li[^>]*>\s*(.*?)\s*</li>', r'- \1\n', content, flags=re.DOTALL)
    content = re.sub(r'<ul[^>]*>', '\n', content)
    content = re.sub(r'</ul>', '\n', content)
    content = re.sub(r'<ol[^>]*>', '\n', content)
    content = re.sub(r'</ol>', '\n', content)

    # Convert images
    content = re.sub(r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*/?\s*>', r'![\2](\1)\n', content)
    content = re.sub(r'<img[^>]*src="([^"]*)"[^>]*/?\s*>', r'![Image](\1)\n', content)

    # Convert line breaks
    content = re.sub(r'<br\s*/?\s*>', '\n', content)

    # Convert horizontal rules
    content = re.sub(r'<hr[^>]*/?\s*>', '\n---\n', content)

    # Remove all remaining HTML tags
    content = re.sub(r'<[^>]+>', '', content)

    # Decode HTML entities
    content = html.unescape(content)

    # Escape curly braces for MDX (they're treated as expressions)
    content = content.replace('{', '&#123;')
    content = content.replace('}', '&#125;')

    # Clean excessive whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = re.sub(r'[ \t]+', ' ', content)
    content = re.sub(r'\n +', '\n', content)
    content = re.sub(r' +\n', '\n', content)

    return content.strip()

def clean_html(html_content: str) -> str:
    """Wrapper for html_to_markdown for backwards compatibility."""
    return html_to_markdown(html_content)

def convert_gutenberg_blocks(content: str) -> str:
    """Convert Gutenberg blocks to clean HTML."""
    if not content:
        return ''

    # Remove Gutenberg block comments but keep content
    # Pattern: <!-- wp:block-name {"attrs":...} --> content <!-- /wp:block-name -->

    # Simple blocks (paragraph, heading, list, etc.)
    content = re.sub(r'<!-- wp:paragraph[^>]*-->\s*', '', content)
    content = re.sub(r'\s*<!-- /wp:paragraph -->', '', content)

    content = re.sub(r'<!-- wp:heading[^>]*-->\s*', '', content)
    content = re.sub(r'\s*<!-- /wp:heading -->', '', content)

    content = re.sub(r'<!-- wp:list[^>]*-->\s*', '', content)
    content = re.sub(r'\s*<!-- /wp:list -->', '', content)

    content = re.sub(r'<!-- wp:list-item[^>]*-->\s*', '', content)
    content = re.sub(r'\s*<!-- /wp:list-item -->', '', content)

    content = re.sub(r'<!-- wp:quote[^>]*-->\s*', '', content)
    content = re.sub(r'\s*<!-- /wp:quote -->', '', content)

    content = re.sub(r'<!-- wp:code[^>]*-->\s*', '', content)
    content = re.sub(r'\s*<!-- /wp:code -->', '', content)

    content = re.sub(r'<!-- wp:preformatted[^>]*-->\s*', '', content)
    content = re.sub(r'\s*<!-- /wp:preformatted -->', '', content)

    # Layout blocks
    content = re.sub(r'<!-- wp:group[^>]*-->\s*', '<div class="content-group">', content)
    content = re.sub(r'\s*<!-- /wp:group -->', '</div>', content)

    content = re.sub(r'<!-- wp:columns[^>]*-->\s*', '<div class="columns">', content)
    content = re.sub(r'\s*<!-- /wp:columns -->', '</div>', content)

    content = re.sub(r'<!-- wp:column[^>]*-->\s*', '<div class="column">', content)
    content = re.sub(r'\s*<!-- /wp:column -->', '</div>', content)

    # Media blocks
    content = re.sub(r'<!-- wp:image[^>]*-->\s*', '', content)
    content = re.sub(r'\s*<!-- /wp:image -->', '', content)

    content = re.sub(r'<!-- wp:gallery[^>]*-->\s*', '<div class="gallery">', content)
    content = re.sub(r'\s*<!-- /wp:gallery -->', '</div>', content)

    content = re.sub(r'<!-- wp:video[^>]*-->\s*', '', content)
    content = re.sub(r'\s*<!-- /wp:video -->', '', content)

    content = re.sub(r'<!-- wp:audio[^>]*-->\s*', '', content)
    content = re.sub(r'\s*<!-- /wp:audio -->', '', content)

    # Embed blocks
    content = re.sub(r'<!-- wp:embed[^>]*-->\s*', '<div class="embed">', content)
    content = re.sub(r'\s*<!-- /wp:embed -->', '</div>', content)

    content = re.sub(r'<!-- wp:core-embed/[^>]*-->\s*', '<div class="embed">', content)
    content = re.sub(r'\s*<!-- /wp:core-embed/[^>]* -->', '</div>', content)

    # Remove any remaining block comments
    content = re.sub(r'<!-- wp:[^>]* -->', '', content)
    content = re.sub(r'<!-- /wp:[^>]* -->', '', content)

    return content

def convert_vc_shortcodes(content: str) -> str:
    """Convert Visual Composer (WPBakery) shortcodes to HTML."""
    if not content:
        return ''

    # Track unknown shortcodes
    def track_unknown(match):
        shortcode = match.group(1)
        if shortcode not in known_shortcodes:
            unknown_shortcodes.add(shortcode)
        return match.group(0)

    known_shortcodes = {
        'vc_row', 'vc_row_inner', 'vc_column', 'vc_column_inner',
        'vc_column_text', 'vc_custom_heading', 'vc_single_image',
        'vc_separator', 'vc_empty_space', 'vc_pie', 'vc_progress_bar',
        'vc_tta_section', 'vc_tta_accordion', 'vc_tta_tabs', 'vc_btn',
        'vc_icon', 'vc_gallery', 'vc_video', 'vc_wp_search',
        'stm_spacing', 'stm_icon_box', 'stm_services', 'stm_news',
        'stm_testimonials', 'stm_testimonials_carousel', 'stm_partner',
        'stm_post_details', 'stm_image_carousel', 'stm_vacancies',
        'stm_company_history_item', 'stm_cost_calculator'
    }

    # First pass: track all shortcodes
    re.sub(r'\[(\w+)[^\]]*\]', track_unknown, content)

    # VC Row -> section/div
    content = re.sub(
        r'\[vc_row[^\]]*\]',
        '<section class="content-section">',
        content
    )
    content = re.sub(r'\[/vc_row\]', '</section>', content)

    # VC Row Inner
    content = re.sub(
        r'\[vc_row_inner[^\]]*\]',
        '<div class="row-inner">',
        content
    )
    content = re.sub(r'\[/vc_row_inner\]', '</div>', content)

    # VC Column - extract width if available
    def convert_column(match):
        attrs = match.group(1) if match.group(1) else ''
        width_match = re.search(r'width="([^"]+)"', attrs)
        offset_match = re.search(r'offset="([^"]+)"', attrs)

        classes = ['column']
        if width_match:
            width = width_match.group(1)
            # Convert fractions to percentages
            if '/' in width:
                num, den = width.split('/')
                pct = int((int(num) / int(den)) * 100)
                classes.append(f'w-{pct}')
        if offset_match:
            classes.append(offset_match.group(1).replace('vc_col-', 'col-'))

        return f'<div class="{" ".join(classes)}">'

    content = re.sub(r'\[vc_column([^\]]*)\]', convert_column, content)
    content = re.sub(r'\[/vc_column\]', '</div>', content)

    content = re.sub(r'\[vc_column_inner([^\]]*)\]', convert_column, content)
    content = re.sub(r'\[/vc_column_inner\]', '</div>', content)

    # VC Column Text - just extract content
    content = re.sub(r'\[vc_column_text[^\]]*\]', '', content)
    content = re.sub(r'\[/vc_column_text\]', '', content)

    # VC Custom Heading
    def convert_heading(match):
        attrs = match.group(1) if match.group(1) else ''
        text_match = re.search(r'text="([^"]+)"', attrs)
        text = text_match.group(1) if text_match else ''
        return f'<h2 class="section-heading">{html.unescape(text)}</h2>'

    content = re.sub(r'\[vc_custom_heading([^\]]*)\]', convert_heading, content)

    # VC Single Image
    def convert_image(match):
        attrs = match.group(1) if match.group(1) else ''
        # Extract image info if available
        return '<figure class="wp-image"><img src="/images/placeholder.jpg" alt="Image" /></figure>'

    content = re.sub(r'\[vc_single_image([^\]]*)\]', convert_image, content)

    # VC Separator
    content = re.sub(r'\[vc_separator[^\]]*\]', '<hr class="section-divider" />', content)

    # VC Empty Space
    content = re.sub(r'\[vc_empty_space[^\]]*\]', '<div class="spacer"></div>', content)

    # VC Button
    def convert_button(match):
        attrs = match.group(1) if match.group(1) else ''
        title_match = re.search(r'title="([^"]+)"', attrs)
        link_match = re.search(r'link="([^"]+)"', attrs)
        title = html.unescape(title_match.group(1)) if title_match else 'Button'
        link = '#'
        if link_match:
            link_str = html.unescape(link_match.group(1))
            url_match = re.search(r'url:([^|]+)', link_str)
            if url_match:
                link = url_match.group(1)
        return f'<a href="{link}" class="btn btn-primary">{title}</a>'

    content = re.sub(r'\[vc_btn([^\]]*)\]', convert_button, content)

    # VC Pie Chart
    def convert_pie(match):
        attrs = match.group(1) if match.group(1) else ''
        value_match = re.search(r'value="([^"]+)"', attrs)
        label_match = re.search(r'label_value="([^"]+)"', attrs)
        title_match = re.search(r'title="([^"]+)"', attrs)

        value = value_match.group(1) if value_match else '0'
        label = html.unescape(label_match.group(1)) if label_match else value
        title = html.unescape(title_match.group(1)) if title_match else ''

        return f'''<div class="stat-item">
  <span class="stat-value">{label}</span>
  <span class="stat-label">{title}</span>
</div>'''

    content = re.sub(r'\[vc_pie([^\]]*)\]', convert_pie, content)

    # STM Spacing
    content = re.sub(r'\[stm_spacing[^\]]*\]', '<div class="spacer"></div>', content)

    # STM Icon Box
    def convert_icon_box(match):
        attrs = match.group(1) if match.group(1) else ''
        title_match = re.search(r'title="([^"]+)"', attrs)
        title = html.unescape(title_match.group(1)) if title_match else ''
        return f'''<div class="icon-box">
  <h3>{title}</h3>
</div>'''

    content = re.sub(r'\[stm_icon_box([^\]]*)\]', convert_icon_box, content)

    # STM Services (placeholder)
    content = re.sub(
        r'\[stm_services[^\]]*\]',
        '<!-- TODO: Services component needs implementation -->',
        content
    )

    # STM News (placeholder)
    content = re.sub(
        r'\[stm_news[^\]]*\]',
        '<!-- TODO: News component needs implementation -->',
        content
    )

    # STM Testimonials
    content = re.sub(
        r'\[stm_testimonials[^\]]*\]',
        '<!-- TODO: Testimonials component needs implementation -->',
        content
    )
    content = re.sub(
        r'\[stm_testimonials_carousel[^\]]*\]',
        '<!-- TODO: Testimonials carousel needs implementation -->',
        content
    )

    # STM Partner
    content = re.sub(
        r'\[stm_partner[^\]]*\]',
        '<!-- TODO: Partner logos component needs implementation -->',
        content
    )

    # STM Post Details (metadata display)
    content = re.sub(r'\[stm_post_details[^\]]*\]', '', content)

    # STM Image Carousel
    content = re.sub(
        r'\[stm_image_carousel[^\]]*\]',
        '<!-- TODO: Image carousel needs implementation -->',
        content
    )

    # STM Vacancies
    content = re.sub(
        r'\[stm_vacancies[^\]]*\]',
        '<!-- TODO: Vacancies/careers listing needs implementation -->',
        content
    )

    # STM Company History
    content = re.sub(
        r'\[stm_company_history_item[^\]]*\]',
        '<!-- TODO: Company history item needs implementation -->',
        content
    )

    # STM Cost Calculator
    content = re.sub(
        r'\[stm_cost_calculator[^\]]*\]',
        '<!-- TODO: Cost calculator needs implementation -->',
        content
    )

    # VC TTA (Tabs/Accordion) sections
    content = re.sub(r'\[vc_tta_accordion[^\]]*\]', '<div class="accordion">', content)
    content = re.sub(r'\[/vc_tta_accordion\]', '</div>', content)

    content = re.sub(r'\[vc_tta_tabs[^\]]*\]', '<div class="tabs">', content)
    content = re.sub(r'\[/vc_tta_tabs\]', '</div>', content)

    def convert_tta_section(match):
        attrs = match.group(1) if match.group(1) else ''
        title_match = re.search(r'title="([^"]+)"', attrs)
        title = html.unescape(title_match.group(1)) if title_match else 'Section'
        return f'<div class="accordion-item"><h4 class="accordion-title">{title}</h4><div class="accordion-content">'

    content = re.sub(r'\[vc_tta_section([^\]]*)\]', convert_tta_section, content)
    content = re.sub(r'\[/vc_tta_section\]', '</div></div>', content)

    # WooCommerce shortcodes
    content = re.sub(
        r'\[woocommerce_cart[^\]]*\]',
        '<!-- TODO: Shopping cart needs implementation -->',
        content
    )
    content = re.sub(
        r'\[woocommerce_my_account[^\]]*\]',
        '<!-- TODO: Account page needs implementation -->',
        content
    )

    # Contact Form 7
    content = re.sub(
        r'\[contact-form-7[^\]]*\]',
        '<div class="contact-form-placeholder"><p>Contact form - please use the contact details provided.</p></div>',
        content
    )

    # WP Search
    content = re.sub(r'\[vc_wp_search[^\]]*\]', '', content)

    # VC Gallery
    content = re.sub(r'\[vc_gallery[^\]]*\]', '<div class="gallery"><!-- Gallery images --></div>', content)

    # VC Video
    def convert_video(match):
        attrs = match.group(1) if match.group(1) else ''
        link_match = re.search(r'link="([^"]+)"', attrs)
        link = link_match.group(1) if link_match else ''
        if 'youtube' in link or 'youtu.be' in link:
            return f'<div class="video-embed"><a href="{link}" target="_blank">Watch Video</a></div>'
        return '<div class="video-embed"><!-- Video content --></div>'

    content = re.sub(r'\[vc_video([^\]]*)\]', convert_video, content)

    # VC Icon
    content = re.sub(r'\[vc_icon[^\]]*\]', '', content)

    # Remove any remaining unknown shortcodes (preserve content between them if any)
    content = re.sub(r'\[\/?[\w_-]+[^\]]*\]', '', content)

    return content

def convert_internal_links(content: str, base_url: str) -> str:
    """Convert internal WordPress links to new site structure."""
    if not content:
        return ''

    # Convert absolute URLs to relative paths
    content = re.sub(
        rf'{re.escape(base_url)}/([\d]{{4}})/([\d]{{2}})/([\d]{{2}})/([^/"]+)/?',
        r'/blog/\4/',
        content
    )

    # Convert page links
    content = re.sub(
        rf'{re.escape(base_url)}/([^"\'>\s]+)/?',
        r'/\1/',
        content
    )

    # Clean up double slashes
    content = re.sub(r'([^:])//', r'\1/', content)

    return content

def generate_frontmatter(item: dict, item_type: str = 'post') -> str:
    """Generate YAML frontmatter for MDX file."""
    fm = ['---']

    # Title (escape quotes)
    title = item.get('title', 'Untitled').replace('"', '\\"')
    fm.append(f'title: "{title}"')

    # Permalink (use 'permalink' instead of 'slug' since Astro reserves 'slug')
    slug = item.get('slug', slugify(title))
    fm.append(f'permalink: "{slug}"')

    # Date
    date = item.get('date', datetime.now().isoformat())
    fm.append(f'date: "{date}"')

    # Modified date
    modified = item.get('modified')
    if modified:
        fm.append(f'updated: "{modified}"')

    # Type
    fm.append(f'type: "{item_type}"')

    # Status
    fm.append(f'status: "{item.get("status", "publish")}"')

    # Excerpt
    excerpt = item.get('excerpt', '').replace('"', '\\"').replace('\n', ' ')[:200]
    if excerpt:
        fm.append(f'excerpt: "{excerpt}"')

    # Categories (for posts)
    categories = item.get('categories', [])
    if categories:
        cat_list = ', '.join(f'"{c["slug"]}"' for c in categories)
        fm.append(f'categories: [{cat_list}]')

    # Tags (for posts)
    tags = item.get('tags', [])
    if tags:
        tag_list = ', '.join(f'"{t["slug"]}"' for t in tags)
        fm.append(f'tags: [{tag_list}]')

    # Featured image
    featured = item.get('featuredImage')
    if featured:
        fm.append(f'featuredImage: "{featured.get("url", "")}"')
        alt = featured.get('alt', '').replace('"', '\\"')
        fm.append(f'featuredImageAlt: "{alt}"')

    # Author
    author_id = item.get('authorId')
    if author_id:
        fm.append(f'authorId: {author_id}')

    # Menu order (for pages)
    if item_type == 'page':
        menu_order = item.get('menuOrder', 0)
        fm.append(f'menuOrder: {menu_order}')

        parent_id = item.get('parentId', 0)
        fm.append(f'parentId: {parent_id}')

        full_path = item.get('fullPath', slug)
        fm.append(f'path: "{full_path}"')

    # Reading time (for posts)
    if item_type == 'post':
        content = item.get('content', '')
        reading_time = estimate_reading_time(content)
        fm.append(f'readingTime: {reading_time}')

    # Canonical URL
    fm.append(f'canonicalUrl: "/{slug}/"')

    fm.append('---')
    return '\n'.join(fm)

def transform_content(content: str, base_url: str) -> str:
    """Transform WordPress content to clean MDX-compatible HTML."""
    if not content:
        return ''

    # First convert Gutenberg blocks
    content = convert_gutenberg_blocks(content)

    # Then convert Visual Composer shortcodes
    content = convert_vc_shortcodes(content)

    # Convert internal links
    content = convert_internal_links(content, base_url)

    # Clean up HTML
    content = clean_html(content)

    # Final cleanup
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content.strip()

def save_mdx(content: str, frontmatter: str, output_path: Path):
    """Save MDX file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
        f.write('\n\n')
        f.write(content)

def transform_posts():
    """Transform all posts to MDX."""
    print("\n[TRANSFORM] Posts...")
    posts = load_json('posts.json')
    site = load_json('site.json')
    base_url = site.get('baseUrl', '')

    for post in posts:
        slug = post.get('slug', slugify(post.get('title', 'untitled')))
        frontmatter = generate_frontmatter(post, 'post')
        content = transform_content(post.get('content', ''), base_url)

        output_path = POSTS_DIR / f'{slug}.mdx'
        save_mdx(content, frontmatter, output_path)

    print(f"  Transformed {len(posts)} posts")
    return posts

def transform_pages():
    """Transform all pages to MDX."""
    print("\n[TRANSFORM] Pages...")
    pages = load_json('pages.json')
    site = load_json('site.json')
    base_url = site.get('baseUrl', '')

    # Build hierarchy info
    page_hierarchy = load_json('page-hierarchy.json')

    for page in pages:
        slug = page.get('slug', slugify(page.get('title', 'untitled')))

        # Get full path from hierarchy
        if str(page['id']) in page_hierarchy:
            page['fullPath'] = page_hierarchy[str(page['id'])]['fullPath']
        else:
            page['fullPath'] = slug

        frontmatter = generate_frontmatter(page, 'page')
        content = transform_content(page.get('content', ''), base_url)

        # Use full path for nested pages
        output_path = PAGES_DIR / f'{slug}.mdx'
        save_mdx(content, frontmatter, output_path)

    print(f"  Transformed {len(pages)} pages")
    return pages

def transform_custom_types():
    """Transform custom post types to MDX."""
    print("\n[TRANSFORM] Custom post types...")

    try:
        custom_types = load_json('custom-post-types.json')
    except:
        print("  No custom post types found")
        return {}

    site = load_json('site.json')
    base_url = site.get('baseUrl', '')

    for type_name, items in custom_types.items():
        # Skip certain types that don't need pages
        if type_name in ['cost-calc', 'cost-calc-templates', 'cost-calc-categories',
                         'wpcf7_contact_form', 'stm_vc_sidebar', 'elementor_library']:
            continue

        type_dir = OUTPUT_DIR / type_name.replace('stm_', '')

        for item in items:
            slug = item.get('slug', slugify(item.get('title', 'untitled')))
            frontmatter = generate_frontmatter(item, type_name)
            content = transform_content(item.get('content', ''), base_url)

            output_path = type_dir / f'{slug}.mdx'
            save_mdx(content, frontmatter, output_path)

        print(f"  Transformed {len(items)} {type_name} items")

    return custom_types

def generate_media_manifest():
    """Generate manifest of all media files."""
    print("\n[TRANSFORM] Media manifest...")
    media = load_json('media.json')

    manifest = []
    for item in media:
        manifest.append({
            'id': item['id'],
            'url': item['url'],
            'file': item.get('file', ''),
            'mimeType': item['mimeType'],
            'title': item['title'],
            'alt': item.get('alt', '')
        })

    output_path = OUTPUT_DIR / 'media-manifest.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"  Generated manifest with {len(manifest)} media items")
    return manifest

def generate_report():
    """Generate transformation report."""
    print("\n[REPORT] Generating transformation report...")

    report = {
        'unknownShortcodes': list(unknown_shortcodes),
        'conversionIssues': conversion_issues,
        'timestamp': datetime.now().isoformat()
    }

    output_path = OUTPUT_DIR / 'transform-report.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"  Unknown shortcodes found: {len(unknown_shortcodes)}")
    if unknown_shortcodes:
        for sc in sorted(unknown_shortcodes):
            print(f"    - {sc}")

    return report

def main():
    """Main transform function."""
    print("=" * 60)
    print("WordPress Content Transform")
    print("=" * 60)

    # Create output directories
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    PAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Transform content
    posts = transform_posts()
    pages = transform_pages()
    custom_types = transform_custom_types()
    media = generate_media_manifest()
    report = generate_report()

    # Summary
    print("\n" + "=" * 60)
    print("TRANSFORM SUMMARY")
    print("=" * 60)
    print(f"  Posts transformed: {len(posts)}")
    print(f"  Pages transformed: {len(pages)}")
    print(f"  Custom types: {len(custom_types)} types")
    print(f"  Media items: {len(media)}")
    print(f"  Unknown shortcodes: {len(unknown_shortcodes)}")
    print(f"\n  Output directory: {OUTPUT_DIR}")

    print("\n[DONE] Transform complete!")

if __name__ == '__main__':
    main()
