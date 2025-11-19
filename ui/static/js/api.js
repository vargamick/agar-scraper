/**
 * API Service - Handles all API communication
 */

const API = {
    baseUrl: 'http://localhost:3010/api/scraper',
    token: null,
    refreshToken: null,

    /**
     * Initialize API with stored tokens
     */
    init() {
        this.token = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
    },

    /**
     * Make authenticated API request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
            });

            if (response.status === 401 && this.refreshToken) {
                // Try to refresh token
                const refreshed = await this.refresh();
                if (refreshed) {
                    // Retry original request
                    headers['Authorization'] = `Bearer ${this.token}`;
                    return await fetch(url, { ...options, headers });
                }
            }

            return response;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },

    /**
     * Parse API response
     */
    async parseResponse(response) {
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || data.message || 'API request failed');
        }

        // API returns wrapped responses with {success, data}
        return data.data || data;
    },

    /**
     * Authentication
     */
    async login(username, password) {
        const response = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });

        const data = await this.parseResponse(response);

        this.token = data.access_token;
        this.refreshToken = data.refresh_token;

        localStorage.setItem('access_token', this.token);
        localStorage.setItem('refresh_token', this.refreshToken);
        localStorage.setItem('user', JSON.stringify(data.user));

        return data;
    },

    async register(userData) {
        const response = await this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        });

        const data = await this.parseResponse(response);

        this.token = data.access_token;
        this.refreshToken = data.refresh_token;

        localStorage.setItem('access_token', this.token);
        localStorage.setItem('refresh_token', this.refreshToken);
        localStorage.setItem('user', JSON.stringify(data.user));

        return data;
    },

    async refresh() {
        try {
            const response = await this.request('/auth/refresh', {
                method: 'POST',
                body: JSON.stringify({ refresh_token: this.refreshToken }),
            });

            const data = await this.parseResponse(response);

            this.token = data.access_token;
            this.refreshToken = data.refresh_token;

            localStorage.setItem('access_token', this.token);
            localStorage.setItem('refresh_token', this.refreshToken);

            return true;
        } catch (error) {
            this.logout();
            return false;
        }
    },

    logout() {
        this.token = null;
        this.refreshToken = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    },

    isAuthenticated() {
        return !!this.token;
    },

    getCurrentUser() {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    },

    /**
     * Jobs API
     */
    async getJobs(params = {}) {
        const queryParams = new URLSearchParams(params).toString();
        const endpoint = `/jobs${queryParams ? '?' + queryParams : ''}`;
        const response = await this.request(endpoint);
        return this.parseResponse(response);
    },

    async getJob(jobId) {
        const response = await this.request(`/jobs/${jobId}`);
        return this.parseResponse(response);
    },

    async createJob(jobData) {
        const response = await this.request('/jobs', {
            method: 'POST',
            body: JSON.stringify(jobData),
        });
        return this.parseResponse(response);
    },

    async controlJob(jobId, action) {
        const response = await this.request(`/jobs/${jobId}/control`, {
            method: 'POST',
            body: JSON.stringify({ action }),
        });
        return this.parseResponse(response);
    },

    async deleteJob(jobId) {
        const response = await this.request(`/jobs/${jobId}`, {
            method: 'DELETE',
        });
        return this.parseResponse(response);
    },

    async getJobLogs(jobId, params = {}) {
        const queryParams = new URLSearchParams(params).toString();
        const endpoint = `/jobs/${jobId}/logs${queryParams ? '?' + queryParams : ''}`;
        const response = await this.request(endpoint);
        return this.parseResponse(response);
    },

    async getJobResults(jobId, params = {}) {
        const queryParams = new URLSearchParams(params).toString();
        const endpoint = `/jobs/${jobId}/results${queryParams ? '?' + queryParams : ''}`;
        const response = await this.request(endpoint);
        return this.parseResponse(response);
    },

    async getStatistics() {
        const response = await this.request('/stats');
        return this.parseResponse(response);
    },
};

// Initialize API on load
API.init();
