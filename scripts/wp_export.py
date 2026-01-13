#!/usr/bin/env python3
"""
WordPress Database Export Script
Exports all content from WordPress database to JSON files.
"""

import os
import sys
import json
import re
import html
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

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

OUTPUT_DIR = Path(__file__).parent.parent / 'content' / '_raw'

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

def get_option(cursor, prefix, option_name):
    """Get a single option from wp_options."""
    try:
        cursor.execute(f"SELECT option_value FROM {prefix}options WHERE option_name = %s", (option_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except:
        return None

def export_site_settings(cursor, prefix):
    """Export site-level settings."""
    print("\n[EXPORT] Site settings...")
    settings = {}
    option_names = [
        'siteurl', 'home', 'blogname', 'blogdescription',
        'permalink_structure', 'timezone_string', 'gmt_offset',
        'date_format', 'time_format', 'posts_per_page',
        'default_category', 'template', 'stylesheet',
        'WPLANG', 'blog_charset', 'admin_email'
    ]

    for opt in option_names:
        value = get_option(cursor, prefix, opt)
        if value:
            settings[opt] = value

    return {
        'name': settings.get('blogname', 'Site'),
        'description': settings.get('blogdescription', ''),
        'baseUrl': settings.get('siteurl', settings.get('home', '')),
        'homeUrl': settings.get('home', settings.get('siteurl', '')),
        'timezone': settings.get('timezone_string', f"UTC+{settings.get('gmt_offset', 0)}"),
        'dateFormat': settings.get('date_format', 'F j, Y'),
        'timeFormat': settings.get('time_format', 'g:i a'),
        'postsPerPage': int(settings.get('posts_per_page', 10)),
        'permalinkStructure': settings.get('permalink_structure', '/%postname%/'),
        'charset': settings.get('blog_charset', 'UTF-8'),
        'language': settings.get('WPLANG', 'en_US'),
        'theme': settings.get('template', 'default'),
        'adminEmail': settings.get('admin_email', '')
    }

def get_post_meta(cursor, prefix, post_id):
    """Get all meta for a post."""
    cursor.execute(f"""
        SELECT meta_key, meta_value
        FROM {prefix}postmeta
        WHERE post_id = %s
    """, (post_id,))

    meta = {}
    for row in cursor.fetchall():
        key, value = row
        # Skip internal/revision meta
        if key.startswith('_edit_') or key == '_wp_old_slug':
            continue
        # Handle multiple values for same key
        if key in meta:
            if isinstance(meta[key], list):
                meta[key].append(value)
            else:
                meta[key] = [meta[key], value]
        else:
            meta[key] = value

    return meta

def get_post_terms(cursor, prefix, post_id, taxonomy):
    """Get terms for a post in a specific taxonomy."""
    cursor.execute(f"""
        SELECT t.term_id, t.name, t.slug
        FROM {prefix}terms t
        JOIN {prefix}term_taxonomy tt ON t.term_id = tt.term_id
        JOIN {prefix}term_relationships tr ON tt.term_taxonomy_id = tr.term_taxonomy_id
        WHERE tr.object_id = %s AND tt.taxonomy = %s
    """, (post_id, taxonomy))

    return [{'id': row[0], 'name': row[1], 'slug': row[2]} for row in cursor.fetchall()]

def get_featured_image(cursor, prefix, post_id, meta):
    """Get featured image details."""
    thumbnail_id = meta.get('_thumbnail_id')
    if not thumbnail_id:
        return None

    try:
        thumbnail_id = int(thumbnail_id)
    except (ValueError, TypeError):
        return None

    cursor.execute(f"""
        SELECT ID, guid, post_title, post_excerpt
        FROM {prefix}posts
        WHERE ID = %s AND post_type = 'attachment'
    """, (thumbnail_id,))

    result = cursor.fetchone()
    if not result:
        return None

    # Get attachment metadata
    cursor.execute(f"""
        SELECT meta_value FROM {prefix}postmeta
        WHERE post_id = %s AND meta_key = '_wp_attached_file'
    """, (thumbnail_id,))
    file_result = cursor.fetchone()

    return {
        'id': result[0],
        'url': result[1],
        'title': result[2] or '',
        'alt': result[3] or '',
        'file': file_result[0] if file_result else ''
    }

def export_posts(cursor, prefix):
    """Export all published posts."""
    print("\n[EXPORT] Posts...")

    cursor.execute(f"""
        SELECT
            ID, post_author, post_date, post_date_gmt,
            post_content, post_title, post_excerpt,
            post_status, post_name, post_modified, post_modified_gmt,
            post_parent, guid, menu_order, post_type
        FROM {prefix}posts
        WHERE post_type = 'post' AND post_status = 'publish'
        ORDER BY post_date DESC
    """)

    posts = []
    for row in cursor.fetchall():
        post_id = row[0]
        meta = get_post_meta(cursor, prefix, post_id)
        categories = get_post_terms(cursor, prefix, post_id, 'category')
        tags = get_post_terms(cursor, prefix, post_id, 'post_tag')
        featured_image = get_featured_image(cursor, prefix, post_id, meta)

        post = {
            'id': post_id,
            'authorId': row[1],
            'date': row[2].isoformat() if row[2] else None,
            'dateGmt': row[3].isoformat() if row[3] else None,
            'content': row[4] or '',
            'title': row[5] or '',
            'excerpt': row[6] or '',
            'status': row[7],
            'slug': row[8] or '',
            'modified': row[9].isoformat() if row[9] else None,
            'modifiedGmt': row[10].isoformat() if row[10] else None,
            'parentId': row[11],
            'guid': row[12],
            'menuOrder': row[13],
            'type': row[14],
            'categories': categories,
            'tags': tags,
            'featuredImage': featured_image,
            'meta': meta
        }
        posts.append(post)

    print(f"  Exported {len(posts)} posts")
    return posts

def export_pages(cursor, prefix):
    """Export all published pages."""
    print("\n[EXPORT] Pages...")

    cursor.execute(f"""
        SELECT
            ID, post_author, post_date, post_date_gmt,
            post_content, post_title, post_excerpt,
            post_status, post_name, post_modified, post_modified_gmt,
            post_parent, guid, menu_order, post_type
        FROM {prefix}posts
        WHERE post_type = 'page' AND post_status = 'publish'
        ORDER BY menu_order ASC, post_title ASC
    """)

    pages = []
    for row in cursor.fetchall():
        page_id = row[0]
        meta = get_post_meta(cursor, prefix, page_id)
        featured_image = get_featured_image(cursor, prefix, page_id, meta)

        page = {
            'id': page_id,
            'authorId': row[1],
            'date': row[2].isoformat() if row[2] else None,
            'dateGmt': row[3].isoformat() if row[3] else None,
            'content': row[4] or '',
            'title': row[5] or '',
            'excerpt': row[6] or '',
            'status': row[7],
            'slug': row[8] or '',
            'modified': row[9].isoformat() if row[9] else None,
            'modifiedGmt': row[10].isoformat() if row[10] else None,
            'parentId': row[11],
            'guid': row[12],
            'menuOrder': row[13],
            'type': row[14],
            'featuredImage': featured_image,
            'meta': meta
        }
        pages.append(page)

    print(f"  Exported {len(pages)} pages")
    return pages

def export_custom_post_types(cursor, prefix):
    """Export custom post types (testimonials, portfolio, works, etc.)."""
    print("\n[EXPORT] Custom post types...")

    # Get list of custom post types (exclude built-in ones)
    cursor.execute(f"""
        SELECT DISTINCT post_type
        FROM {prefix}posts
        WHERE post_type NOT IN (
            'post', 'page', 'attachment', 'revision',
            'nav_menu_item', 'wp_navigation', 'wp_template',
            'wp_template_part', 'wp_global_styles'
        )
        AND post_status = 'publish'
    """)

    custom_types = [row[0] for row in cursor.fetchall()]
    all_custom = {}

    for post_type in custom_types:
        cursor.execute(f"""
            SELECT
                ID, post_author, post_date, post_date_gmt,
                post_content, post_title, post_excerpt,
                post_status, post_name, post_modified, post_modified_gmt,
                post_parent, guid, menu_order, post_type
            FROM {prefix}posts
            WHERE post_type = %s AND post_status = 'publish'
            ORDER BY menu_order ASC, post_date DESC
        """, (post_type,))

        items = []
        for row in cursor.fetchall():
            item_id = row[0]
            meta = get_post_meta(cursor, prefix, item_id)
            featured_image = get_featured_image(cursor, prefix, item_id, meta)

            # Get custom taxonomies for this post type
            cursor.execute(f"""
                SELECT DISTINCT tt.taxonomy
                FROM {prefix}term_taxonomy tt
                JOIN {prefix}term_relationships tr ON tt.term_taxonomy_id = tr.term_taxonomy_id
                WHERE tr.object_id = %s
            """, (item_id,))
            taxonomies = {}
            for tax_row in cursor.fetchall():
                tax_name = tax_row[0]
                terms = get_post_terms(cursor, prefix, item_id, tax_name)
                if terms:
                    taxonomies[tax_name] = terms

            item = {
                'id': item_id,
                'authorId': row[1],
                'date': row[2].isoformat() if row[2] else None,
                'dateGmt': row[3].isoformat() if row[3] else None,
                'content': row[4] or '',
                'title': row[5] or '',
                'excerpt': row[6] or '',
                'status': row[7],
                'slug': row[8] or '',
                'modified': row[9].isoformat() if row[9] else None,
                'modifiedGmt': row[10].isoformat() if row[10] else None,
                'parentId': row[11],
                'guid': row[12],
                'menuOrder': row[13],
                'type': row[14],
                'featuredImage': featured_image,
                'taxonomies': taxonomies,
                'meta': meta
            }
            items.append(item)

        if items:
            all_custom[post_type] = items
            print(f"  Exported {len(items)} {post_type} items")

    return all_custom

def export_taxonomies(cursor, prefix):
    """Export all taxonomies (categories, tags, custom)."""
    print("\n[EXPORT] Taxonomies...")

    # Get all taxonomy types
    cursor.execute(f"""
        SELECT DISTINCT taxonomy FROM {prefix}term_taxonomy
    """)
    taxonomy_types = [row[0] for row in cursor.fetchall()]

    taxonomies = {}

    for tax_type in taxonomy_types:
        cursor.execute(f"""
            SELECT t.term_id, t.name, t.slug, tt.description, tt.count, tt.parent
            FROM {prefix}terms t
            JOIN {prefix}term_taxonomy tt ON t.term_id = tt.term_id
            WHERE tt.taxonomy = %s
            ORDER BY t.name ASC
        """, (tax_type,))

        terms = []
        for row in cursor.fetchall():
            terms.append({
                'id': row[0],
                'name': row[1],
                'slug': row[2],
                'description': row[3] or '',
                'count': row[4],
                'parentId': row[5]
            })

        if terms:
            taxonomies[tax_type] = terms
            print(f"  Exported {len(terms)} {tax_type} terms")

    return taxonomies

def export_menus(cursor, prefix):
    """Export navigation menus with their items."""
    print("\n[EXPORT] Navigation menus...")

    # Get all nav menus
    cursor.execute(f"""
        SELECT t.term_id, t.name, t.slug
        FROM {prefix}terms t
        JOIN {prefix}term_taxonomy tt ON t.term_id = tt.term_id
        WHERE tt.taxonomy = 'nav_menu'
    """)

    menus = []
    for row in cursor.fetchall():
        menu_id = row[0]
        menu = {
            'id': menu_id,
            'name': row[1],
            'slug': row[2],
            'items': []
        }

        # Get menu items for this menu
        cursor.execute(f"""
            SELECT p.ID, p.post_title, p.menu_order
            FROM {prefix}posts p
            JOIN {prefix}term_relationships tr ON p.ID = tr.object_id
            JOIN {prefix}term_taxonomy tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
            WHERE p.post_type = 'nav_menu_item'
            AND p.post_status = 'publish'
            AND tt.term_id = %s
            ORDER BY p.menu_order ASC
        """, (menu_id,))

        items_raw = cursor.fetchall()

        for item_row in items_raw:
            item_id = item_row[0]
            meta = get_post_meta(cursor, prefix, item_id)

            menu_item = {
                'id': item_id,
                'title': meta.get('_menu_item_title', item_row[1]) or item_row[1],
                'order': item_row[2],
                'type': meta.get('_menu_item_type', ''),  # custom, post_type, taxonomy
                'objectType': meta.get('_menu_item_object', ''),  # page, post, category, custom
                'objectId': meta.get('_menu_item_object_id', ''),
                'url': meta.get('_menu_item_url', ''),
                'parentId': int(meta.get('_menu_item_menu_item_parent', 0)),
                'target': meta.get('_menu_item_target', ''),
                'classes': meta.get('_menu_item_classes', []),
                'xfn': meta.get('_menu_item_xfn', ''),
                'description': meta.get('_menu_item_description', '')
            }

            # Resolve actual URL for linked objects
            if menu_item['type'] == 'post_type' and menu_item['objectId']:
                cursor.execute(f"""
                    SELECT post_name, post_type FROM {prefix}posts
                    WHERE ID = %s
                """, (menu_item['objectId'],))
                result = cursor.fetchone()
                if result:
                    menu_item['resolvedSlug'] = result[0]
                    menu_item['resolvedType'] = result[1]

            elif menu_item['type'] == 'taxonomy' and menu_item['objectId']:
                cursor.execute(f"""
                    SELECT t.slug FROM {prefix}terms t
                    JOIN {prefix}term_taxonomy tt ON t.term_id = tt.term_id
                    WHERE t.term_id = %s
                """, (menu_item['objectId'],))
                result = cursor.fetchone()
                if result:
                    menu_item['resolvedSlug'] = result[0]

            menu['items'].append(menu_item)

        menus.append(menu)
        print(f"  Menu '{menu['name']}': {len(menu['items'])} items")

    return menus

def export_media(cursor, prefix):
    """Export media/attachment information."""
    print("\n[EXPORT] Media attachments...")

    cursor.execute(f"""
        SELECT
            ID, post_title, post_name, post_mime_type,
            guid, post_date, post_excerpt
        FROM {prefix}posts
        WHERE post_type = 'attachment'
        ORDER BY post_date DESC
    """)

    media = []
    for row in cursor.fetchall():
        attachment_id = row[0]
        meta = get_post_meta(cursor, prefix, attachment_id)

        attachment = {
            'id': attachment_id,
            'title': row[1] or '',
            'slug': row[2] or '',
            'mimeType': row[3] or '',
            'url': row[4] or '',
            'date': row[5].isoformat() if row[5] else None,
            'alt': row[6] or '',
            'file': meta.get('_wp_attached_file', ''),
            'meta': meta.get('_wp_attachment_metadata', {})
        }
        media.append(attachment)

    print(f"  Exported {len(media)} attachments")
    return media

def export_users(cursor, prefix):
    """Export users (basic info only, no passwords)."""
    print("\n[EXPORT] Users...")

    cursor.execute(f"""
        SELECT ID, user_login, user_nicename, user_email, user_registered, display_name
        FROM {prefix}users
    """)

    users = []
    for row in cursor.fetchall():
        user_id = row[0]

        # Get user meta
        cursor.execute(f"""
            SELECT meta_key, meta_value
            FROM {prefix}usermeta
            WHERE user_id = %s
            AND meta_key IN ('first_name', 'last_name', 'nickname', 'description', 'wp_user_avatar')
        """, (user_id,))

        user_meta = dict(cursor.fetchall())

        user = {
            'id': user_id,
            'username': row[1],
            'nicename': row[2],
            'email': row[3],
            'registered': row[4].isoformat() if row[4] else None,
            'displayName': row[5] or '',
            'firstName': user_meta.get('first_name', ''),
            'lastName': user_meta.get('last_name', ''),
            'bio': user_meta.get('description', '')
        }
        users.append(user)

    print(f"  Exported {len(users)} users")
    return users

def export_seo_meta(cursor, prefix, posts, pages):
    """Export SEO metadata from various SEO plugins."""
    print("\n[EXPORT] SEO metadata...")

    seo_data = {}

    # Collect all post/page IDs
    all_ids = [p['id'] for p in posts] + [p['id'] for p in pages]

    # Check for Yoast SEO
    cursor.execute(f"""
        SELECT post_id, meta_key, meta_value
        FROM {prefix}postmeta
        WHERE post_id IN ({','.join(str(i) for i in all_ids)})
        AND (meta_key LIKE '_yoast_wpseo_%'
             OR meta_key LIKE 'rank_math_%'
             OR meta_key LIKE '_aioseo_%')
    """)

    for row in cursor.fetchall():
        post_id = row[0]
        key = row[1]
        value = row[2]

        if post_id not in seo_data:
            seo_data[post_id] = {}

        # Normalize key names
        if key.startswith('_yoast_wpseo_'):
            clean_key = key.replace('_yoast_wpseo_', '')
        elif key.startswith('rank_math_'):
            clean_key = key.replace('rank_math_', '')
        elif key.startswith('_aioseo_'):
            clean_key = key.replace('_aioseo_', '')
        else:
            clean_key = key

        seo_data[post_id][clean_key] = value

    print(f"  Exported SEO data for {len(seo_data)} items")
    return seo_data

def build_page_hierarchy(pages):
    """Build page hierarchy tree from flat list."""
    hierarchy = {}
    page_map = {p['id']: p for p in pages}

    def get_path(page):
        """Get full path including parent slugs."""
        path = [page['slug']]
        current = page
        while current['parentId'] > 0 and current['parentId'] in page_map:
            parent = page_map[current['parentId']]
            path.insert(0, parent['slug'])
            current = parent
        return '/'.join(path)

    for page in pages:
        page['fullPath'] = get_path(page)
        hierarchy[page['id']] = {
            'slug': page['slug'],
            'fullPath': page['fullPath'],
            'parentId': page['parentId'],
            'title': page['title']
        }

    return hierarchy

def create_redirects(site_settings, posts, pages):
    """Create redirect mappings based on permalink structure."""
    redirects = []
    permalink_structure = site_settings.get('permalinkStructure', '/%postname%/')

    # For posts with date-based permalinks
    if '/%year%/' in permalink_structure:
        for post in posts:
            if post['date']:
                date_obj = datetime.fromisoformat(post['date'])
                old_path = permalink_structure.replace('%year%', str(date_obj.year))
                old_path = old_path.replace('%monthnum%', str(date_obj.month).zfill(2))
                old_path = old_path.replace('%day%', str(date_obj.day).zfill(2))
                old_path = old_path.replace('%postname%', post['slug'])

                # New path is simpler
                new_path = f"/blog/{post['slug']}"

                if old_path != new_path:
                    redirects.append({
                        'from': old_path,
                        'to': new_path,
                        'status': 301,
                        'type': 'post'
                    })

    return redirects

def save_json(data, filename):
    """Save data to JSON file."""
    output_path = OUTPUT_DIR / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    print(f"  [SAVED] {output_path}")

def main():
    """Main export function."""
    print("=" * 60)
    print("WordPress Database Export")
    print("=" * 60)

    # Connect to database
    conn = connect_db()
    cursor = conn.cursor()

    # Use detected prefix
    prefix = 'wp_'

    # Export all content
    site_settings = export_site_settings(cursor, prefix)
    save_json(site_settings, 'site.json')

    posts = export_posts(cursor, prefix)
    save_json(posts, 'posts.json')

    pages = export_pages(cursor, prefix)
    save_json(pages, 'pages.json')

    # Build page hierarchy
    page_hierarchy = build_page_hierarchy(pages)
    save_json(page_hierarchy, 'page-hierarchy.json')

    custom_post_types = export_custom_post_types(cursor, prefix)
    save_json(custom_post_types, 'custom-post-types.json')

    taxonomies = export_taxonomies(cursor, prefix)
    save_json(taxonomies, 'taxonomies.json')

    menus = export_menus(cursor, prefix)
    save_json(menus, 'menus.json')

    media = export_media(cursor, prefix)
    save_json(media, 'media.json')

    users = export_users(cursor, prefix)
    save_json(users, 'users.json')

    seo_data = export_seo_meta(cursor, prefix, posts, pages)
    save_json(seo_data, 'seo.json')

    # Create redirects
    redirects = create_redirects(site_settings, posts, pages)
    save_json(redirects, 'redirects.json')

    # Summary
    print("\n" + "=" * 60)
    print("EXPORT SUMMARY")
    print("=" * 60)
    print(f"  Site: {site_settings['name']}")
    print(f"  Posts: {len(posts)}")
    print(f"  Pages: {len(pages)}")
    print(f"  Custom Post Types: {len(custom_post_types)}")
    print(f"  Taxonomies: {len(taxonomies)}")
    print(f"  Menus: {len(menus)}")
    print(f"  Media: {len(media)}")
    print(f"  Users: {len(users)}")
    print(f"  Redirects: {len(redirects)}")
    print(f"\n  Output directory: {OUTPUT_DIR}")

    cursor.close()
    conn.close()

    print("\n[DONE] Export complete!")

if __name__ == '__main__':
    main()
