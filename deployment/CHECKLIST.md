# Deployment Checklist

Use this checklist to ensure all steps are completed for production deployment.

## Pre-Deployment

### AWS LightSail Setup
- [ ] LightSail instance created (4GB+ RAM, Ubuntu 22.04)
- [ ] Static IP attached to instance
- [ ] SSH key configured
- [ ] Instance is accessible via SSH
- [ ] Security group allows ports 22, 80, 443

### Domain Configuration
- [ ] Domain purchased and configured
- [ ] DNS A record points to LightSail static IP
- [ ] DNS propagation complete (verify with `dig` or `nslookup`)
- [ ] Domain resolves to correct IP

### AWS S3 Setup
- [ ] S3 bucket created (`agar-documentation`)
- [ ] Bucket is in correct region (`ap-southeast-2`)
- [ ] IAM user created with S3 write permissions
- [ ] Access key and secret key generated
- [ ] Test upload to bucket successful

## Server Preparation

### System Updates
- [ ] System packages updated: `sudo apt update && sudo apt upgrade -y`
- [ ] Timezone configured: `sudo timedatectl set-timezone Australia/Sydney`
- [ ] Hostname set: `sudo hostnamectl set-hostname askagar`

### Software Installation
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] Docker group membership configured
- [ ] Logged out and back in after docker group change
- [ ] Nginx installed
- [ ] Certbot installed
- [ ] Git installed

### Firewall Configuration
- [ ] UFW firewall enabled
- [ ] Port 22 (SSH) allowed
- [ ] Port 80 (HTTP) allowed
- [ ] Port 443 (HTTPS) allowed
- [ ] Other ports blocked

## Application Deployment

### Repository Setup
- [ ] Repository cloned to `~/apps/agar-scraper`
- [ ] Working directory correct
- [ ] Git configured (if pushing changes)

### Environment Configuration
- [ ] `production.env` copied to `.env`
- [ ] Secrets generated with `generate_secret.py`
- [ ] `SECRET_KEY` updated in `.env`
- [ ] `POSTGRES_PASSWORD` updated in `.env`
- [ ] `DATABASE_URL` updated with new password
- [ ] `S3_ACCESS_KEY_ID` set
- [ ] `S3_SECRET_ACCESS_KEY` set
- [ ] `S3_BUCKET_NAME` set to `agar-documentation`
- [ ] `S3_REGION` set to `ap-southeast-2`
- [ ] `CORS_ORIGINS` includes production domain(s)
- [ ] `ENVIRONMENT` set to `production`
- [ ] `DEBUG` set to `false`
- [ ] File permissions set: `chmod 600 .env`

### Docker Deployment
- [ ] Deployment script executable: `chmod +x deployment/scripts/deploy.sh`
- [ ] Deployment script run successfully
- [ ] All containers started (postgres, redis, crawl4ai, api, celery-worker, ui)
- [ ] All containers healthy (check with `docker ps`)
- [ ] No errors in logs: `docker-compose -f docker-compose.prod.yml logs`

## Web Server Configuration

### Nginx Setup
- [ ] Nginx configuration copied to `/etc/nginx/sites-available/askagar`
- [ ] Domain name updated in config if needed
- [ ] Configuration syntax valid: `sudo nginx -t`
- [ ] Site enabled: symlink created in `/etc/nginx/sites-enabled/`
- [ ] Nginx restarted: `sudo systemctl restart nginx`
- [ ] HTTP site accessible (before SSL)

### SSL Certificate
- [ ] Certbot run for domain: `sudo certbot --nginx -d askagar.com -d www.askagar.com`
- [ ] Email provided for renewal notifications
- [ ] Certificate successfully installed
- [ ] HTTPS site accessible
- [ ] HTTP redirects to HTTPS
- [ ] SSL certificate auto-renewal configured

## Application Configuration

### Admin User
- [ ] Admin user created with `create_admin.py`
- [ ] Admin login tested
- [ ] Default password changed immediately

### API Testing
- [ ] Health endpoint accessible: `https://askagar.com/api/scraper/health`
- [ ] API docs accessible: `https://askagar.com/api/scraper/docs`
- [ ] Registration endpoint works
- [ ] Login endpoint works
- [ ] Job creation endpoint works (authenticated)
- [ ] Stats endpoint works

### UI Testing
- [ ] UI accessible: `https://askagar.com`
- [ ] Login page loads
- [ ] Registration works
- [ ] Dashboard loads after login
- [ ] Job creation form works
- [ ] Job list displays
- [ ] Auto-refresh works (5 second interval)

### S3 Integration Testing
- [ ] Test job with S3 upload enabled created
- [ ] Job completes successfully
- [ ] Files uploaded to S3 bucket
- [ ] Files organized correctly with `agar/` prefix
- [ ] Files accessible in S3

## Monitoring & Maintenance

### Auto-Start Service
- [ ] Systemd service file copied: `sudo cp deployment/systemd/agar-scraper.service /etc/systemd/system/`
- [ ] Service enabled: `sudo systemctl enable agar-scraper`
- [ ] Service started: `sudo systemctl start agar-scraper`
- [ ] Service status checked: `sudo systemctl status agar-scraper`
- [ ] Test reboot and verify auto-start

### Monitoring Setup
- [ ] Monitoring script tested: `./deployment/scripts/monitor.sh`
- [ ] Monitoring added to crontab (every 5 minutes)
- [ ] Log directory created and writable
- [ ] Alert email configured (optional)

### Backup Setup
- [ ] Backup script tested: `./deployment/scripts/backup.sh`
- [ ] Backup directory created
- [ ] Daily backup added to crontab (2 AM)
- [ ] Backup retention configured (30 days)
- [ ] S3 backup upload tested (optional)
- [ ] Test restore from backup

### Log Management
- [ ] Application logs accessible: `docker-compose -f docker-compose.prod.yml logs`
- [ ] Nginx logs accessible: `tail -f /var/log/nginx/askagar_*.log`
- [ ] Log rotation configured
- [ ] Disk space monitored

## Security Hardening

### File Permissions
- [ ] `.env` file: `chmod 600 .env`
- [ ] Scripts executable but not writable by others
- [ ] Scraper data directory permissions correct
- [ ] Log directory permissions correct

### Password Security
- [ ] All default passwords changed
- [ ] Strong passwords used (from `generate_secret.py`)
- [ ] Secrets not committed to git
- [ ] `.env` in `.gitignore`

### Network Security
- [ ] Only necessary ports exposed
- [ ] Database port not exposed (internal only)
- [ ] Redis port not exposed (internal only)
- [ ] API only accessible via Nginx proxy
- [ ] Rate limiting configured in Nginx

### Application Security
- [ ] CORS properly configured
- [ ] JWT tokens properly secured
- [ ] HTTPS enforced for all traffic
- [ ] Security headers configured in Nginx
- [ ] No debug mode in production
- [ ] No sensitive data in logs

## Post-Deployment Verification

### Functional Testing
- [ ] Create test user account
- [ ] Run full scraping job on Agar website
- [ ] Verify job completes successfully
- [ ] Verify data saved locally
- [ ] Verify data uploaded to S3
- [ ] Check job stats and logs
- [ ] Test job cancellation

### Performance Testing
- [ ] Monitor resource usage during scraping
- [ ] Check memory usage: `free -h`
- [ ] Check disk usage: `df -h`
- [ ] Check CPU usage: `top` or `htop`
- [ ] Verify no memory leaks over 24 hours

### Load Testing
- [ ] Create multiple concurrent jobs
- [ ] Monitor Celery worker performance
- [ ] Check for any errors or failures
- [ ] Verify all jobs complete

## Documentation

### Internal Documentation
- [ ] Deployment notes documented
- [ ] Admin credentials stored securely
- [ ] Backup procedures documented
- [ ] Recovery procedures documented
- [ ] Monitoring alerts documented

### User Documentation
- [ ] User guide updated with production URL
- [ ] API documentation accessible
- [ ] Support contact information provided

## Final Steps

### Communication
- [ ] Stakeholders notified of deployment
- [ ] Production URL shared
- [ ] Admin credentials shared securely
- [ ] Known issues documented

### Monitoring
- [ ] First 24 hours monitored closely
- [ ] Error logs reviewed
- [ ] Performance metrics collected
- [ ] User feedback collected

## Rollback Plan

In case of issues:

1. [ ] Rollback procedure documented
2. [ ] Previous version tagged in git
3. [ ] Database backup available
4. [ ] Quick rollback tested

## Sign-Off

- [ ] All checklist items completed
- [ ] Deployment verified by technical lead
- [ ] Production approved for public use

---

**Deployment Date**: _______________

**Deployed By**: _______________

**Approved By**: _______________

**Notes**:
