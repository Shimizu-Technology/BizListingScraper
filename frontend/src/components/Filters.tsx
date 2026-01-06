import { Search, SlidersHorizontal, ArrowUpDown, Download, Filter } from 'lucide-react';
import type { Filters as FiltersType } from '../types';
import { getExportUrl } from '../lib/api';

interface FiltersProps {
  filters: FiltersType;
  onUpdate: (filters: Partial<FiltersType>) => void;
  total: number;
}

export function Filters({ filters, onUpdate, total }: FiltersProps) {
  const handleExport = () => {
    const url = getExportUrl({
      states: filters.states || undefined,
      source: filters.source === 'all' ? undefined : filters.source,
      minPrice: filters.minPrice ? parseFloat(filters.minPrice) : undefined,
      maxPrice: filters.maxPrice ? parseFloat(filters.maxPrice) : undefined,
      minCashFlow: filters.minCashFlow ? parseFloat(filters.minCashFlow) : undefined,
      minRevenue: filters.minRevenue ? parseFloat(filters.minRevenue) : undefined,
      minEbitda: filters.minEbitda ? parseFloat(filters.minEbitda) : undefined,
      isReviewed: filters.isReviewed === 'all' ? undefined : filters.isReviewed === 'reviewed',
      search: filters.search || undefined,
    });
    window.open(url, '_blank');
  };

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4">
      {/* Row 1: Search and States */}
      <div className="flex flex-col lg:flex-row gap-4 mb-4">
        <div className="flex-1">
          <div className="relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" />
            <input
              type="text"
              placeholder="Search listings..."
              value={filters.search}
              onChange={(e) => onUpdate({ search: e.target.value })}
              className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Filter size={18} className="text-[var(--color-text-muted)]" />
          <select
            value={filters.states}
            onChange={(e) => onUpdate({ states: e.target.value })}
            className="bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors"
          >
            <option value="MI,CT">MI + CT</option>
            <option value="MI">Michigan Only</option>
            <option value="CT">Connecticut Only</option>
            <option value="">All States</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={filters.source}
            onChange={(e) => onUpdate({ source: e.target.value })}
            className="bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors"
          >
            <option value="all">All Sources</option>
            <option value="bizquest">BizQuest</option>
            <option value="bizbuysell">BizBuySell</option>
            <option value="businessesforsale">BusinessesForSale</option>
            <option value="transworld">Transworld</option>
            <option value="synergybb">Synergy BB</option>
            <option value="smbdealhunter">SMB Deal Hunter</option>
            <option value="fcbb">FCBB</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={filters.isReviewed}
            onChange={(e) => onUpdate({ isReviewed: e.target.value as 'all' | 'reviewed' | 'unreviewed' })}
            className="bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors"
          >
            <option value="all">All Listings</option>
            <option value="unreviewed">Not Reviewed</option>
            <option value="reviewed">Reviewed</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={filters.isActive}
            onChange={(e) => onUpdate({ isActive: e.target.value as 'active' | 'inactive' | 'all' })}
            className="bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors"
          >
            <option value="active">Active Only</option>
            <option value="inactive">Inactive (Sold/Removed)</option>
            <option value="all">All (Active + Inactive)</option>
          </select>
        </div>
      </div>

      {/* Row 2: Financial Filters */}
      <div className="flex flex-col lg:flex-row gap-4 mb-4">
        <div className="flex items-center gap-2">
          <SlidersHorizontal size={18} className="text-[var(--color-text-muted)]" />
          <span className="text-xs text-[var(--color-text-muted)] whitespace-nowrap">Price:</span>
          <input
            type="text"
            placeholder="Min"
            value={filters.minPrice}
            onChange={(e) => onUpdate({ minPrice: e.target.value.replace(/[^0-9]/g, '') })}
            className="w-24 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors tabular-nums"
          />
          <span className="text-[var(--color-text-muted)]">—</span>
          <input
            type="text"
            placeholder="Max"
            value={filters.maxPrice}
            onChange={(e) => onUpdate({ maxPrice: e.target.value.replace(/[^0-9]/g, '') })}
            className="w-24 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors tabular-nums"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-[var(--color-text-muted)] whitespace-nowrap">CF/SDE ≥</span>
          <input
            type="text"
            placeholder="400000"
            value={filters.minCashFlow}
            onChange={(e) => onUpdate({ minCashFlow: e.target.value.replace(/[^0-9]/g, '') })}
            className="w-28 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors tabular-nums"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-[var(--color-text-muted)] whitespace-nowrap">Revenue ≥</span>
          <input
            type="text"
            placeholder="2000000"
            value={filters.minRevenue}
            onChange={(e) => onUpdate({ minRevenue: e.target.value.replace(/[^0-9]/g, '') })}
            className="w-28 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors tabular-nums"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-[var(--color-text-muted)] whitespace-nowrap">EBITDA ≥</span>
          <input
            type="text"
            placeholder="400000"
            value={filters.minEbitda}
            onChange={(e) => onUpdate({ minEbitda: e.target.value.replace(/[^0-9]/g, '') })}
            className="w-28 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors tabular-nums"
          />
        </div>
      </div>

      {/* Row 3: Sort and Export */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <ArrowUpDown size={18} className="text-[var(--color-text-muted)]" />
          <select
            value={`${filters.sortBy}-${filters.sortOrder}`}
            onChange={(e) => {
              const [sortBy, sortOrder] = e.target.value.split('-');
              onUpdate({ sortBy, sortOrder: sortOrder as 'asc' | 'desc' });
            }}
            className="bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors"
          >
            <option value="first_seen_at-desc">Newest First</option>
            <option value="first_seen_at-asc">Oldest First</option>
            <option value="asking_price-desc">Price: High to Low</option>
            <option value="asking_price-asc">Price: Low to High</option>
            <option value="cash_flow-desc">Cash Flow: High to Low</option>
            <option value="cash_flow-asc">Cash Flow: Low to High</option>
          </select>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-sm text-[var(--color-text-muted)]">
            Showing <span className="font-medium text-[var(--color-text)]">{total.toLocaleString()}</span> listings
          </div>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--color-accent)] text-[var(--color-bg)] rounded-lg hover:bg-[var(--color-accent-dim)] transition-colors font-medium text-sm"
          >
            <Download size={16} />
            Export Excel
          </button>
        </div>
      </div>
    </div>
  );
}
