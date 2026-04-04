# Offline Document Processor

Standalone script for processing documents with Voyage AI embeddings without running the main server.

## Features

- ✅ Uses Voyage AI (10M tokens/month free tier)
- ✅ No server needed - direct database connection
- ✅ Perfect for admin testing and bulk uploads
- ✅ Shows real-time progress in terminal
- ✅ Respects Voyage's 3 RPM rate limit automatically
- ✅ Documents appear in UI immediately after processing

## Prerequisites

1. Voyage AI API key in `.env` file:
   ```
   VOYAGE_API_KEY=pa--S8iAZQSYGGGAcwUAMqQUsUlFHHckg1u5WXAPcoRrkR
   ```

2. Supabase credentials in `.env` file (already configured)

3. Python dependencies installed:
   ```bash
   pip install supabase httpx PyPDF2 python-dotenv
   ```

## Usage

### Basic Usage

```bash
python offline_document_processor.py "path/to/document.pdf" --user-id YOUR_USER_ID
```

### Example

```bash
# Process your Guyton textbook
python offline_document_processor.py "C:\Users\nayan\Downloads\Med project assets\Books\Guyton and Hall textbook of medical physiology 12th Edition_compressed.pdf" --user-id 5add0677-8c00-4e4f-a22c-f56b58f1658e
```

### With Feature Specification

```bash
# Process for specific feature (chat, mcq, flashcard, explain, highyield)
python offline_document_processor.py "document.pdf" --user-id YOUR_ID --feature mcq
```

## What It Does

1. **Extracts text** from PDF (shows progress every 50 pages)
2. **Chunks text** into ~1000 character segments with overlap
3. **Generates embeddings** using Voyage AI (1536 dims → padded to 4096)
4. **Stores in database** with proper indexing
5. **Updates progress** in real-time

## Processing Time

- **Rate limit**: 3 requests/minute (20 seconds between requests)
- **100-page PDF**: ~50 chunks = ~17 minutes
- **1000-page PDF**: ~500 chunks = ~167 minutes (2.8 hours)

The script shows estimated time remaining as it processes.

## Output Example

```
============================================================
📄 Processing Document
============================================================
File: Guyton and Hall textbook.pdf
Size: 29.62 MB
User ID: 5add0677-8c00-4e4f-a22c-f56b58f1658e

📄 Extracting text from PDF...
📊 Total pages: 1112
   Processed 50/1112 pages...
   Processed 100/1112 pages...
   ...
✅ Extracted 2,500,000 characters

✂️  Chunking text...
✅ Created 547 chunks

💾 Creating document record...
✅ Document record created: abc-123-def

🔄 Generating embeddings with Voyage AI...
   Rate limit: 3 requests/minute (20 seconds between requests)
   Estimated time: 182.3 minutes

  ✓ Chunk 1/547 (0%) - 182.3 min remaining
  ✓ Chunk 2/547 (0%) - 182.0 min remaining
  ...
  ✓ Chunk 547/547 (100%) - 0.0 min remaining

✅ Embedding generation complete!
   Generated: 547/547
   Failed: 0/547

============================================================
✅ Document processed successfully!
============================================================
Document ID: abc-123-def
Filename: Guyton and Hall textbook.pdf
Chunks: 547
Embeddings: 547

🎉 Document is now ready for search in the app!
============================================================
```

## Viewing in UI

After processing completes:

1. Go to `/documents` page
2. Document appears in your list
3. Status shows "Completed" ✅
4. Click to view chunks and embeddings
5. Use in Chat/MCQ/Explain with RAG

## Canceling

Press `Ctrl+C` to cancel processing. The document will remain in "processing" state in the database.

## Troubleshooting

### "VOYAGE_API_KEY not found"
- Add `VOYAGE_API_KEY` to your `.env` file

### "Rate limit exceeded"
- Script automatically waits 20 seconds between requests
- If you see this error, the script will retry automatically

### "Insufficient text extracted"
- PDF might be image-based or corrupted
- Try a different PDF or use OCR preprocessing

### Document not appearing in UI
- Check that `user_id` matches your logged-in user
- Refresh the documents page
- Check database for document record

## Cost

- **Voyage AI Free Tier**: 10M tokens/month
- **Average document**: 50k tokens
- **Monthly capacity**: ~200 documents
- **After free tier**: Pay per token (very affordable)

## Notes

- Main server continues using HuggingFace (unchanged)
- This script is for admin testing only
- Documents processed offline work identically to server-uploaded documents
- All embeddings are stored in 4096-dimension format (Voyage 1536 → padded)
- Vector search works seamlessly across all documents
