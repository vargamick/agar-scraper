# Web Scraper Dashboard UI Guide

## Overview

The Web Scraper Dashboard is a simple, modern web interface for managing scraping jobs. It provides an intuitive way to create, monitor, and manage web scraping tasks without needing to use curl or API clients directly.

## Quick Start

### Starting the UI

```bash
# Option 1: Use the start script
./start_ui.sh

# Option 2: Start manually
cd ui
python3 server.py
```

The UI will be accessible at: **http://localhost:8080**

### Prerequisites

- The API must be running at `http://localhost:3010`
- Python 3.x installed

## Features

### 1. Authentication

**Registration**
- Click "Register" on the login screen
- Provide username, email, full name, and password (minimum 8 characters)
- Automatically logged in after registration

**Login**
- Enter username/email and password
- Tokens are stored in browser localStorage
- Auto-refresh keeps you logged in

### 2. Dashboard Overview

The Overview tab displays:

**Statistics Cards**
- Total Jobs
- Running Jobs
- Queued Jobs
- Completed Jobs
- Failed Jobs
- Total Pages Scraped

**Recent Jobs**
- Last 5 jobs created
- Quick status overview
- Click to view details

**Auto-refresh**: Updates every 5 seconds

### 3. Job Management

**Jobs Tab**
- View all jobs with pagination
- Filter by status (pending, running, completed, failed, cancelled)
- Search and sort capabilities
- Quick actions (pause, resume, cancel, delete)

**Job Actions**
- **Running**: Pause or Cancel
- **Paused**: Resume or Cancel
- **Completed/Failed**: Delete

### 4. Creating Jobs

Navigate to the **Create Job** tab:

#### Basic Information
- **Job Name** (required): Unique identifier for the job
- **Description** (optional): Purpose and details

#### Scraping Configuration
- **Start URLs** (required): One URL per line
- **Max Pages**: Maximum pages to scrape (default: 100)
- **Crawl Depth**: How deep to follow links (default: 3, max: 10)
- **Follow Links**: Whether to crawl linked pages
- **Respect robots.txt**: Honor site crawling rules

#### Output Configuration
- **File Format**: JSON, Markdown, or HTML
- **Save Files Locally**: Store results locally

#### S3 Upload Configuration
- **Enable S3 Upload**: Upload results to AWS S3
- **S3 Bucket**: Override default bucket (optional)
- **S3 Path Prefix**: Custom folder structure (optional)
- **Upload PDFs**: Include downloaded PDFs
- **Upload Screenshots**: Include page screenshots
- **Upload Categories**: Include category JSON files

**Example Job Creation**:
```
Name: Agar Full Scrape
Description: Complete scrape of Agar.com.au website
Start URLs:
  https://www.agar.com.au
Max Pages: 50
Crawl Depth: 3
S3 Upload: Enabled
  Upload PDFs: Yes
  Upload Screenshots: No
```

### 5. Job Details

Click any job card to view detailed information:

#### Info Tab
- Job configuration
- Current status and progress
- Statistics (items extracted, errors, etc.)
- Timestamps (created, started, completed)
- Full configuration JSON

#### Logs Tab
- Real-time job logs
- Color-coded log levels (INFO, WARNING, ERROR)
- Timestamps for each entry
- Last 100 log entries

#### Results Tab
- Scraped data preview
- URLs and content
- Paginated results (up to 50 items)
- Export options

### 6. Monitoring Jobs

**Progress Indicators**
- Progress bars for running jobs
- Page counts (e.g., "45 / 100 pages")
- Percentage completion

**Status Badges**
- Pending: Gray
- Running: Blue
- Completed: Green
- Failed: Red
- Cancelled: Dark gray

**Real-time Updates**
- Auto-refresh every 5 seconds
- Manual refresh button available
- Live progress tracking

## User Interface

### Layout

```
┌─────────────────────────────────────────────┐
│  Header: Web Scraper Dashboard  [User] [Logout] │
├─────────────────────────────────────────────┤
│  [ Overview ] [ Jobs ] [ Create Job ]       │
├─────────────────────────────────────────────┤
│                                             │
│  Tab Content Area                           │
│                                             │
│  - Statistics cards                         │
│  - Job lists                                │
│  - Forms                                    │
│                                             │
└─────────────────────────────────────────────┘
```

### Color Scheme

- Primary: Blue (#2563eb)
- Success: Green (#10b981)
- Danger: Red (#ef4444)
- Warning: Orange (#f59e0b)
- Background: Light gray (#f9fafb)

### Responsive Design

- Desktop: Full layout with multi-column grids
- Tablet: Adjusted columns and spacing
- Mobile: Single column, stacked layout

## API Integration

### Endpoints Used

The UI communicates with these API endpoints:

**Authentication**
- POST `/api/auth/register` - Create account
- POST `/api/auth/login` - Sign in
- POST `/api/auth/refresh` - Refresh token
- GET `/api/auth/me` - Get user info

**Jobs**
- GET `/api/scraper/jobs` - List jobs
- POST `/api/scraper/jobs` - Create job
- GET `/api/scraper/jobs/{id}` - Get job details
- POST `/api/scraper/jobs/{id}/control` - Control job (pause/resume/cancel)
- DELETE `/api/scraper/jobs/{id}` - Delete job
- GET `/api/scraper/jobs/{id}/logs` - Get job logs
- GET `/api/scraper/jobs/{id}/results` - Get job results

**Statistics**
- GET `/api/scraper/stats` - Get overall statistics

### Authentication Flow

1. User logs in or registers
2. API returns access_token and refresh_token
3. Tokens stored in localStorage
4. Access token sent with each request
5. Auto-refresh when token expires

## Troubleshooting

### Common Issues

**Cannot connect to API**
```bash
# Check API is running
docker-compose ps

# Test API health
curl http://localhost:3010/api/scraper/health
```

**CORS Errors**
- API CORS is configured for `http://localhost:8080`
- Don't access UI via IP address (use localhost)
- Check browser console for specific errors

**Login Fails**
- Verify credentials are correct
- Check API logs: `docker-compose logs api`
- Ensure user account exists (register first)

**Jobs Not Updating**
- Check browser console for errors
- Verify auto-refresh is working (Network tab)
- Click manual Refresh button
- Check API connectivity

**UI Not Loading**
```bash
# Restart UI server
cd ui
python3 server.py
```

### Browser Console

Open browser Developer Tools (F12) to:
- View network requests
- Check for JavaScript errors
- Monitor API responses
- Debug authentication issues

## Advanced Usage

### Custom API URL

Edit `ui/static/js/api.js`:

```javascript
const API = {
    baseUrl: 'http://your-api-host:port/api',
    // ...
};
```

### Changing UI Port

Edit `ui/server.py`:

```python
PORT = 8080  # Change to desired port
```

### Disabling Auto-refresh

Edit `ui/static/js/app.js`:

```javascript
// Change refresh interval (milliseconds)
this.refreshInterval = setInterval(() => {
    // ...
}, 10000); // 10 seconds instead of 5
```

Or comment out `this.startAutoRefresh()` to disable entirely.

## Security Considerations

### Authentication Tokens

- Tokens stored in browser localStorage
- Automatically cleared on logout
- Refresh tokens valid for 7 days
- Access tokens valid for 60 minutes

### Best Practices

1. **Don't share tokens**: Keep your localStorage private
2. **Logout when done**: Clear tokens from browser
3. **Use HTTPS in production**: Encrypt all traffic
4. **Strong passwords**: Minimum 8 characters
5. **Regular updates**: Keep API and UI in sync

## Development

### File Structure

```
ui/
├── index.html           # Main page (all screens)
├── static/
│   ├── css/
│   │   └── styles.css   # Complete styling
│   └── js/
│       ├── api.js       # API client and auth
│       └── app.js       # UI logic and rendering
├── server.py            # HTTP server
└── README.md            # Technical docs
```

### Key Components

**API Client** (`api.js`)
- Request handling
- Token management
- Response parsing
- Error handling

**App Logic** (`app.js`)
- Screen management
- Tab switching
- Form handling
- Real-time updates
- Event listeners

**Styling** (`styles.css`)
- Responsive grid layouts
- Component styles
- Status indicators
- Modal dialogs

### Making Changes

1. Edit HTML/CSS/JS files
2. Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+F5)
3. Check browser console for errors
4. Test with API

No build process or compilation needed!

## Keyboard Shortcuts

- **Tab**: Navigate form fields
- **Enter**: Submit forms
- **Escape**: Close modals (planned)
- **Cmd/Ctrl + R**: Refresh page
- **Cmd/Ctrl + Shift + R**: Hard refresh (clear cache)

## Browser Compatibility

Tested and supported:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Uses standard web APIs:
- Fetch API
- LocalStorage
- ES6+ JavaScript
- CSS Grid and Flexbox

## Future Enhancements

Potential features:
- Export job results as CSV/Excel
- Bulk job operations
- Job templates and presets
- Advanced filtering and search
- Job scheduling UI
- Webhook configuration
- Dark mode toggle
- Keyboard shortcuts
- Notification system

## Support

For issues or questions:
1. Check browser console for errors
2. Review API logs: `docker-compose logs api`
3. Verify all services running: `docker-compose ps`
4. Check this documentation
5. Review [API documentation](API_DOCUMENTATION.md)

## Summary

The Web Scraper Dashboard provides a complete interface for:
- Creating and configuring scraping jobs
- Monitoring job progress in real-time
- Viewing logs and results
- Managing job lifecycle (pause, resume, cancel, delete)
- Tracking statistics and performance

Built with vanilla JavaScript for simplicity and maintainability.
