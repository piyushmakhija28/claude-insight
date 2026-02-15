/**
 * Claude Insight - Internationalization (i18n) Library
 * Handles multi-language support for the application
 */

class I18nManager {
    constructor() {
        this.currentLanguage = localStorage.getItem('language') || 'en';
        this.translations = {};
        this.availableLanguages = ['en', 'hi', 'es', 'fr', 'de'];
        this.languageNames = {
            'en': 'English',
            'hi': 'हिन्दी',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch'
        };
    }

    /**
     * Initialize i18n system
     */
    async init() {
        await this.loadLanguage(this.currentLanguage);
        this.applyTranslations();
        this.updateLanguageSelector();
    }

    /**
     * Load language file
     */
    async loadLanguage(lang) {
        try {
            const response = await fetch(`/static/i18n/${lang}.json`);
            if (!response.ok) {
                console.error(`Failed to load language: ${lang}`);
                // Fallback to English
                if (lang !== 'en') {
                    return this.loadLanguage('en');
                }
                return;
            }
            this.translations = await response.json();
            this.currentLanguage = lang;
            localStorage.setItem('language', lang);

            // Update HTML lang attribute
            document.documentElement.lang = lang;

            // Trigger custom event
            window.dispatchEvent(new CustomEvent('languageChanged', {
                detail: { language: lang }
            }));
        } catch (error) {
            console.error('Error loading language:', error);
        }
    }

    /**
     * Change language
     */
    async changeLanguage(lang) {
        if (!this.availableLanguages.includes(lang)) {
            console.error(`Language ${lang} not available`);
            return;
        }

        await this.loadLanguage(lang);
        this.applyTranslations();
        this.updateLanguageSelector();

        // Reload current page to apply translations fully
        // Comment this out if you want dynamic translation without reload
        // window.location.reload();
    }

    /**
     * Get translation by key path (e.g., "common.save")
     */
    t(keyPath, defaultValue = '') {
        const keys = keyPath.split('.');
        let value = this.translations;

        for (const key of keys) {
            if (value && typeof value === 'object' && key in value) {
                value = value[key];
            } else {
                return defaultValue || keyPath;
            }
        }

        return value || defaultValue || keyPath;
    }

    /**
     * Apply translations to DOM elements with data-i18n attribute
     */
    applyTranslations() {
        // Translate elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);

            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        });

        // Translate elements with data-i18n-html attribute (allows HTML)
        document.querySelectorAll('[data-i18n-html]').forEach(element => {
            const key = element.getAttribute('data-i18n-html');
            element.innerHTML = this.t(key);
        });

        // Translate placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });

        // Translate titles
        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.t(key);
        });

        // Translate values
        document.querySelectorAll('[data-i18n-value]').forEach(element => {
            const key = element.getAttribute('data-i18n-value');
            element.value = this.t(key);
        });
    }

    /**
     * Update language selector dropdown
     */
    updateLanguageSelector() {
        const selector = document.getElementById('languageSelector');
        if (selector) {
            selector.value = this.currentLanguage;
        }

        // Update language name in button/display
        const langDisplay = document.getElementById('currentLanguage');
        if (langDisplay) {
            langDisplay.textContent = this.languageNames[this.currentLanguage];
        }
    }

    /**
     * Get current language
     */
    getCurrentLanguage() {
        return this.currentLanguage;
    }

    /**
     * Get available languages
     */
    getAvailableLanguages() {
        return this.availableLanguages.map(code => ({
            code: code,
            name: this.languageNames[code]
        }));
    }

    /**
     * Format date according to current language
     */
    formatDate(date, options = {}) {
        const d = typeof date === 'string' ? new Date(date) : date;
        return new Intl.DateTimeFormat(this.currentLanguage, options).format(d);
    }

    /**
     * Format number according to current language
     */
    formatNumber(number, options = {}) {
        return new Intl.NumberFormat(this.currentLanguage, options).format(number);
    }

    /**
     * Format currency according to current language
     */
    formatCurrency(amount, currency = 'USD', options = {}) {
        return new Intl.NumberFormat(this.currentLanguage, {
            style: 'currency',
            currency: currency,
            ...options
        }).format(amount);
    }
}

// Create global instance
window.i18n = new I18nManager();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    await window.i18n.init();
});

// Helper function for easy translation access
window.t = (key, defaultValue) => window.i18n.t(key, defaultValue);
