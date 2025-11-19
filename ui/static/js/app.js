/**
 * Main Application Logic
 */

class App {
    constructor() {
        this.currentJobId = null;
        this.refreshInterval = null;
        this.init();
    }

    init() {
        // Check authentication
        if (API.isAuthenticated()) {
            this.showDashboard();
        } else {
            this.showLogin();
        }

        // Setup event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Login/Register forms
        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('registerForm').addEventListener('submit', (e) => this.handleRegister(e));
        document.getElementById('showRegister').addEventListener('click', (e) => {
            e.preventDefault();
            this.showScreen('registerScreen');
        });
        document.getElementById('showLogin').addEventListener('click', (e) => {
            e.preventDefault();
            this.showScreen('loginScreen');
        });

        // Logout
        document.getElementById('logoutBtn').addEventListener('click', () => this.handleLogout());

        // Navigation tabs
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });

        // Job detail tabs
        document.querySelectorAll('.job-detail-tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchJobDetailTab(tab.dataset.detailTab));
        });

        // Modal
        document.querySelector('.modal-close').addEventListener('click', () => this.closeModal());
        document.getElementById('jobDetailModal').addEventListener('click', (e) => {
            if (e.target.id === 'jobDetailModal') {
                this.closeModal();
            }
        });

        // Create job form
        document.getElementById('createJobForm').addEventListener('submit', (e) => this.handleCreateJob(e));

        // S3 checkbox toggle
        document.getElementById('uploadToS3').addEventListener('change', (e) => {
            document.getElementById('s3ConfigSection').style.display = e.target.checked ? 'block' : 'none';
        });

        // Filters
        document.getElementById('statusFilter').addEventListener('change', () => this.loadJobs());
        document.getElementById('refreshJobsBtn').addEventListener('click', () => this.loadJobs());
    }

    showScreen(screenId) {
        document.querySelectorAll('.screen').forEach(screen => screen.classList.remove('active'));
        document.getElementById(screenId).classList.add('active');
    }

    showLogin() {
        this.showScreen('loginScreen');
    }

    showDashboard() {
        this.showScreen('dashboardScreen');
        const user = API.getCurrentUser();
        if (user) {
            document.getElementById('userInfo').textContent = `${user.full_name || user.username}`;
        }
        this.loadStatistics();
        this.loadRecentJobs();
        this.startAutoRefresh();
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
        event.target.classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.getElementById(`${tabName}Tab`).classList.add('active');

        // Load data for tab
        if (tabName === 'jobs') {
            this.loadJobs();
        } else if (tabName === 'overview') {
            this.loadStatistics();
            this.loadRecentJobs();
        }
    }

    switchJobDetailTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.job-detail-tab').forEach(tab => tab.classList.remove('active'));
        event.target.classList.add('active');

        // Update tab content
        document.querySelectorAll('.job-detail-content').forEach(content => content.classList.remove('active'));
        document.getElementById(`job${tabName.charAt(0).toUpperCase() + tabName.slice(1)}Tab`).classList.add('active');

        // Load data for tab
        if (tabName === 'logs' && this.currentJobId) {
            this.loadJobLogs(this.currentJobId);
        } else if (tabName === 'results' && this.currentJobId) {
            this.loadJobResults(this.currentJobId);
        }
    }

    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            const activeTab = document.querySelector('.tab-content.active');
            if (activeTab && activeTab.id === 'overviewTab') {
                this.loadStatistics();
                this.loadRecentJobs();
            } else if (activeTab && activeTab.id === 'jobsTab') {
                this.loadJobs();
            }
        }, 5000); // Refresh every 5 seconds
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        const errorDiv = document.getElementById('loginError');
        errorDiv.style.display = 'none';

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        try {
            await API.login(username, password);
            this.showDashboard();
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        const errorDiv = document.getElementById('registerError');
        errorDiv.style.display = 'none';

        const userData = {
            username: document.getElementById('regUsername').value,
            email: document.getElementById('regEmail').value,
            full_name: document.getElementById('regFullName').value,
            password: document.getElementById('regPassword').value,
        };

        try {
            await API.register(userData);
            this.showDashboard();
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        }
    }

    handleLogout() {
        API.logout();
        this.stopAutoRefresh();
        this.showLogin();
    }

    async loadStatistics() {
        try {
            const stats = await API.getStatistics();
            document.getElementById('statTotalJobs').textContent = stats.totalJobs;
            document.getElementById('statRunningJobs').textContent = stats.runningJobs;
            document.getElementById('statQueuedJobs').textContent = stats.queuedJobs;
            document.getElementById('statCompletedJobs').textContent = stats.completedJobs;
            document.getElementById('statFailedJobs').textContent = stats.failedJobs;
            document.getElementById('statPagesScraped').textContent = stats.totalPagesScraped.toLocaleString();
        } catch (error) {
            console.error('Failed to load statistics:', error);
        }
    }

    async loadRecentJobs() {
        try {
            const data = await API.getJobs({ limit: 5 });
            this.renderJobsList(data.jobs, 'recentJobsList');
        } catch (error) {
            console.error('Failed to load recent jobs:', error);
        }
    }

    async loadJobs() {
        const statusFilter = document.getElementById('statusFilter').value;
        const params = { limit: 50 };
        if (statusFilter) {
            params.status = statusFilter;
        }

        const container = document.getElementById('jobsList');
        container.innerHTML = '<div class="loading">Loading...</div>';

        try {
            const data = await API.getJobs(params);
            this.renderJobsList(data.jobs, 'jobsList');
        } catch (error) {
            console.error('Failed to load jobs:', error);
            container.innerHTML = `<div class="error-message">Failed to load jobs: ${error.message}</div>`;
        }
    }

    renderJobsList(jobs, containerId) {
        const container = document.getElementById(containerId);

        if (!jobs || jobs.length === 0) {
            container.innerHTML = '<div class="loading">No jobs found</div>';
            return;
        }

        container.innerHTML = jobs.map(job => this.createJobCard(job)).join('');

        // Add click handlers
        container.querySelectorAll('.job-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.classList.contains('btn')) {
                    this.showJobDetail(card.dataset.jobId);
                }
            });
        });

        // Add action button handlers
        container.querySelectorAll('.btn-danger').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const jobId = btn.closest('.job-card').dataset.jobId;
                this.deleteJob(jobId);
            });
        });

        container.querySelectorAll('.btn-secondary').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const jobId = btn.closest('.job-card').dataset.jobId;
                const action = btn.dataset.action;
                this.controlJob(jobId, action);
            });
        });
    }

    createJobCard(job) {
        const statusClass = `status-${job.status}`;
        const createdAt = new Date(job.createdAt).toLocaleString();

        let progressBar = '';
        if (job.status === 'running') {
            const percentage = job.progress?.percentage || 0;
            const phase = job.stats?.phase || 'starting';
            const categoriesFound = job.stats?.categories_found || job.stats?.categoriesFound || 0;
            const productsFound = job.stats?.products_found || job.stats?.productsFound || 0;

            let phaseText = '';
            if (phase === 'discovering_categories') {
                phaseText = 'Discovering categories...';
            } else if (phase === 'collecting_products') {
                phaseText = `Collecting products from ${categoriesFound} categories...`;
            } else if (phase === 'scraping_products') {
                phaseText = `Scraping ${productsFound} products`;
            } else {
                phaseText = `${job.progress.pagesScraped || 0} / ${job.progress.totalPages || 0} pages`;
            }

            progressBar = `
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${percentage}%"></div>
                </div>
                <div style="font-size: 12px; color: var(--gray-600); margin-top: 4px;">
                    ${phaseText}
                </div>
            `;
        }

        let actions = '';
        if (job.status === 'running') {
            actions = `<button class="btn btn-secondary btn-small" data-action="pause">Pause</button>`;
        } else if (job.status === 'paused') {
            actions = `<button class="btn btn-secondary btn-small" data-action="resume">Resume</button>`;
        }
        if (job.status === 'running' || job.status === 'paused' || job.status === 'pending') {
            actions += `<button class="btn btn-danger btn-small" data-action="cancel">Cancel</button>`;
        }
        if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
            actions = `<button class="btn btn-danger btn-small">Delete</button>`;
        }

        return `
            <div class="job-card" data-job-id="${job.jobId}">
                <div class="job-card-header">
                    <div>
                        <div class="job-card-title">${this.escapeHtml(job.name)}</div>
                        ${job.description ? `<div class="job-card-description">${this.escapeHtml(job.description)}</div>` : ''}
                    </div>
                    <span class="status-badge ${statusClass}">${job.status}</span>
                </div>
                ${progressBar}
                <div class="job-card-meta">
                    <span>Created: ${createdAt}</span>
                    <span>By: ${this.escapeHtml(job.createdBy)}</span>
                    <span>Type: ${job.type}</span>
                </div>
                ${actions ? `<div class="job-card-actions">${actions}</div>` : ''}
            </div>
        `;
    }

    async showJobDetail(jobId) {
        this.currentJobId = jobId;

        try {
            const job = await API.getJob(jobId);

            document.getElementById('modalJobName').textContent = job.name;

            const infoHtml = `
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Status</div>
                        <div class="info-value">
                            <span class="status-badge status-${job.status}">${job.status}</span>
                        </div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Job ID</div>
                        <div class="info-value">${job.jobId}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Type</div>
                        <div class="info-value">${job.type}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Created By</div>
                        <div class="info-value">${this.escapeHtml(job.createdBy)}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Created At</div>
                        <div class="info-value">${new Date(job.createdAt).toLocaleString()}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Current Phase</div>
                        <div class="info-value">${this.formatPhase(job.stats.phase || 'unknown')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Categories Found</div>
                        <div class="info-value">${job.stats.categories_found || job.stats.categoriesFound || 0}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Products Found</div>
                        <div class="info-value">${job.stats.products_found || job.stats.productsFound || 0}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Pages Scraped</div>
                        <div class="info-value">${job.progress.pagesScraped || 0} / ${job.progress.totalPages || 0}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Items Extracted</div>
                        <div class="info-value">${job.stats.itemsExtracted || job.stats.items_extracted || 0}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Errors</div>
                        <div class="info-value">${job.stats.errors || 0}</div>
                    </div>
                </div>

                <h3 style="margin-top: 24px; margin-bottom: 12px;">Configuration</h3>
                <pre style="background: var(--gray-50); padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 12px;">${JSON.stringify(job.config, null, 2)}</pre>

                ${job.description ? `
                    <h3 style="margin-top: 24px; margin-bottom: 12px;">Description</h3>
                    <p>${this.escapeHtml(job.description)}</p>
                ` : ''}
            `;

            document.getElementById('jobDetailInfo').innerHTML = infoHtml;

            // Show modal
            document.getElementById('jobDetailModal').classList.add('active');

            // Reset to info tab
            this.switchJobDetailTab('info');

        } catch (error) {
            console.error('Failed to load job details:', error);
            alert('Failed to load job details');
        }
    }

    async loadJobLogs(jobId) {
        try {
            const data = await API.getJobLogs(jobId, { limit: 100 });
            const container = document.getElementById('jobLogs');

            if (!data.logs || data.logs.length === 0) {
                container.innerHTML = '<div class="loading">No logs available</div>';
                return;
            }

            const logsHtml = data.logs.map(log => {
                const timestamp = new Date(log.timestamp).toLocaleTimeString();
                return `
                    <div class="log-entry">
                        <span class="log-timestamp">${timestamp}</span>
                        <span class="log-level log-level-${log.level}">${log.level.toUpperCase()}</span>
                        <span>${this.escapeHtml(log.message)}</span>
                    </div>
                `;
            }).join('');

            container.innerHTML = logsHtml;
        } catch (error) {
            console.error('Failed to load logs:', error);
            document.getElementById('jobLogs').innerHTML = '<div class="loading">Failed to load logs</div>';
        }
    }

    async loadJobResults(jobId) {
        try {
            const data = await API.getJobResults(jobId, { limit: 50 });
            const container = document.getElementById('jobResults');

            if (!data.results || data.results.length === 0) {
                container.innerHTML = '<div class="loading">No results available</div>';
                return;
            }

            const resultsHtml = data.results.map(result => {
                return `
                    <div class="result-item">
                        ${result.url ? `<div class="result-url">${this.escapeHtml(result.url)}</div>` : ''}
                        <div class="result-content">
                            <pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word;">${JSON.stringify(result.content, null, 2)}</pre>
                        </div>
                    </div>
                `;
            }).join('');

            container.innerHTML = resultsHtml;
        } catch (error) {
            console.error('Failed to load results:', error);
            document.getElementById('jobResults').innerHTML = '<div class="loading">Failed to load results</div>';
        }
    }

    closeModal() {
        document.getElementById('jobDetailModal').classList.remove('active');
        this.currentJobId = null;
    }

    async controlJob(jobId, action) {
        try {
            await API.controlJob(jobId, action);
            this.loadJobs();
            this.loadRecentJobs();
        } catch (error) {
            console.error('Failed to control job:', error);
            alert(`Failed to ${action} job: ${error.message}`);
        }
    }

    async deleteJob(jobId) {
        if (!confirm('Are you sure you want to delete this job?')) {
            return;
        }

        try {
            await API.deleteJob(jobId);
            this.loadJobs();
            this.loadRecentJobs();
            this.loadStatistics();
        } catch (error) {
            console.error('Failed to delete job:', error);
            alert(`Failed to delete job: ${error.message}`);
        }
    }

    async handleCreateJob(e) {
        e.preventDefault();

        const errorDiv = document.getElementById('createJobError');
        const successDiv = document.getElementById('createJobSuccess');
        errorDiv.style.display = 'none';
        successDiv.style.display = 'none';

        // Parse start URLs
        const startUrlsText = document.getElementById('startUrls').value;
        const startUrls = startUrlsText.split('\n').map(url => url.trim()).filter(url => url);

        if (startUrls.length === 0) {
            errorDiv.textContent = 'Please enter at least one start URL';
            errorDiv.style.display = 'block';
            return;
        }

        // Build job configuration
        const jobData = {
            name: document.getElementById('jobName').value,
            description: document.getElementById('jobDescription').value || null,
            type: 'web',
            config: {
                startUrls,
                maxPages: parseInt(document.getElementById('maxPages').value),
                crawlDepth: parseInt(document.getElementById('crawlDepth').value),
                followLinks: document.getElementById('followLinks').checked,
                respectRobotsTxt: document.getElementById('respectRobotsTxt').checked,
            },
            output: {
                saveFiles: document.getElementById('saveFiles').checked,
                fileFormat: document.getElementById('fileFormat').value,
            },
        };

        // Add S3 configuration if enabled
        if (document.getElementById('uploadToS3').checked) {
            jobData.output.uploadToS3 = {
                enabled: true,
                uploadPdfs: document.getElementById('uploadPdfs').checked,
                uploadScreenshots: document.getElementById('uploadScreenshots').checked,
                uploadCategories: document.getElementById('uploadCategories').checked,
            };

            const s3Bucket = document.getElementById('s3Bucket').value.trim();
            const s3Prefix = document.getElementById('s3Prefix').value.trim();

            if (s3Bucket) {
                jobData.output.uploadToS3.bucket = s3Bucket;
            }
            if (s3Prefix) {
                jobData.output.uploadToS3.prefix = s3Prefix;
            }
        }

        try {
            const result = await API.createJob(jobData);

            successDiv.textContent = `Job created successfully! Job ID: ${result.jobId}`;
            successDiv.style.display = 'block';

            // Reset form
            document.getElementById('createJobForm').reset();

            // Refresh jobs list
            this.loadJobs();
            this.loadRecentJobs();
            this.loadStatistics();

            // Switch to jobs tab after a delay
            setTimeout(() => {
                document.querySelector('.nav-tab[data-tab="jobs"]').click();
            }, 2000);

        } catch (error) {
            console.error('Failed to create job:', error);
            errorDiv.textContent = `Failed to create job: ${error.message}`;
            errorDiv.style.display = 'block';
        }
    }

    formatPhase(phase) {
        const phaseMap = {
            'discovering_categories': 'Discovering Categories',
            'collecting_products': 'Collecting Products',
            'scraping_products': 'Scraping Products',
            'downloading_pdfs': 'Downloading PDFs',
            'uploading_to_s3': 'Uploading to S3',
            'completed': 'Completed',
            'unknown': 'Starting...'
        };
        return phaseMap[phase] || phase;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
