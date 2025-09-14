# JSONBin Setup Instructions

This application uses JSONBin.io to store and manage personifications data. Follow these steps to set it up:

## 1. Create a JSONBin Account

1. Go to [JSONBin.io](https://jsonbin.io/)
2. Sign up for a free account
3. Get your API key from the dashboard

## 2. Create a Bin

1. Create a new bin with the following initial structure:

```json
{
  "choice": null,
  "personifications": []
}
```

2. Copy the Bin ID from the URL (it will look like: `64f8a9b2b89b1e2345678901`)

## 3. Set Environment Variables

Create a `.env.local` file in the frontend directory with:

```env
JSONBIN_API_KEY=your_actual_api_key_here
JSONBIN_BIN_ID=your_actual_bin_id_here
```

## 4. Data Structure

The JSONBin should contain:

- `choice`: The ID of the currently active personification (string or null)
- `personifications`: Array of personification objects

Each personification object should have the structure defined in `types/personification.ts`.

## 5. Migration from Mock Data

If you want to migrate your existing mock data to JSONBin:

1. Copy the data from `src/lib/mock-data.ts`
2. Update your bin with:

```json
{
  "choice": null,
  "personifications": [
    /* paste your mock data here */
  ]
}
```

## API Endpoints

The application provides these API endpoints:

- `GET /api/personifications` - Fetch all personifications and active choice
- `POST /api/personifications/active` - Update the active personification choice
