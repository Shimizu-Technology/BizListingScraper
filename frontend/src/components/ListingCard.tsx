import { ExternalLink, TrendingUp, MapPin, Sparkles, Building2, CheckCircle2, Circle } from 'lucide-react';
import type { Listing } from '../types';

interface ListingCardProps {
  listing: Listing;
  onToggleReviewed: (listingId: number, isReviewed: boolean) => void;
}

function formatCurrency(value: number | null): string {
  if (value === null) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
  }).format(date);
}

export function ListingCard({ listing, onToggleReviewed }: ListingCardProps) {
  const handleReviewClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onToggleReviewed(listing.id, !listing.is_reviewed);
  };

  return (
    <div className={`relative bg-[var(--color-surface)] border rounded-xl p-5 transition-all duration-200 group ${
      listing.is_reviewed 
        ? 'border-[var(--color-accent)]/30 opacity-70' 
        : 'border-[var(--color-border)] hover:border-[var(--color-accent)] hover:bg-[var(--color-surface-2)]'
    }`}>
      {/* Review checkbox */}
      <button
        onClick={handleReviewClick}
        className="absolute top-3 right-3 p-1 rounded-lg hover:bg-[var(--color-bg)] transition-colors z-10"
        title={listing.is_reviewed ? 'Mark as not reviewed' : 'Mark as reviewed'}
      >
        {listing.is_reviewed ? (
          <CheckCircle2 size={22} className="text-[var(--color-accent)]" />
        ) : (
          <Circle size={22} className="text-[var(--color-text-muted)] group-hover:text-[var(--color-accent)]" />
        )}
      </button>

      <a
        href={listing.url}
        target="_blank"
        rel="noopener noreferrer"
        className="block"
      >
        <div className="flex items-start justify-between gap-4 mb-3 pr-8">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              {listing.is_new_today && (
                <span className="inline-flex items-center gap-1 text-xs font-medium text-[var(--color-accent)] bg-[var(--color-accent)]/10 px-2 py-0.5 rounded-full">
                  <Sparkles size={12} />
                  New
                </span>
              )}
              {listing.has_price_change && (
                <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded-full">
                  <TrendingUp size={12} />
                  Updated
                </span>
              )}
              {listing.is_reviewed && (
                <span className="inline-flex items-center gap-1 text-xs font-medium text-[var(--color-text-muted)] bg-[var(--color-bg)] px-2 py-0.5 rounded-full">
                  Reviewed
                </span>
              )}
            </div>
            <h3 className="font-semibold text-lg leading-tight line-clamp-2 group-hover:text-[var(--color-accent)] transition-colors">
              {listing.title}
            </h3>
          </div>
          <ExternalLink size={18} className="text-[var(--color-text-muted)] group-hover:text-[var(--color-accent)] flex-shrink-0 transition-colors mt-1" />
        </div>

        <div className="flex items-center gap-2 text-sm text-[var(--color-text-muted)] mb-4">
          <MapPin size={14} />
          <span>{listing.city || 'Unknown'}, {listing.state || '—'}</span>
        </div>

        {listing.description && (
          <p className="text-sm text-[var(--color-text-muted)] line-clamp-2 mb-4">
            {listing.description}
          </p>
        )}

        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-[var(--color-border)]">
          <div>
            <div className="text-xs text-[var(--color-text-muted)] mb-1">Asking Price</div>
            <div className="font-semibold text-lg tabular-nums text-[var(--color-accent)]">
              {formatCurrency(listing.asking_price)}
            </div>
          </div>
          <div>
            <div className="text-xs text-[var(--color-text-muted)] mb-1">Cash Flow</div>
            <div className="font-semibold text-lg tabular-nums">
              {formatCurrency(listing.cash_flow)}
            </div>
          </div>
        </div>

        {/* Additional financials if available */}
        {(listing.gross_revenue || listing.ebitda) && (
          <div className="grid grid-cols-2 gap-4 pt-2">
            {listing.gross_revenue && (
              <div>
                <div className="text-xs text-[var(--color-text-muted)] mb-1">Revenue</div>
                <div className="font-medium tabular-nums text-sm">
                  {formatCurrency(listing.gross_revenue)}
                </div>
              </div>
            )}
            {listing.ebitda && (
              <div>
                <div className="text-xs text-[var(--color-text-muted)] mb-1">EBITDA</div>
                <div className="font-medium tabular-nums text-sm">
                  {formatCurrency(listing.ebitda)}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="flex items-center justify-between mt-4 pt-3 border-t border-[var(--color-border)] text-xs text-[var(--color-text-muted)]">
          <div className="flex items-center gap-2">
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-medium ${
              listing.source === 'bizbuysell' 
                ? 'bg-blue-500/10 text-blue-400' 
                : listing.source === 'bizquest'
                ? 'bg-emerald-500/10 text-emerald-400'
                : listing.source === 'fcbb'
                ? 'bg-orange-500/10 text-orange-400'
                : listing.source === 'transworld'
                ? 'bg-purple-500/10 text-purple-400'
                : listing.source === 'businessesforsale'
                ? 'bg-cyan-500/10 text-cyan-400'
                : listing.source === 'smbdealhunter'
                ? 'bg-rose-500/10 text-rose-400'
                : listing.source === 'synergybb'
                ? 'bg-amber-500/10 text-amber-400'
                : listing.source === 'murphybusiness'
                ? 'bg-teal-500/10 text-teal-400'
                : 'bg-[var(--color-bg)] text-[var(--color-text-muted)]'
            }`}>
              <Building2 size={12} />
              {listing.source === 'bizbuysell' ? 'BizBuySell' : 
               listing.source === 'bizquest' ? 'BizQuest' : 
               listing.source === 'fcbb' ? 'FCBB' : 
               listing.source === 'transworld' ? 'Transworld' : 
               listing.source === 'businessesforsale' ? 'BizForSale' :
               listing.source === 'smbdealhunter' ? 'SMB Deal Hunter' :
               listing.source === 'synergybb' ? 'Synergy BB' :
               listing.source === 'murphybusiness' ? 'Murphy Biz' : listing.source}
            </span>
          </div>
          <span>Added {formatDate(listing.first_seen_at)}</span>
        </div>
      </a>
    </div>
  );
}
