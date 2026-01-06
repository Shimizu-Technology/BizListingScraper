export interface Listing {
  id: number;
  external_id: string;
  source: string;
  url: string;
  title: string;
  asking_price: number | null;
  cash_flow: number | null;
  gross_revenue: number | null;
  ebitda: number | null;
  city: string | null;
  state: string | null;
  category: string | null;
  description: string | null;
  broker_name: string | null;
  broker_company: string | null;
  first_seen_at: string;
  last_seen_at: string;
  last_updated_at: string | null;
  is_active: boolean;
  is_new_today: boolean;
  has_price_change: boolean;
  is_reviewed: boolean;
  reviewed_at: string | null;
  notes: string | null;
}

export interface ListingsResponse {
  listings: Listing[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface Stats {
  total_active_listings: number;
  new_today: number;
  updated_today: number;
  removed_this_week: number;
  avg_asking_price: number;
  total_value: number;
  listings_by_category: Record<string, number>;
  listings_by_state: Record<string, number>;
}

export interface Filters {
  search: string;
  states: string;
  source: string;  // 'all' | 'bizbuysell' | 'bizquest'
  minPrice: string;
  maxPrice: string;
  minCashFlow: string;
  minRevenue: string;
  minEbitda: string;
  isReviewed: 'all' | 'reviewed' | 'unreviewed';
  isActive: 'active' | 'inactive' | 'all';
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}
