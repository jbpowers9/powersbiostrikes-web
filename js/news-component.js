/**
 * News Component for PowersBioStrikes
 * ====================================
 * Embeddable news widget for stock detail pages.
 *
 * Usage:
 *   <div id="stock-news" data-ticker="AAPL"></div>
 *   <script src="js/news-component.js"></script>
 *   <script>
 *     NewsComponent.init('stock-news', 'AAPL', { maxItems: 5 });
 *   </script>
 */

const NewsComponent = {
    // Configuration
    config: {
        dataUrl: 'data/news.json',
        maxItems: 5,
    },

    // Cached news data
    newsData: null,

    /**
     * Initialize news component
     * @param {string} containerId - DOM element ID to render into
     * @param {string} ticker - Stock ticker to filter news for
     * @param {object} options - Configuration options
     */
    async init(containerId, ticker, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`NewsComponent: Container #${containerId} not found`);
            return;
        }

        const config = { ...this.config, ...options };

        // Show loading state
        container.innerHTML = this.renderLoading();

        try {
            // Fetch or use cached data
            if (!this.newsData) {
                const response = await fetch(config.dataUrl);
                this.newsData = await response.json();
            }

            // Get news for this ticker
            const tickerNews = this.newsData.by_ticker?.[ticker] || [];

            if (tickerNews.length === 0) {
                container.innerHTML = this.renderEmpty(ticker);
                return;
            }

            // Render news
            const newsToShow = tickerNews.slice(0, config.maxItems);
            container.innerHTML = this.renderNews(newsToShow, ticker, config);

        } catch (error) {
            console.error('NewsComponent error:', error);
            container.innerHTML = this.renderError();
        }
    },

    /**
     * Get sentiment icon
     */
    getSentimentIcon(sentiment) {
        switch(sentiment) {
            case 'positive': return '📈';
            case 'negative': return '📉';
            default: return '➖';
        }
    },

    /**
     * Format time ago
     */
    timeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);

        if (seconds < 60) return 'just now';
        if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
        if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
        return Math.floor(seconds / 86400) + 'd ago';
    },

    /**
     * Render loading state
     */
    renderLoading() {
        return `
            <div class="news-widget-loading">
                <div class="animate-pulse space-y-3">
                    <div class="h-16 bg-gray-800 rounded"></div>
                    <div class="h-16 bg-gray-800 rounded"></div>
                    <div class="h-16 bg-gray-800 rounded"></div>
                </div>
            </div>
        `;
    },

    /**
     * Render empty state
     */
    renderEmpty(ticker) {
        return `
            <div class="news-widget-empty text-center py-6 text-gray-500">
                <div class="text-3xl mb-2">📰</div>
                <p>No recent news for $${ticker}</p>
            </div>
        `;
    },

    /**
     * Render error state
     */
    renderError() {
        return `
            <div class="news-widget-error text-center py-6 text-gray-500">
                <div class="text-3xl mb-2">⚠️</div>
                <p>Could not load news</p>
            </div>
        `;
    },

    /**
     * Render news items
     */
    renderNews(items, ticker, config) {
        const newsItems = items.map(item => {
            const isNegative = item.sentiment === 'negative';
            const isFda = item.categories?.includes('fda');
            const isClinical = item.categories?.includes('clinical');

            let borderClass = 'border-gray-700';
            if (isNegative) borderClass = 'border-red-500';
            else if (isFda) borderClass = 'border-green-500';
            else if (isClinical) borderClass = 'border-blue-500';

            const tags = (item.tags || []).slice(0, 2).map(tag =>
                `<span class="text-xs px-2 py-0.5 bg-gray-800 rounded text-gray-400">${tag}</span>`
            ).join(' ');

            return `
                <a href="${item.link}" target="_blank"
                   class="block p-3 bg-gray-900 rounded-lg border-l-2 ${borderClass}
                          hover:bg-gray-800 transition mb-2">
                    <div class="flex items-start gap-2">
                        <span class="text-lg">${this.getSentimentIcon(item.sentiment)}</span>
                        <div class="flex-1 min-w-0">
                            <p class="font-medium text-sm text-white line-clamp-2 mb-1">
                                ${item.title}
                            </p>
                            <div class="flex items-center gap-2 text-xs text-gray-500">
                                <span>${item.publisher}</span>
                                <span>•</span>
                                <span>${this.timeAgo(item.published)}</span>
                            </div>
                            ${tags ? `<div class="mt-1 flex gap-1">${tags}</div>` : ''}
                        </div>
                    </div>
                </a>
            `;
        }).join('');

        return `
            <div class="news-widget">
                <div class="flex items-center justify-between mb-3">
                    <h3 class="font-semibold text-white flex items-center gap-2">
                        <span>📰</span> Recent News
                    </h3>
                    <a href="news.html?ticker=${ticker}" class="text-xs text-gold hover:underline">
                        View All →
                    </a>
                </div>
                <div class="space-y-2">
                    ${newsItems}
                </div>
            </div>
        `;
    },

    /**
     * Render compact inline news (for tables/lists)
     */
    renderCompact(items, maxItems = 3) {
        if (!items || items.length === 0) return '';

        const newsItems = items.slice(0, maxItems).map(item => {
            const icon = this.getSentimentIcon(item.sentiment);
            return `
                <a href="${item.link}" target="_blank"
                   class="block text-sm text-gray-400 hover:text-white truncate"
                   title="${item.title}">
                    ${icon} ${item.title}
                </a>
            `;
        }).join('');

        return `<div class="space-y-1">${newsItems}</div>`;
    },

    /**
     * Get news for a specific ticker (for programmatic use)
     */
    async getTickerNews(ticker) {
        if (!this.newsData) {
            const response = await fetch(this.config.dataUrl);
            this.newsData = await response.json();
        }
        return this.newsData.by_ticker?.[ticker] || [];
    },

    /**
     * Get high priority alerts
     */
    async getAlerts() {
        if (!this.newsData) {
            const response = await fetch(this.config.dataUrl);
            this.newsData = await response.json();
        }
        return this.newsData.high_priority || [];
    }
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NewsComponent;
}
