import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

interface MenuItem {
  id: number;
  title: string;
  url: string;
  order: number;
  parentId: number;
  resolvedSlug?: string;
  resolvedType?: string;
  children?: MenuItem[];
  description?: string;
}

interface RawMenuItem {
  id: number;
  title: string;
  order: number;
  type: string;
  objectType: string;
  objectId: string;
  url: string;
  parentId: number;
  resolvedSlug?: string;
  resolvedType?: string;
}

interface Menu {
  id: number;
  name: string;
  slug: string;
  items: RawMenuItem[];
}

// Default navigation if menu data is not available
const defaultNavigation: MenuItem[] = [
  { id: 1, title: 'Home', url: '/', order: 0, parentId: 0, description: "Zambia's first licensed reinsurance broker since 2006" },
  { id: 2, title: 'About Us', url: '/company-overview', order: 1, parentId: 0, description: 'Our heritage, values, and market position' },
  { id: 3, title: 'Partnerships', url: '/partnerships', order: 2, parentId: 0, description: 'Strategic alliances that enhance client value' },
  { id: 4, title: 'Products', url: '/our-products', order: 3, parentId: 0, description: 'Treaty, facultative, and specialty reinsurance solutions' },
  { id: 5, title: 'Services', url: '/our-services', order: 4, parentId: 0, description: 'Comprehensive broking and advisory services' },
  { id: 6, title: 'News', url: '/blog', order: 5, parentId: 0, description: 'Industry insights and company updates' },
  { id: 7, title: 'Contact', url: '/contact', order: 6, parentId: 0, description: 'Connect with our team in Lusaka' },
];

function resolveUrl(item: RawMenuItem): string {
  // Custom URL
  if (item.type === 'custom' && item.url) {
    // Convert external URLs to internal if they're on the same domain
    if (item.url.startsWith('https://guardianreinsurance.co.zm')) {
      return item.url.replace('https://guardianreinsurance.co.zm', '');
    }
    return item.url;
  }

  // Post type (page, post)
  if (item.type === 'post_type' && item.resolvedSlug) {
    if (item.resolvedType === 'page') {
      return `/${item.resolvedSlug}`;
    }
    if (item.resolvedType === 'post') {
      return `/blog/${item.resolvedSlug}`;
    }
  }

  // Taxonomy (category, tag)
  if (item.type === 'taxonomy' && item.resolvedSlug) {
    if (item.objectType === 'category') {
      return `/category/${item.resolvedSlug}`;
    }
    if (item.objectType === 'post_tag') {
      return `/tag/${item.resolvedSlug}`;
    }
  }

  // Fallback
  return item.url || '#';
}

function buildMenuTree(items: RawMenuItem[]): MenuItem[] {
  const menuItems: MenuItem[] = items.map((item) => ({
    id: item.id,
    title: item.title || 'Untitled',
    url: resolveUrl(item),
    order: item.order,
    parentId: item.parentId,
    children: [],
  }));

  // Build tree structure
  const tree: MenuItem[] = [];
  const itemMap = new Map<number, MenuItem>();

  // First pass: create map
  menuItems.forEach((item) => {
    itemMap.set(item.id, item);
  });

  // Second pass: build tree
  menuItems.forEach((item) => {
    if (item.parentId === 0) {
      tree.push(item);
    } else {
      const parent = itemMap.get(item.parentId);
      if (parent) {
        if (!parent.children) {
          parent.children = [];
        }
        parent.children.push(item);
      }
    }
  });

  // Sort by order
  tree.sort((a, b) => a.order - b.order);
  tree.forEach((item) => {
    if (item.children) {
      item.children.sort((a, b) => a.order - b.order);
    }
  });

  return tree;
}

export async function getNavigation(): Promise<MenuItem[]> {
  try {
    // Try to load from raw data
    const menuPath = join(process.cwd(), 'content', '_raw', 'menus.json');

    if (existsSync(menuPath)) {
      const menuData = JSON.parse(readFileSync(menuPath, 'utf-8')) as Menu[];

      // Find the GuardianRe menu (primary navigation)
      const primaryMenu = menuData.find(
        (m) => m.slug === 'guardianre' || m.name.toLowerCase().includes('guardian')
      );

      if (primaryMenu && primaryMenu.items.length > 0) {
        return buildMenuTree(primaryMenu.items);
      }

      // Fallback to Main Menu
      const mainMenu = menuData.find((m) => m.slug === 'main-menu');
      if (mainMenu && mainMenu.items.length > 0) {
        // Get only top-level items for main navigation
        const topLevelItems = buildMenuTree(mainMenu.items).slice(0, 8);
        return topLevelItems;
      }
    }
  } catch (error) {
    console.error('Error loading navigation:', error);
  }

  return defaultNavigation;
}

export async function getAllMenus(): Promise<Menu[]> {
  try {
    const menuPath = join(process.cwd(), 'content', '_raw', 'menus.json');

    if (existsSync(menuPath)) {
      return JSON.parse(readFileSync(menuPath, 'utf-8')) as Menu[];
    }
  } catch (error) {
    console.error('Error loading menus:', error);
  }

  return [];
}
