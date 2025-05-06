# US Census Data Scraper

A Python-based tool for downloading TIGER shapefiles and scraping US Census QuickFacts data. This project automates the collection of geographical and demographic data from the US Census Bureau.

## Features

- Downloads TIGER shapefiles for states, counties, and places
- Scrapes QuickFacts data for geographical entities with population over 5000
- Supports concurrent downloads and API requests
- Stores data in S3-compatible storage
- Handles rate limiting and retries for robust data collection

## Requirements

- Python 3.13+
- S3-compatible storage (AWS S3 or compatible alternative)
- Environment variables configuration

## Installation

1. Clone the repository
2. Install dependencies using Poetry:

```bash
poetry install
```

## Configuration

Create a `.env` file in the root directory with the following variables:

```env
S3_BUCKET=your-bucket-name
S3_ENDPOINT=your-s3-endpoint  # Optional, for S3-compatible storage
AWS_REGION=us-east-1  # Default region
DL_CONCURRENCY=5  # Concurrent downloads
SCRAPE_SEARCH_CONCURRENCY=10  # Concurrent QuickFacts searches
```

## Architecture

### Core Components

1. **TIGER File Downloader** (`tiger_dl.py`)

   - Downloads geographical data files from Census TIGER database
   - Supports state, county, CBSA, and place shapefiles
   - Uses concurrent downloads for efficiency

2. **QuickFacts Scraper** (`scrape_search.py`)

   - Searches and scrapes demographic data from Census QuickFacts
   - Handles pagination and rate limiting
   - Caches results to avoid redundant requests

3. **QuickFacts Downloader** (`quickfacts_dl.py`)
   - Downloads detailed QuickFacts CSV files
   - Processes up to 6 geographies per request
   - Cleans and validates downloaded data

### Data Models

1. **GeoInfo**

   - Represents geographical entities
   - Contains GEOID, ID (slug used by quickfacts), label, and level information

2. **SearchQuery**

   - Handles different types of geographical searches
   - Supports state, county, and place queries

3. **TigerPaths**
   - Manages paths for different TIGER file types
   - Handles dynamic file discovery and organization

## Usage

Run the main script to start the data collection process:

```bash
python app/main.py
```

The script will:

1. Download TIGER files
2. Scrape QuickFacts search results
3. Download detailed QuickFacts data
4. Store all data in the configured S3 bucket

## Error Handling

- Implements exponential backoff for API requests
- Validates downloaded data integrity
- Caches successful results to resume interrupted operations
- Logs warnings for missing or invalid data

## Performance Optimization

- Concurrent downloads with configurable limits
- Caching of search results
- Efficient S3 operations
- Batched QuickFacts requests

## Dependencies

- httpx: HTTP client for async requests
- pydantic: Data validation and settings management
- boto3: AWS S3 client
- tenacity: Retry handling
- dbfread: DBF file parsing
- beautifulsoup4: HTML parsing
- certifi: SSL certificates
