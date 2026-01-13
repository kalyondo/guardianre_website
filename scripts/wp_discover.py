#!/usr/bin/env python3
"""
WordPress Database Discovery Script
Connects to MySQL, detects table prefix, and analyzes WordPress site structure.
"""

import os
import sys
import json
import re
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from collections import defaultdict

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4',
    'use_unicode': True
}

def connect_db():
    """Establish database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            print(f"[OK] Connected to MySQL database: {DB_CONFIG['database']}")
            return conn
    except Error as e:
        print(f"[ERROR] Failed to connect: {e}")
        sys.exit(1)

def get_all_tables(cursor):
    """Get all tables in the database."""
    cursor.execute("SHOW TABLES")
    return [row[0] for row in cursor.fetchall()]

def detect_prefix(tables):
    """Detect WordPress table prefix by looking for common WP tables."""
    wp_core_tables = ['posts', 'postmeta', 'options', 'terms', 'term_taxonomy',
                      'term_relationships', 'users', 'usermeta', 'comments', 'commentmeta']

    prefixes = defaultdict(int)

    for table in tables:
        for core_table in wp_core_tables:
            if table.endswith('_' + core_table) or table.endswith(core_table):
                # Extract prefix
                if table.endswith('_' + core_table):
                    prefix = table[:-len(core_table)-1] + '_'
                else:
                    prefix = ''
                prefixes[prefix] += 1

    if prefixes:
        # Return the most common prefix
        return max(prefixes.items(), key=lambda x: x[1])[0]
    return None

def get_option(cursor, prefix, option_name):
    """Get a single option from wp_options."""
    try:
        cursor.execute(f"SELECT option_value FROM {prefix}options WHERE option_name = %s", (option_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except:
        return None

def get_site_settings(cursor, prefix):
    """Retrieve key site settings from wp_options."""
    settings = {}
    option_names = [
        'siteurl', 'home', 'blogname', 'blogdescription',
        'permalink_structure', 'timezone_string', 'gmt_offset',
        'date_format', 'time_format', 'posts_per_page',
        'default_category', 'template', 'stylesheet',
        'WPLANG', 'blog_charset'
    ]

    for opt in option_names:
        value = get_option(cursor, prefix, opt)
        if value:
            settings[opt] = value

    return settings

def count_content(cursor, prefix):
    """Count posts, pages, and other content types."""
    counts = {}

    # Count by post_type and post_status
    cursor.execute(f"""
        SELECT post_type, post_status, COUNT(*) as count
        FROM {prefix}posts
        GROUP BY post_type, post_status
        ORDER BY count DESC
    """)

    post_counts = cursor.fetchall()
    counts['by_type_status'] = [(row[0], row[1], row[2]) for row in post_counts]

    # Published posts
    cursor.execute(f"""
        SELECT COUNT(*) FROM {prefix}posts
        WHERE post_type = 'post' AND post_status = 'publish'
    """)
    counts['published_posts'] = cursor.fetchone()[0]

    # Published pages
    cursor.execute(f"""
        SELECT COUNT(*) FROM {prefix}posts
        WHERE post_type = 'page' AND post_status = 'publish'
    """)
    counts['published_pages'] = cursor.fetchone()[0]

    # Attachments
    cursor.execute(f"""
        SELECT COUNT(*) FROM {prefix}posts
        WHERE post_type = 'attachment'
    """)
    counts['attachments'] = cursor.fetchone()[0]

    # Nav menu items
    cursor.execute(f"""
        SELECT COUNT(*) FROM {prefix}posts
        WHERE post_type = 'nav_menu_item'
    """)
    counts['nav_menu_items'] = cursor.fetchone()[0]

    # Categories
    cursor.execute(f"""
        SELECT COUNT(*) FROM {prefix}term_taxonomy
        WHERE taxonomy = 'category'
    """)
    counts['categories'] = cursor.fetchone()[0]

    # Tags
    cursor.execute(f"""
        SELECT COUNT(*) FROM {prefix}term_taxonomy
        WHERE taxonomy = 'post_tag'
    """)
    counts['tags'] = cursor.fetchone()[0]

    # Menus
    cursor.execute(f"""
        SELECT COUNT(*) FROM {prefix}term_taxonomy
        WHERE taxonomy = 'nav_menu'
    """)
    counts['menus'] = cursor.fetchone()[0]

    return counts

def list_taxonomies(cursor, prefix):
    """List all taxonomy types and their counts."""
    cursor.execute(f"""
        SELECT taxonomy, COUNT(*) as count
        FROM {prefix}term_taxonomy
        GROUP BY taxonomy
        ORDER BY count DESC
    """)
    return cursor.fetchall()

def list_post_types(cursor, prefix):
    """List all post types in use."""
    cursor.execute(f"""
        SELECT DISTINCT post_type
        FROM {prefix}posts
    """)
    return [row[0] for row in cursor.fetchall()]

def check_seo_plugins(cursor, prefix):
    """Detect SEO plugin data in postmeta."""
    seo_indicators = {}

    # Yoast SEO
    cursor.execute(f"""
        SELECT COUNT(*) FROM {prefix}postmeta
        WHERE meta_key LIKE '_yoast_wpseo_%'
    """)
    yoast_count = cursor.fetchone()[0]
    if yoast_count > 0:
        seo_indicators['yoast'] = yoast_count

    # RankMath
    cursor.execute(f"""
        SELECT COUNT(*) FROM {prefix}postmeta
        WHERE meta_key LIKE 'rank_math_%'
    """)
    rankmath_count = cursor.fetchone()[0]
    if rankmath_count > 0:
        seo_indicators['rankmath'] = rankmath_count

    # All in One SEO
    cursor.execute(f"""
        SELECT COUNT(*) FROM {prefix}postmeta
        WHERE meta_key LIKE '_aioseo_%' OR meta_key LIKE '_aioseop_%'
    """)
    aioseo_count = cursor.fetchone()[0]
    if aioseo_count > 0:
        seo_indicators['aioseo'] = aioseo_count

    # SEOPress
    cursor.execute(f"""
        SELECT COUNT(*) FROM {prefix}postmeta
        WHERE meta_key LIKE '_seopress_%'
    """)
    seopress_count = cursor.fetchone()[0]
    if seopress_count > 0:
        seo_indicators['seopress'] = seopress_count

    return seo_indicators

def list_active_plugins(cursor, prefix):
    """Try to get active plugins from options."""
    try:
        import phpserialize
        plugins_option = get_option(cursor, prefix, 'active_plugins')
        if plugins_option:
            plugins = phpserialize.loads(plugins_option.encode())
            return [p.decode() if isinstance(p, bytes) else p for p in plugins.values()]
    except:
        pass

    # Alternative: just return the raw string
    return get_option(cursor, prefix, 'active_plugins')

def get_menu_structure(cursor, prefix):
    """Get all navigation menus and their items."""
    menus = []

    # Get all nav_menu terms
    cursor.execute(f"""
        SELECT t.term_id, t.name, t.slug, tt.count
        FROM {prefix}terms t
        JOIN {prefix}term_taxonomy tt ON t.term_id = tt.term_id
        WHERE tt.taxonomy = 'nav_menu'
    """)

    for row in cursor.fetchall():
        menu = {
            'id': row[0],
            'name': row[1],
            'slug': row[2],
            'item_count': row[3]
        }
        menus.append(menu)

    return menus

def get_sample_posts(cursor, prefix, limit=5):
    """Get sample posts to understand content structure."""
    cursor.execute(f"""
        SELECT ID, post_title, post_name, post_date, post_status
        FROM {prefix}posts
        WHERE post_type = 'post' AND post_status = 'publish'
        ORDER BY post_date DESC
        LIMIT {limit}
    """)
    return cursor.fetchall()

def get_sample_pages(cursor, prefix, limit=5):
    """Get sample pages."""
    cursor.execute(f"""
        SELECT ID, post_title, post_name, post_parent, post_status
        FROM {prefix}posts
        WHERE post_type = 'page' AND post_status = 'publish'
        ORDER BY menu_order ASC, post_title ASC
        LIMIT {limit}
    """)
    return cursor.fetchall()

def analyze_content_format(cursor, prefix):
    """Analyze content format (Gutenberg blocks, shortcodes, etc.)."""
    analysis = {
        'gutenberg_blocks': 0,
        'shortcodes': set(),
        'classic_editor': 0
    }

    cursor.execute(f"""
        SELECT ID, post_content
        FROM {prefix}posts
        WHERE post_type IN ('post', 'page')
        AND post_status = 'publish'
    """)

    shortcode_pattern = re.compile(r'\[(\w+)[^\]]*\]')

    for row in cursor.fetchall():
        content = row[1] or ''

        # Check for Gutenberg blocks
        if '<!-- wp:' in content:
            analysis['gutenberg_blocks'] += 1
        else:
            analysis['classic_editor'] += 1

        # Find shortcodes
        shortcodes = shortcode_pattern.findall(content)
        analysis['shortcodes'].update(shortcodes)

    analysis['shortcodes'] = list(analysis['shortcodes'])
    return analysis

def main():
    """Main discovery function."""
    print("=" * 60)
    print("WordPress Database Discovery")
    print("=" * 60)
    print()

    # Connect to database
    conn = connect_db()
    cursor = conn.cursor()

    # Get all tables
    tables = get_all_tables(cursor)
    print(f"\n[INFO] Total tables in database: {len(tables)}")

    # Detect prefix
    prefix = detect_prefix(tables)
    if not prefix:
        print("[ERROR] Could not detect WordPress table prefix!")
        print("Tables found:", tables)
        sys.exit(1)

    print(f"\n[DETECTED] Table prefix: '{prefix}'")

    # Verify core tables exist
    core_tables = ['posts', 'postmeta', 'options', 'terms', 'term_taxonomy', 'term_relationships']
    missing = [t for t in core_tables if f"{prefix}{t}" not in tables]
    if missing:
        print(f"[WARNING] Missing core tables: {missing}")
    else:
        print("[OK] All core WordPress tables found")

    # Get site settings
    print("\n" + "-" * 40)
    print("SITE SETTINGS")
    print("-" * 40)
    settings = get_site_settings(cursor, prefix)
    for key, value in settings.items():
        # Truncate long values
        display_value = value[:80] + '...' if len(str(value)) > 80 else value
        print(f"  {key}: {display_value}")

    # Content counts
    print("\n" + "-" * 40)
    print("CONTENT COUNTS")
    print("-" * 40)
    counts = count_content(cursor, prefix)
    print(f"  Published Posts: {counts['published_posts']}")
    print(f"  Published Pages: {counts['published_pages']}")
    print(f"  Attachments: {counts['attachments']}")
    print(f"  Categories: {counts['categories']}")
    print(f"  Tags: {counts['tags']}")
    print(f"  Navigation Menus: {counts['menus']}")
    print(f"  Nav Menu Items: {counts['nav_menu_items']}")

    print("\n  Content by type/status:")
    for post_type, status, count in counts['by_type_status'][:15]:
        print(f"    {post_type}/{status}: {count}")

    # Taxonomies
    print("\n" + "-" * 40)
    print("TAXONOMIES")
    print("-" * 40)
    taxonomies = list_taxonomies(cursor, prefix)
    for tax, count in taxonomies:
        print(f"  {tax}: {count}")

    # Post types
    print("\n" + "-" * 40)
    print("POST TYPES")
    print("-" * 40)
    post_types = list_post_types(cursor, prefix)
    for pt in post_types:
        print(f"  - {pt}")

    # SEO plugins
    print("\n" + "-" * 40)
    print("SEO PLUGIN DATA")
    print("-" * 40)
    seo_data = check_seo_plugins(cursor, prefix)
    if seo_data:
        for plugin, count in seo_data.items():
            print(f"  {plugin}: {count} meta entries")
    else:
        print("  No SEO plugin data detected")

    # Menus
    print("\n" + "-" * 40)
    print("NAVIGATION MENUS")
    print("-" * 40)
    menus = get_menu_structure(cursor, prefix)
    if menus:
        for menu in menus:
            print(f"  - {menu['name']} (slug: {menu['slug']}, items: {menu['item_count']})")
    else:
        print("  No navigation menus found")

    # Content format analysis
    print("\n" + "-" * 40)
    print("CONTENT FORMAT ANALYSIS")
    print("-" * 40)
    content_analysis = analyze_content_format(cursor, prefix)
    print(f"  Gutenberg block posts: {content_analysis['gutenberg_blocks']}")
    print(f"  Classic editor posts: {content_analysis['classic_editor']}")
    if content_analysis['shortcodes']:
        print(f"  Shortcodes found: {', '.join(content_analysis['shortcodes'][:20])}")
        if len(content_analysis['shortcodes']) > 20:
            print(f"    ... and {len(content_analysis['shortcodes']) - 20} more")

    # Sample posts
    print("\n" + "-" * 40)
    print("SAMPLE PUBLISHED POSTS")
    print("-" * 40)
    sample_posts = get_sample_posts(cursor, prefix)
    for post in sample_posts:
        print(f"  [{post[0]}] {post[1][:50]} -> /{post[2]}/")

    # Sample pages
    print("\n" + "-" * 40)
    print("SAMPLE PUBLISHED PAGES")
    print("-" * 40)
    sample_pages = get_sample_pages(cursor, prefix)
    for page in sample_pages:
        parent_note = f" (parent: {page[3]})" if page[3] > 0 else ""
        print(f"  [{page[0]}] {page[1][:50]} -> /{page[2]}/{parent_note}")

    # Save discovery results to JSON
    discovery_results = {
        'prefix': prefix,
        'settings': settings,
        'counts': {
            'published_posts': counts['published_posts'],
            'published_pages': counts['published_pages'],
            'attachments': counts['attachments'],
            'categories': counts['categories'],
            'tags': counts['tags'],
            'menus': counts['menus']
        },
        'taxonomies': dict(taxonomies),
        'post_types': post_types,
        'seo_plugins': seo_data,
        'menus': menus,
        'content_format': content_analysis,
        'shortcodes': content_analysis['shortcodes']
    }

    output_path = Path(__file__).parent.parent / 'content' / '_raw' / 'discovery.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(discovery_results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n[SAVED] Discovery results to: {output_path}")

    # Summary
    print("\n" + "=" * 60)
    print("DISCOVERY SUMMARY")
    print("=" * 60)
    print(f"  Database: {DB_CONFIG['database']}")
    print(f"  Table Prefix: {prefix}")
    print(f"  Site Name: {settings.get('blogname', 'Unknown')}")
    print(f"  Site URL: {settings.get('siteurl', 'Unknown')}")
    print(f"  Permalink Structure: {settings.get('permalink_structure', 'Unknown')}")
    print(f"  Theme: {settings.get('template', 'Unknown')}")
    print(f"  Total Content: {counts['published_posts']} posts, {counts['published_pages']} pages")
    print(f"  SEO Data: {list(seo_data.keys()) if seo_data else 'None'}")
    print()

    cursor.close()
    conn.close()

    return discovery_results

if __name__ == '__main__':
    main()
