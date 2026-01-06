import { useState, useEffect, useCallback } from 'react';
import type { Listing, ListingsResponse, Stats, Filters } from '../types';
import { fetchListings, fetchStats, updateReviewStatus } from '../lib/api';

export function useListings() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState<Filters>({
    search: '',
    states: 'MI,CT',
    source: 'all',
    minPrice: '',
    maxPrice: '',
    minCashFlow: '',
    minRevenue: '',
    minEbitda: '',
    isReviewed: 'all',
    isActive: 'active',
    sortBy: 'first_seen_at',
    sortOrder: 'desc',
  });

  const loadListings = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data: ListingsResponse = await fetchListings({
        page,
        perPage: 25,
        search: filters.search || undefined,
        states: filters.states || undefined,
        source: filters.source === 'all' ? undefined : filters.source,
        minPrice: filters.minPrice ? parseFloat(filters.minPrice) : undefined,
        maxPrice: filters.maxPrice ? parseFloat(filters.maxPrice) : undefined,
        minCashFlow: filters.minCashFlow ? parseFloat(filters.minCashFlow) : undefined,
        minRevenue: filters.minRevenue ? parseFloat(filters.minRevenue) : undefined,
        minEbitda: filters.minEbitda ? parseFloat(filters.minEbitda) : undefined,
        isReviewed: filters.isReviewed === 'all' ? undefined : filters.isReviewed === 'reviewed',
        isActive: filters.isActive === 'all' ? undefined : filters.isActive === 'active',
        sortBy: filters.sortBy,
        sortOrder: filters.sortOrder,
      });
      
      setListings(data.listings);
      setTotalPages(data.pages);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load listings');
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  const loadStats = useCallback(async () => {
    try {
      const data = await fetchStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  }, []);

  useEffect(() => {
    loadListings();
  }, [loadListings]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const updateFilters = (newFilters: Partial<Filters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    setPage(1);
  };

  const toggleReviewed = async (listingId: number, isReviewed: boolean) => {
    // Optimistic update - update UI immediately
    setListings(prev => 
      prev.map(l => l.id === listingId ? { ...l, is_reviewed: isReviewed } : l)
    );
    
    try {
      await updateReviewStatus(listingId, isReviewed);
    } catch (err) {
      // Revert on error
      console.error('Failed to update review status:', err);
      setListings(prev => 
        prev.map(l => l.id === listingId ? { ...l, is_reviewed: !isReviewed } : l)
      );
    }
  };

  const refresh = () => {
    loadListings();
    loadStats();
  };

  return {
    listings,
    stats,
    loading,
    error,
    page,
    setPage,
    totalPages,
    total,
    filters,
    updateFilters,
    toggleReviewed,
    refresh,
  };
}
