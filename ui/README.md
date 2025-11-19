# Web Scraper Dashboard UI

A simple, clean web interface for managing web scraping jobs.

## Features

- **Authentication**: Login and registration
- **Dashboard**: View statistics and recent jobs
- **Job Management**: Create, monitor, pause, resume, cancel, and delete jobs
- **Real-time Updates**: Auto-refresh every 5 seconds
- **Job Details**: View configuration, logs, and results
- **S3 Integration**: Configure S3 uploads per job

## Quick Start

### 1. Make sure the API is running

The API should be running at `http://localhost:3010`

```bash
# From the project root
cd /Users/mick/AI/c4ai/agar
docker-compose up
```

### 2. Start the UI server

```bash
cd ui
python3 server.py
```

The UI will be available at: **http://localhost:8080**

### 3. Login or Register

- Use the registration form to create a new account
- Or login with existing credentials

## File Structure

```
ui/
├── index.html              # Main HTML file
├── static/
│   ├── css/
│   │   └── styles.css     # All styling
│   └── js/
│       ├── api.js         # API client
│       └── app.js         # Application logic
├── server.py              # Simple HTTP server
└── README.md              # This file
```

## Technology Stack

- **Frontend**: Vanilla HTML, CSS, JavaScript (no frameworks)
- **API Communication**: Fetch API
- **Server**: Python http.server
- **Styling**: Custom CSS with CSS variables

## Configuration

### API Base URL

The API URL is configured in `static/js/api.js`:

```javascript
const API = {
    baseUrl: 'http://localhost:3010/api/scraper',
    // ...
};
```

Change this if your API is running on a different host/port.

### UI Server Port

The UI server port is configured in `server.py`:

```python
PORT = 8080
```

## Usage

### Creating a Scraping Job

1. Click the **Create Job** tab
2. Fill in the job details:
   - Job Name (required)
   - Description (optional)
   - Start URLs (one per line, required)
   - Max Pages
   - Crawl Depth
3. Configure output settings:
   - File format (JSON, Markdown, HTML)
   - S3 upload options
4. Click **Create and Start Job**

### Monitoring Jobs

- The **Overview** tab shows statistics and recent jobs
- The **Jobs** tab shows all jobs with filtering options
- Click on any job card to view detailed information
- Jobs auto-refresh every 5 seconds

### Job Controls

- **Running jobs**: Can be paused or cancelled
- **Paused jobs**: Can be resumed or cancelled
- **Completed/Failed jobs**: Can be deleted

### Viewing Job Details

Click on any job card to open the detail modal with:

- **Info**: Job configuration and statistics
- **Logs**: Real-time job logs
- **Results**: Scraped data and results

## Development

The UI is built with vanilla JavaScript for simplicity. No build process required.

To modify:

1. Edit the HTML, CSS, or JS files
2. Refresh your browser (hard refresh: Cmd+Shift+R / Ctrl+Shift+F5)

## Troubleshooting

### Cannot connect to API

- Verify the API is running: `docker-compose ps`
- Check the API is accessible: `curl http://localhost:3010/api/scraper/health`
- Check browser console for CORS errors

### Login fails

- Make sure you've registered an account first
- Check the API logs for authentication errors
- Verify the credentials are correct

### Jobs not updating

- Check browser console for errors
- Verify auto-refresh is working (check network tab)
- Try manually clicking the Refresh button

## Browser Support

- Chrome/Edge: Latest
- Firefox: Latest
- Safari: Latest

## License

Part of the 3DN Scraper project.
