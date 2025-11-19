"""
AWS S3 Uploader Service

Handles uploading scraper job outputs to AWS S3.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from uuid import UUID

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from boto3.s3.transfer import TransferConfig

from api.config import settings


logger = logging.getLogger(__name__)


class S3UploadError(Exception):
    """Exception raised for S3 upload errors."""
    pass


class S3Uploader:
    """
    Service class for uploading scraper job outputs to AWS S3.

    Handles file uploads, directory uploads, error handling, and retries.
    Tracks uploaded files and returns S3 URLs for database storage.
    """

    def __init__(
        self,
        job_id: UUID,
        folder_name: str,
        output_path: str,
        s3_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize S3 uploader.

        Args:
            job_id: Job UUID
            folder_name: Timestamp folder name (YYYYMMDD_HHMMSS)
            output_path: Local output path
            s3_config: Optional S3 configuration override
        """
        self.job_id = str(job_id)
        self.folder_name = folder_name
        self.output_path = Path(output_path)
        self.s3_config = s3_config or {}

        # S3 configuration
        self.bucket_name = self.s3_config.get('bucket') or settings.S3_BUCKET_NAME
        self.prefix = self.s3_config.get('prefix') or settings.S3_PREFIX

        # Ensure prefix ends with /
        if self.prefix and not self.prefix.endswith('/'):
            self.prefix += '/'

        # Upload tracking
        self.uploaded_files: Dict[str, str] = {}
        self.upload_stats = {
            'files_uploaded': 0,
            'bytes_uploaded': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

        # Initialize S3 client
        self.s3_client = self._create_s3_client()

        # Transfer configuration for large files
        self.transfer_config = TransferConfig(
            multipart_threshold=1024 * 25,  # 25 MB
            max_concurrency=10,
            multipart_chunksize=1024 * 25,
            use_threads=True
        )

        logger.info(f"S3Uploader initialized for job {self.job_id}, bucket: {self.bucket_name}")

    def _create_s3_client(self):
        """Create and configure boto3 S3 client."""
        try:
            # Create S3 client with credentials
            client = boto3.client(
                's3',
                region_name=settings.S3_REGION,
                aws_access_key_id=settings.S3_ACCESS_KEY_ID,
                aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            )

            # Verify bucket exists and is accessible
            try:
                client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"Verified access to S3 bucket: {self.bucket_name}")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    raise S3UploadError(f"S3 bucket '{self.bucket_name}' does not exist")
                elif error_code == '403':
                    raise S3UploadError(f"Access denied to S3 bucket '{self.bucket_name}'")
                else:
                    raise S3UploadError(f"Error accessing bucket: {str(e)}")

            return client

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to create S3 client: {str(e)}")
            raise S3UploadError(f"Failed to initialize S3 client: {str(e)}")

    def _generate_s3_key(self, local_path: Path) -> str:
        """
        Generate S3 key from local file path.

        Args:
            local_path: Local file path

        Returns:
            S3 object key
        """
        # Get relative path from output_path
        try:
            relative_path = local_path.relative_to(self.output_path)
        except ValueError:
            # If not relative to output_path, use filename only
            relative_path = local_path.name

        # Construct S3 key: prefix/folder_name_job_id/relative_path
        full_folder_name = f"{self.folder_name}_{self.job_id}"
        s3_key = f"{self.prefix}{full_folder_name}/{relative_path}"

        # Normalize path separators to forward slashes for S3
        s3_key = s3_key.replace('\\', '/')

        return s3_key

    def _get_s3_url(self, s3_key: str) -> str:
        """
        Generate S3 URL for an object key.

        Args:
            s3_key: S3 object key

        Returns:
            S3 URL (s3:// format)
        """
        return f"s3://{self.bucket_name}/{s3_key}"

    def _get_https_url(self, s3_key: str) -> str:
        """
        Generate HTTPS URL for an object key.

        Args:
            s3_key: S3 object key

        Returns:
            HTTPS URL
        """
        return f"https://{self.bucket_name}.s3.{settings.S3_REGION}.amazonaws.com/{s3_key}"

    def upload_file(
        self,
        local_path: Path,
        s3_key: Optional[str] = None,
        extra_args: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Upload a single file to S3.

        Args:
            local_path: Path to local file
            s3_key: Optional S3 key (generated if not provided)
            extra_args: Optional extra arguments for upload

        Returns:
            S3 URL of uploaded file

        Raises:
            S3UploadError: If upload fails
        """
        if not local_path.exists():
            raise S3UploadError(f"Local file does not exist: {local_path}")

        if not local_path.is_file():
            raise S3UploadError(f"Path is not a file: {local_path}")

        # Generate S3 key if not provided
        if s3_key is None:
            s3_key = self._generate_s3_key(local_path)

        # Default extra arguments
        if extra_args is None:
            extra_args = {}

        # Set content type based on file extension
        if 'ContentType' not in extra_args:
            content_type = self._get_content_type(local_path)
            if content_type:
                extra_args['ContentType'] = content_type

        try:
            # Get file size
            file_size = local_path.stat().st_size

            logger.info(f"Uploading {local_path.name} ({file_size} bytes) to s3://{self.bucket_name}/{s3_key}")

            # Upload file
            self.s3_client.upload_file(
                str(local_path),
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args,
                Config=self.transfer_config
            )

            # Track upload
            s3_url = self._get_s3_url(s3_key)
            self.uploaded_files[str(local_path)] = s3_url
            self.upload_stats['files_uploaded'] += 1
            self.upload_stats['bytes_uploaded'] += file_size

            logger.info(f"Successfully uploaded to {s3_url}")
            return s3_url

        except ClientError as e:
            self.upload_stats['errors'] += 1
            error_msg = f"Failed to upload {local_path}: {str(e)}"
            logger.error(error_msg)
            raise S3UploadError(error_msg)

    def upload_directory(
        self,
        directory_path: Path,
        recursive: bool = True,
        pattern: str = "*"
    ) -> List[str]:
        """
        Upload all files in a directory to S3.

        Args:
            directory_path: Path to directory
            recursive: Whether to upload subdirectories
            pattern: Glob pattern for file matching

        Returns:
            List of S3 URLs for uploaded files
        """
        if not directory_path.exists():
            raise S3UploadError(f"Directory does not exist: {directory_path}")

        if not directory_path.is_dir():
            raise S3UploadError(f"Path is not a directory: {directory_path}")

        uploaded_urls = []

        # Find files
        if recursive:
            files = list(directory_path.rglob(pattern))
        else:
            files = list(directory_path.glob(pattern))

        # Filter to files only
        files = [f for f in files if f.is_file()]

        logger.info(f"Uploading {len(files)} files from {directory_path}")

        # Upload each file
        for file_path in files:
            try:
                s3_url = self.upload_file(file_path)
                uploaded_urls.append(s3_url)
            except S3UploadError as e:
                logger.warning(f"Skipping file due to error: {e}")
                continue

        return uploaded_urls

    def upload_batch(self, file_list: List[str]) -> Dict[str, str]:
        """
        Upload a batch of files specified by paths.

        Args:
            file_list: List of file paths to upload

        Returns:
            Dict mapping local paths to S3 URLs
        """
        results = {}

        for file_path_str in file_list:
            file_path = Path(file_path_str)

            if not file_path.exists():
                logger.warning(f"File not found, skipping: {file_path}")
                continue

            try:
                s3_url = self.upload_file(file_path)
                results[file_path_str] = s3_url
            except S3UploadError as e:
                logger.warning(f"Failed to upload {file_path}: {e}")
                results[file_path_str] = None

        return results

    def upload_job_outputs(self) -> Dict[str, Any]:
        """
        Upload all job output files based on configuration.

        Returns:
            Dict with upload results and S3 URLs
        """
        self.upload_stats['start_time'] = datetime.utcnow().isoformat()

        logger.info(f"Starting S3 upload for job {self.job_id}")

        results = {
            'status': 'success',
            's3_urls': {},
            'uploaded_files': [],
            'errors': []
        }

        try:
            # Get upload configuration
            include_files = self.s3_config.get('includeFiles', [
                'all_products.json',
                'categories.json',
                'results.json'
            ])
            upload_pdfs = self.s3_config.get('uploadPdfs', True)
            upload_screenshots = self.s3_config.get('uploadScreenshots', False)
            upload_categories = self.s3_config.get('uploadCategories', False)

            # Upload specific files
            for filename in include_files:
                file_path = self.output_path / filename
                if file_path.exists():
                    try:
                        s3_url = self.upload_file(file_path)
                        results['s3_urls'][filename.replace('.', '_')] = s3_url
                        results['uploaded_files'].append(filename)
                    except S3UploadError as e:
                        results['errors'].append(f"{filename}: {str(e)}")
                else:
                    logger.warning(f"File not found: {filename}")

            # Upload PDFs directory
            if upload_pdfs:
                pdfs_dir = self.output_path / 'pdfs'
                if pdfs_dir.exists():
                    try:
                        pdf_urls = self.upload_directory(pdfs_dir, recursive=True)
                        results['s3_urls']['pdfs_dir'] = self._get_s3_url(
                            self._generate_s3_key(pdfs_dir)
                        )
                        logger.info(f"Uploaded {len(pdf_urls)} PDF files")
                    except S3UploadError as e:
                        results['errors'].append(f"PDFs: {str(e)}")

            # Upload screenshots directory
            if upload_screenshots:
                screenshots_dir = self.output_path / 'screenshots'
                if screenshots_dir.exists():
                    try:
                        screenshot_urls = self.upload_directory(screenshots_dir)
                        results['s3_urls']['screenshots_dir'] = self._get_s3_url(
                            self._generate_s3_key(screenshots_dir)
                        )
                        logger.info(f"Uploaded {len(screenshot_urls)} screenshots")
                    except S3UploadError as e:
                        results['errors'].append(f"Screenshots: {str(e)}")

            # Upload category JSON files
            if upload_categories:
                categories_dir = self.output_path / 'categories'
                if categories_dir.exists():
                    try:
                        category_urls = self.upload_directory(
                            categories_dir,
                            recursive=True,
                            pattern="*.json"
                        )
                        results['s3_urls']['categories_dir'] = self._get_s3_url(
                            self._generate_s3_key(categories_dir)
                        )
                        logger.info(f"Uploaded {len(category_urls)} category files")
                    except S3UploadError as e:
                        results['errors'].append(f"Categories: {str(e)}")

            # Set status based on errors
            if results['errors']:
                results['status'] = 'partial'
                logger.warning(f"Upload completed with {len(results['errors'])} errors")
            else:
                logger.info(f"Successfully uploaded all files for job {self.job_id}")

        except Exception as e:
            results['status'] = 'failed'
            results['errors'].append(f"Upload failed: {str(e)}")
            logger.error(f"S3 upload failed for job {self.job_id}: {str(e)}")
            raise S3UploadError(f"Failed to upload job outputs: {str(e)}")

        finally:
            self.upload_stats['end_time'] = datetime.utcnow().isoformat()

        return results

    def get_upload_stats(self) -> Dict[str, Any]:
        """
        Get upload statistics.

        Returns:
            Dict with upload stats
        """
        return {
            **self.upload_stats,
            'total_files': self.upload_stats['files_uploaded'],
            'total_bytes': self.upload_stats['bytes_uploaded']
        }

    def get_s3_urls(self) -> Dict[str, str]:
        """
        Get all uploaded file S3 URLs.

        Returns:
            Dict mapping local paths to S3 URLs
        """
        return self.uploaded_files.copy()

    @staticmethod
    def _get_content_type(file_path: Path) -> Optional[str]:
        """
        Determine content type from file extension.

        Args:
            file_path: File path

        Returns:
            Content type string or None
        """
        extension = file_path.suffix.lower()

        content_types = {
            '.json': 'application/json',
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.html': 'text/html',
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
        }

        return content_types.get(extension)
