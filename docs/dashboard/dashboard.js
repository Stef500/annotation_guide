// BRAT Annotation Guide - Dashboard JavaScript

class BuildDashboard {
    constructor() {
        this.repoInfo = this.getRepoInfo();
        this.init();
    }

    getRepoInfo() {
        // Try to get repository information from various sources
        const currentUrl = window.location.href;
        
        // Extract from GitHub Pages URL pattern
        if (currentUrl.includes('.github.io')) {
            const parts = currentUrl.split('/');
            const userIndex = parts.findIndex(part => part.includes('.github.io'));
            if (userIndex >= 0 && userIndex < parts.length - 1) {
                const user = parts[userIndex].replace('.github.io', '');
                const repo = parts[userIndex + 1] || 'annotation_guide';
                return { owner: user, repo: repo };
            }
        }
        
        // Default fallback - you might want to configure this
        return { 
            owner: 'your-username', 
            repo: 'annotation_guide' 
        };
    }

    async init() {
        this.updateTimestamp();
        this.setupLinks();
        await this.loadBuildStatus();
        await this.loadRecentBuilds();
        
        // Refresh data every 5 minutes
        setInterval(() => {
            this.loadBuildStatus();
            this.loadRecentBuilds();
            this.updateTimestamp();
        }, 5 * 60 * 1000);
    }

    updateTimestamp() {
        const timestampElement = document.getElementById('timestamp');
        if (timestampElement) {
            timestampElement.textContent = new Date().toLocaleString();
        }
    }

    setupLinks() {
        const baseUrl = `https://github.com/${this.repoInfo.owner}/${this.repoInfo.repo}`;
        
        const links = {
            'actions-link': `${baseUrl}/actions`,
            'releases-link': `${baseUrl}/releases/latest`,
            'trigger-build-link': `${baseUrl}/actions/workflows/build-pdf.yml`,
            'releases-page-link': `${baseUrl}/releases`,
            'repository-link': baseUrl,
            'readme-link': `${baseUrl}/blob/main/README.md`,
            'templates-link': `${baseUrl}/tree/main/templates`,
            'docs-link': `${baseUrl}/blob/main/docs/`
        };

        Object.entries(links).forEach(([id, url]) => {
            const element = document.getElementById(id);
            if (element) {
                element.href = url;
            }
        });
    }

    async loadBuildStatus() {
        try {
            const apiUrl = `https://api.github.com/repos/${this.repoInfo.owner}/${this.repoInfo.repo}/actions/workflows/build-pdf.yml/runs?per_page=5`;
            const response = await fetch(apiUrl);
            
            if (!response.ok) {
                throw new Error(`GitHub API error: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.workflow_runs && data.workflow_runs.length > 0) {
                const latest = data.workflow_runs[0];
                this.updateBuildStatusDisplay(latest);
                this.updateBuildStatistics(data.workflow_runs);
            }
        } catch (error) {
            console.log('Could not fetch build status:', error);
            this.showError('build-status', 'Unable to load');
        }
    }

    updateBuildStatusDisplay(build) {
        const statusElement = document.getElementById('build-status');
        const lastBuildElement = document.getElementById('last-build');
        
        if (statusElement) {
            const status = build.conclusion || 'in_progress';
            const statusText = status.replace('_', ' ').toUpperCase();
            
            statusElement.textContent = statusText;
            statusElement.className = 'badge ' + this.getStatusClass(status);
        }
        
        if (lastBuildElement) {
            lastBuildElement.textContent = new Date(build.created_at).toLocaleString();
        }
    }

    updateBuildStatistics(builds) {
        const totalBuildsElement = document.getElementById('total-builds');
        const successRateElement = document.getElementById('success-rate');
        
        if (totalBuildsElement) {
            totalBuildsElement.textContent = builds.length;
        }
        
        if (successRateElement && builds.length > 0) {
            const successful = builds.filter(build => build.conclusion === 'success').length;
            const rate = Math.round((successful / builds.length) * 100);
            successRateElement.textContent = `${rate}%`;
        }
    }

    async loadRecentBuilds() {
        try {
            const apiUrl = `https://api.github.com/repos/${this.repoInfo.owner}/${this.repoInfo.repo}/actions/workflows/build-pdf.yml/runs?per_page=5`;
            const response = await fetch(apiUrl);
            
            if (!response.ok) {
                throw new Error(`GitHub API error: ${response.status}`);
            }
            
            const data = await response.json();
            this.displayRecentBuilds(data.workflow_runs || []);
        } catch (error) {
            console.log('Could not fetch recent builds:', error);
            this.showError('recent-builds-list', 'Unable to load recent builds');
        }
    }

    displayRecentBuilds(builds) {
        const container = document.getElementById('recent-builds-list');
        if (!container) return;

        if (builds.length === 0) {
            container.innerHTML = '<p class="loading">No recent builds found</p>';
            return;
        }

        const buildsHtml = builds.map(build => {
            const status = build.conclusion || 'in_progress';
            const duration = build.updated_at && build.created_at ? 
                this.calculateDuration(build.created_at, build.updated_at) : 'Running';
            
            return `
                <div class="build-item">
                    <div class="build-info">
                        <span class="badge ${this.getStatusClass(status)}">${status.replace('_', ' ').toUpperCase()}</span>
                        <span class="build-commit">${build.head_sha.substring(0, 7)}</span>
                        <span>${build.head_branch}</span>
                    </div>
                    <div class="build-duration">${duration}</div>
                </div>
            `;
        }).join('');

        container.innerHTML = buildsHtml;
    }

    getStatusClass(status) {
        const statusMap = {
            'success': 'success',
            'failure': 'failure',
            'in_progress': 'in-progress',
            'queued': 'in-progress',
            'cancelled': 'cancelled',
            'neutral': 'cancelled'
        };
        return statusMap[status] || 'in-progress';
    }

    calculateDuration(start, end) {
        const startTime = new Date(start);
        const endTime = new Date(end);
        const duration = Math.floor((endTime - startTime) / 1000);
        
        if (duration < 60) return `${duration}s`;
        if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
        return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
    }

    showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `<span style="color: #d73a49;">${message}</span>`;
        }
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new BuildDashboard();
});