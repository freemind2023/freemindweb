# Credentials

This folder holds your Google Cloud service account credentials.

## Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select an existing one)
3. Enable these APIs:
   - **Google Analytics Data API** (GA4)
   - **Google Search Console API**
4. Go to **IAM & Admin > Service Accounts**
5. Create a service account
6. Download the JSON key file
7. Save it here as `service-account.json`

## Granting Access

### Google Analytics 4
- Go to GA4 Admin > Property > Property Access Management
- Add the service account email (from the JSON file) as a Viewer

### Google Search Console
- Go to Search Console > Settings > Users and permissions
- Add the service account email as a Full user

## Security

- `service-account.json` is gitignored — never commit it
- The `.example` file shows the expected format
- Keep credentials on your local machine only
