import { useState, useEffect } from 'react';
import { Building2, DollarSign, TrendingUp, Sparkles, RefreshCw, AlertCircle, Play, Loader2 } from 'lucide-react';
import { useListings } from './hooks/useListings';
import { StatCard } from './components/StatCard';
import { ListingCard } from './components/ListingCard';
import { Filters } from './components/Filters';
import { Pagination } from './components/Pagination';
import { triggerScrape, getScrapeStatus } from './lib/api';

function formatCurrency(value: number): string {
  if (value >= 1_000_000_000) {
    return `$${(value / 1_000_000_000).toFixed(1)}B`;
  }
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  if (value >= 1_000) {
    return `$${(value / 1_000).toFixed(0)}K`;
  }
  return `$${value.toFixed(0)}`;
}

function App() {
  const {
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
  } = useListings();

  const [scrapeRunning, setScrapeRunning] = useState(false);
  const [scrapeStatus, setScrapeStatus] = useState<string>('');

  // Poll scrape status when running
  useEffect(() => {
    if (!scrapeRunning) return;
    
    const interval = setInterval(async () => {
      try {
        const status = await getScrapeStatus();
        if (!status.running) {
          setScrapeRunning(false);
          setScrapeStatus(status.status === 'completed' 
            ? `Completed! Found ${status.listings_found || 0} listings` 
            : status.error || 'Scrape finished');
          refresh();
          setTimeout(() => setScrapeStatus(''), 5000);
        } else {
          setScrapeStatus(`Running... ${status.listings_found || 0} listings found`);
        }
      } catch {
        setScrapeRunning(false);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [scrapeRunning, refresh]);

  const handleScrape = async () => {
    if (scrapeRunning) return;
    try {
      setScrapeRunning(true);
      setScrapeStatus('Starting scrape...');
      const states = filters.states ? filters.states.split(',') : ['MI', 'CT'];
      await triggerScrape(states, 25);
    } catch (err) {
      setScrapeRunning(false);
      setScrapeStatus(err instanceof Error ? err.message : 'Failed to start scrape');
      setTimeout(() => setScrapeStatus(''), 5000);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[var(--color-bg)]/80 backdrop-blur-xl border-b border-[var(--color-border)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--color-accent)] to-emerald-600 flex items-center justify-center">
                <Building2 size={20} className="text-[var(--color-bg)]" />
              </div>
              <div>
                <h1 className="font-display text-xl font-semibold tracking-tight">BizListing</h1>
                <p className="text-xs text-[var(--color-text-muted)] hidden sm:block">Michigan & Connecticut Business Opportunities</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {scrapeStatus && (
                <span className="text-xs text-[var(--color-text-muted)] hidden sm:inline max-w-[200px] truncate">
                  {scrapeStatus}
                </span>
              )}
              <button
                onClick={handleScrape}
                disabled={scrapeRunning}
                className="flex items-center gap-2 px-4 py-2 bg-[var(--color-accent)] text-[var(--color-bg)] rounded-lg hover:bg-[var(--color-accent-dim)] transition-colors disabled:opacity-50 font-medium"
              >
                {scrapeRunning ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Play size={16} />
                )}
                <span className="text-sm hidden sm:inline">Scrape</span>
              </button>
              <button
                onClick={refresh}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg hover:border-[var(--color-accent)] transition-colors disabled:opacity-50"
              >
                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                <span className="text-sm font-medium hidden sm:inline">Refresh</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {/* Stats Grid */}
        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6 sm:mb-8">
            <StatCard
              label="Total Listings"
              value={stats.total_active_listings.toLocaleString()}
              icon={<Building2 size={20} />}
              subtext="Active opportunities"
            />
            <StatCard
              label="New Today"
              value={stats.new_today.toLocaleString()}
              icon={<Sparkles size={20} />}
              subtext="Fresh listings"
            />
            <StatCard
              label="Average Price"
              value={formatCurrency(stats.avg_asking_price)}
              icon={<DollarSign size={20} />}
              subtext="Across all listings"
            />
            <StatCard
              label="Total Value"
              value={formatCurrency(stats.total_value)}
              icon={<TrendingUp size={20} />}
              subtext="Market opportunity"
            />
          </div>
        )}

        {/* Filters */}
        <div className="mb-6">
          <Filters filters={filters} onUpdate={updateFilters} total={total} />
        </div>

        {/* Error State */}
        {error && (
          <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl mb-6">
            <AlertCircle size={20} className="text-red-400" />
            <span className="text-red-400">{error}</span>
          </div>
        )}

        {/* Loading State - Initial load (no listings yet) */}
        {loading && !listings.length && (
          <div className="flex items-center justify-center py-20">
            <div className="flex items-center gap-3 text-[var(--color-text-muted)]">
              <RefreshCw size={20} className="animate-spin" />
              <span>Loading listings...</span>
            </div>
          </div>
        )}

        {/* No Results */}
        {!loading && listings.length === 0 && (
          <div className="text-center py-20">
            <Building2 size={48} className="mx-auto text-[var(--color-text-muted)] mb-4" />
            <h3 className="text-lg font-semibold mb-2">No listings found</h3>
            <p className="text-[var(--color-text-muted)]">Try adjusting your filters</p>
          </div>
        )}

        {/* Loading overlay when filtering with existing listings */}
        {loading && listings.length > 0 && (
          <div className="flex items-center justify-center gap-2 py-4 mb-4 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl">
            <RefreshCw size={16} className="animate-spin text-[var(--color-accent)]" />
            <span className="text-sm text-[var(--color-text-muted)]">Updating results...</span>
          </div>
        )}

        <div className={`grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mb-8 ${loading ? 'opacity-50 pointer-events-none' : ''}`}>
          {listings.map((listing) => (
            <ListingCard 
              key={listing.id} 
              listing={listing} 
              onToggleReviewed={toggleReviewed}
            />
          ))}
        </div>

        {/* Pagination */}
        <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--color-border)] mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-sm text-[var(--color-text-muted)]">
            <span>Data sourced from BizBuySell</span>
            <span>Updated daily</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
