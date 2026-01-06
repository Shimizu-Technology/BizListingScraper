import type { ListingsResponse, Stats } from '../types';

// In production, use the environment variable + /api. In development, use Vite's proxy.
const API_BASE = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api';

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${API_BASE}/stats`);
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function fetchListings(params: {
  page?: number;
  perPage?: number;
  search?: string;
  states?: string;
  source?: string;
  minPrice?: number;
  maxPrice?: number;
  minCashFlow?: number;
  minRevenue?: number;
  minEbitda?: number;
  isReviewed?: boolean;
  isActive?: boolean;
  sortBy?: string;
  sortOrder?: string;
}): Promise<ListingsResponse> {
  const searchParams = new URLSearchParams();
  
  if (params.page) searchParams.set('page', params.page.toString());
  if (params.perPage) searchParams.set('per_page', params.perPage.toString());
  if (params.search) searchParams.set('search', params.search);
  if (params.states) searchParams.set('states', params.states);
  if (params.source) searchParams.set('source', params.source);
  if (params.minPrice) searchParams.set('min_price', params.minPrice.toString());
  if (params.maxPrice) searchParams.set('max_price', params.maxPrice.toString());
  if (params.minCashFlow) searchParams.set('min_cash_flow', params.minCashFlow.toString());
  if (params.minRevenue) searchParams.set('min_revenue', params.minRevenue.toString());
  if (params.minEbitda) searchParams.set('min_ebitda', params.minEbitda.toString());
  if (params.isReviewed !== undefined) searchParams.set('is_reviewed', params.isReviewed.toString());
  if (params.isActive !== undefined) searchParams.set('is_active', params.isActive.toString());
  if (params.sortBy) searchParams.set('sort_by', params.sortBy);
  if (params.sortOrder) searchParams.set('sort_order', params.sortOrder);
  
  const res = await fetch(`${API_BASE}/listings?${searchParams}`);
  if (!res.ok) throw new Error('Failed to fetch listings');
  return res.json();
}

export async function updateReviewStatus(listingId: number, isReviewed: boolean, notes?: string): Promise<void> {
  const res = await fetch(`${API_BASE}/listings/${listingId}/review`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_reviewed: isReviewed, notes }),
  });
  if (!res.ok) throw new Error('Failed to update review status');
}

export async function triggerScrape(states?: string[], maxPages: number = 25): Promise<{ run_id: number }> {
  const res = await fetch(`${API_BASE}/stats/scrape`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ states, max_pages: maxPages }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to start scrape');
  }
  return res.json();
}

export async function getScrapeStatus(): Promise<{
  running: boolean;
  run_id: number | null;
  status: string;
  listings_found?: number;
  error?: string;
}> {
  const res = await fetch(`${API_BASE}/stats/scrape-status`);
  if (!res.ok) throw new Error('Failed to get scrape status');
  return res.json();
}

export function getExportUrl(params: {
  states?: string;
  source?: string;
  minPrice?: number;
  maxPrice?: number;
  minCashFlow?: number;
  minRevenue?: number;
  minEbitda?: number;
  isReviewed?: boolean;
  search?: string;
  format?: 'excel' | 'csv';
}): string {
  const searchParams = new URLSearchParams();
  
  if (params.states) searchParams.set('states', params.states);
  if (params.source) searchParams.set('source', params.source);
  if (params.minPrice) searchParams.set('min_price', params.minPrice.toString());
  if (params.maxPrice) searchParams.set('max_price', params.maxPrice.toString());
  if (params.minCashFlow) searchParams.set('min_cash_flow', params.minCashFlow.toString());
  if (params.minRevenue) searchParams.set('min_revenue', params.minRevenue.toString());
  if (params.minEbitda) searchParams.set('min_ebitda', params.minEbitda.toString());
  if (params.isReviewed !== undefined) searchParams.set('is_reviewed', params.isReviewed.toString());
  if (params.search) searchParams.set('search', params.search);
  
  // Default to Excel format
  const format = params.format || 'excel';
  return `${API_BASE}/listings/export/${format}?${searchParams}`;
}
