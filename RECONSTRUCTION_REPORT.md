# WordPress Site Reconstruction Report

## Site Information

| Property | Value |
|----------|-------|
| **Site Name** | Guardian Reinsurance Brokers Zambia Limited |
| **Original URL** | https://guardianreinsurance.co.zm |
| **Database** | MySQL `guardianre` |
| **Table Prefix** | `wp_` |
| **WordPress Theme** | consulting (StyleMix Themes) |
| **Reconstruction Date** | January 13, 2026 |

## Database Discovery Summary

### Core Tables Found
- wp_posts
- wp_postmeta
- wp_options
- wp_terms
- wp_term_taxonomy
- wp_term_relationships
- wp_users
- wp_usermeta
- wp_comments
- wp_commentmeta

### Site Settings

| Setting | Value |
|---------|-------|
| Site URL | https://guardianreinsurance.co.zm |
| Home URL | https://guardianreinsurance.co.zm |
| Permalink Structure | `/%year%/%monthnum%/%day%/%postname%/` |
| Timezone | UTC+0 |
| Date Format | F j, Y |
| Posts Per Page | 10 |
| Charset | UTF-8 |

## Content Statistics

| Content Type | Count |
|--------------|-------|
| Published Posts | 10 |
| Published Pages | 59 |
| Attachments | 95 |
| Categories | 9 |
| Tags | 17 |
| Navigation Menus | 5 |
| Nav Menu Items | 89 |

### Custom Post Types

| Post Type | Published Count |
|-----------|-----------------|
| stm_works | 12 |
| stm_event | 10 |
| cost-calc-templates | 101 |
| cost-calc-categories | 10 |
| wpcf7_contact_form | 9 |
| stm_portfolio | 8 |
| stm_testimonials | 8 |
| stm_vc_sidebar | 8 |
| cost-calc | 7 |
| stm_service | 6 |
| stm_careers | 6 |
| stm_staff | 6 |
| elementor_library | 2 |
| event_member | 1 |

### Taxonomies

| Taxonomy | Term Count |
|----------|------------|
| post_tag | 17 |
| category | 9 |
| stm_works_category | 6 |
| nav_menu | 5 |
| stm_portfolio_category | 3 |
| stm_testimonials_category | 2 |
| elementor_library_type | 1 |

### Navigation Menus

| Menu Name | Slug | Items |
|-----------|------|-------|
| GuardianRe | guardianre | 5 |
| Main Menu | main-menu | 65 |
| Sidebar Menu 1 | sidebar-menu-1 | 7 |
| Sidebar Menu 2 | sidebar-menu-2 | 6 |
| Sidebar Menu 3 | sidebar-menu-3 | 6 |

## Content Format Analysis

| Format | Count |
|--------|-------|
| Gutenberg Block Posts | 8 |
| Classic Editor Posts | 61 |

### Page Builder Used
The site extensively uses **Visual Composer (WPBakery Page Builder)** with the **Consulting theme** by StyleMix Themes. This theme provides numerous custom shortcodes and post types for building professional consulting/business websites.

## SEO Plugin Detection

**No SEO plugin metadata detected.**

The following SEO plugins were checked:
- Yoast SEO (`_yoast_wpseo_*`)
- RankMath (`rank_math_*`)
- All in One SEO (`_aioseo_*`, `_aioseop_*`)
- SEOPress (`_seopress_*`)

## URL Structure

### Original Permalink Pattern
```
/%year%/%monthnum%/%day%/%postname%/
```
Example: `/2024/01/15/hello-world/`

### New URL Structure
```
/blog/[slug]/
```
Example: `/blog/hello-world/`

### Redirects Created
10 redirect rules have been generated to map old URLs to new paths. See `content/_raw/redirects.json` and `public/_redirects`.

## Shortcodes Encountered

### Known/Converted Shortcodes
- `[vc_row]`, `[vc_column]` - Layout structure
- `[vc_column_text]` - Text content
- `[vc_custom_heading]` - Custom headings
- `[vc_single_image]` - Images
- `[vc_separator]` - Dividers
- `[vc_empty_space]` - Spacing
- `[vc_btn]` - Buttons
- `[vc_pie]` - Pie charts
- `[vc_tta_section]`, `[vc_tta_accordion]`, `[vc_tta_tabs]` - Tabs/Accordions
- `[stm_spacing]` - Theme spacing

### Unknown/Theme-Specific Shortcodes (32)
The following shortcodes were encountered but could not be fully converted:

**Page Builder Elements:**
- `[vc_cta]` - Call to action
- `[vc_wp_search]` - WordPress search

**Theme-Specific (STM):**
- `[stm_about_vacancy]`
- `[stm_charts]`
- `[stm_company_history]`
- `[stm_event_lesson]`, `[stm_event_lessons]`
- `[stm_events]`, `[stm_events_form]`, `[stm_events_information]`, `[stm_events_map]`
- `[stm_info_box]`
- `[stm_portfolio]`
- `[stm_post_about_author]`, `[stm_post_bottom]`, `[stm_post_comments]`
- `[stm_pricing_plan]`
- `[stm_quote]`
- `[stm_share_buttons]`
- `[stm_sidebar]`
- `[stm_staff_bottom]`, `[stm_staff_list]`
- `[stm_stats_counter]`
- `[stm_vacancy_bottom]`
- `[stm_works]`

**WooCommerce:**
- `[woocommerce_cart]`
- `[woocommerce_checkout]`
- `[woocommerce_my_account]`

**Other:**
- `[bookit]` - Booking plugin
- `[contact]` - Unknown contact form
- `[rev_slider]` - Revolution Slider
- `[class]`, `[src]` - Likely malformed HTML attributes

## Media Assessment

### Total Attachments: 95

Media files are referenced by their original URLs (e.g., `https://guardianreinsurance.co.zm/wp-content/uploads/...`).

**Media Manifest Location:** `content/media-manifest.json`

### Media Status
- The WordPress uploads directory was not available
- Images reference external URLs which may or may not be accessible
- Templates include fallback placeholder images
- A media fetch script can be used to download accessible images

### To Download Media (Optional)
If the original URLs are still accessible:
```bash
python3 scripts/media_fetch.py
```
This script will attempt to download all referenced media files to `public/images/`.

## Conversion Issues

### Handled Automatically
1. **Gutenberg Blocks**: Stripped block comments, preserved content
2. **Basic VC Shortcodes**: Converted to semantic HTML
3. **Internal Links**: Converted from absolute to relative URLs
4. **Date-based URLs**: Redirects created for old permalink structure

### Requires Manual Review
1. **Theme-specific shortcodes**: Replaced with TODO comments
2. **Contact forms**: Replaced with placeholder text
3. **Dynamic content**: Cost calculators, events, etc. need custom implementation
4. **Missing media**: Images show placeholder when unavailable

### Not Convertible
1. **Revolution Slider**: Complex slider plugin, content not recoverable
2. **Cost Calculator**: Custom plugin, would need reimplementation
3. **Event Booking**: Custom functionality, would need reimplementation

## Output Files

### Export Files (`content/_raw/`)
| File | Description |
|------|-------------|
| `site.json` | Site settings and configuration |
| `posts.json` | All blog posts |
| `pages.json` | All pages |
| `page-hierarchy.json` | Page parent/child relationships |
| `taxonomies.json` | Categories, tags, custom taxonomies |
| `menus.json` | Navigation menus and items |
| `media.json` | Attachment metadata |
| `users.json` | User information |
| `seo.json` | SEO metadata (empty) |
| `redirects.json` | URL redirect mappings |
| `custom-post-types.json` | All custom post type content |
| `discovery.json` | Database discovery results |

### Transformed Content (`src/content/`)
| Directory | Count | Description |
|-----------|-------|-------------|
| `posts/` | 10 | Blog post MDX files |
| `pages/` | 59 | Page MDX files |
| `testimonials/` | 8 | Testimonial MDX files |
| `service/` | 6 | Service MDX files |
| `portfolio/` | 8 | Portfolio MDX files |

## Recommendations

### Immediate Actions
1. **Review all pages** for shortcode placeholders and fill in content manually
2. **Download media** if original URLs are accessible
3. **Test all internal links** for broken references
4. **Update contact information** in footer and contact page

### Future Enhancements
1. **Implement dynamic components** for:
   - Testimonials carousel
   - Portfolio gallery
   - Services grid
   - Team/staff section
2. **Add contact form** using a service like Formspree or Netlify Forms
3. **Implement cost calculator** if needed (custom development)
4. **Add analytics** (Google Analytics, Plausible, etc.)

### Content Updates
1. Review and update:
   - Company description
   - Service offerings
   - Team members
   - Contact details
2. Remove or update demo/placeholder content from the original theme

## Technical Notes

### Build Requirements
- Node.js 18+
- npm or pnpm
- Python 3.8+ (for export scripts only)

### Production Build
```bash
npm run build
```
Output: `dist/` directory with static files

### Hosting Recommendations
- **Netlify**: Recommended (redirects file included)
- **Vercel**: Works with Astro preset
- **Cloudflare Pages**: Excellent for static sites
- **AWS S3 + CloudFront**: For enterprise deployments

---

*Report generated on January 13, 2026*
*WordPress Database: guardianre*
*Target Framework: Astro + Tailwind CSS*
