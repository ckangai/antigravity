# Deployment Instructions for CitySpecialty

## Prerequisites
1. **Google Cloud Project**: You need an active GCP project.
2. **Billing Enabled**: Cloud Run and Cloud SQL require billing.
3. **gcloud CLI**: Installed and authenticated (`gcloud auth login`).
4. **Gmail App Password**: For sending emails. [Create one here](https://myaccount.google.com/apppasswords).

## Step 1: Create Google Cloud SQL Instance

```bash
# Set your project ID
gcloud config set project qwiklabs-gcp-01-d54926c33023

# Create a Cloud SQL instance (MySQL)
gcloud sql instances create city-specialty-db-instance \
    --database-version=MYSQL_8_0 \
    --cpu=1 \
    --memory=4GB \
    --region=us-central1 \
    --root-password=Summit$2026 # Remember this!

# Create the database
gcloud sql databases create city_specialty_db --instance=city-specialty-db-instance
```

## Step 1.1: Initialize Database Schema

You must run the SQL script to create the table. You can do this via Cloud Console (SQL Studio) or gcloud:

```bash
gcloud sql connect city-specialty-db-instance --user=root --quiet < db_init.sql
```
*Note: This requires the Cloud SQL Auth Proxy or running from a machine with authorized network access. Alternatively, paste the contents of `db_init.sql` into the Cloud Console's SQL Studio.*

## Step 2: Build and Deploy to Cloud Run

We will deploy directly from source, which builds the container automatically.

> [!CAUTION]
> **Check your directory!**
> You must run these commands from inside the `CitySpecialty` folder. If you are in the parent folder, the build will fail with confusing permission errors.

```bash
# Enter the project directory
cd ~/antigravity/CitySpecialty
```

```bash
# Enable necessary APIs
gcloud services enable run.googleapis.com sqladmin.googleapis.com cloudbuild.googleapis.com

# Grant Cloud Build permissions (Fix for cloudbuild.builds.get error)
# Replace [YOUR_EMAIL] with your actual email address
gcloud projects add-iam-policy-binding qwiklabs-gcp-01-d54926c33023 \
    --member="user:student-03-9b3b82513b2b@qwiklabs.net" \
    --role="roles/cloudbuild.builds.editor"

# Deploy
gcloud run deploy city-specialty-service \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars INSTANCE_CONNECTION_NAME=qwiklabs-gcp-01-d54926c33023:us-central1:city-specialty-db-instance \
    --set-env-vars DB_USER=root \
    --project qwiklabs-gcp-01-d54926c33023 \
    --set-env-vars 'DB_PASS=Summit$2026' \
    --set-env-vars DB_NAME=city_specialty_db \
    --set-env-vars "GMAIL_APP_PASSWORD=mohw pjcn ybvq nmav" \
    --set-env-vars EMAIL_USER=charles@charleskangai.co.uk \
    --set-env-vars SECRET_KEY=af11ba9019ea882bc447e292c1834521a8aa72dbcadd64e55021e26d59586858
```

**Note**: Replace all `[PLACEHOLDERS]` with your actual values.
- `ANCE_CONNECTION_NAME`: Find this in the Cloud Console SQL overview page.

## Step 2.1: Initial DB Migration (Optional but recommended)
The app is configured to create tables on startup if they don't exist. Ensure the `DB_USER` has rights to create tables.

## Step 3: Verify
- Visit the URL provided by the deployment command.
- Enter a city and specialty.
- Check your email!
