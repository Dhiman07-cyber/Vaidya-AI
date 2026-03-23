"""
Offline Document Processor with Voyage AI
Standalone script for processing documents without running the main server
Perfect for admin testing and bulk uploads with generous free tier

Usage:
    python offline_document_processor.py "path/to/document.pdf" --user-id YOUR_USER_ID
    
Features:
    - Uses Voyage AI (10M tokens/month free)
    - Processes documents independently
    - Direct database connection
    - Shows progress in terminal
    - No server needed
"""

import os
import sys
import asyncio
import argparse
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import PyPDF2
from dotenv import load_dotenv
from supabase import create_client
import httpx

# Load environment variables
load_dotenv()

class OfflineDocumentProcessor:
    """Standalone document processor using Voyage AI"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.voyage_api_key = os.getenv("VOYAGE_API_KEY")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.voyage_api_key:
            raise ValueError("VOYAGE_API_KEY not found in .env file")
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found in .env file")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.voyage_url = "https://api.voyageai.com/v1/embeddings"
        
    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        print(f"\n📄 Extracting text from PDF...")
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            print(f"📊 Total pages: {total_pages}")
            
            text = ""
            for i, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                    
                    # Show progress every 50 pages
                    if (i + 1) % 50 == 0:
                        print(f"   Processed {i + 1}/{total_pages} pages...")
                except Exception as e:
                    print(f"   ⚠️  Warning: Failed to extract page {i + 1}: {str(e)}")
                    continue
            
            print(f"✅ Extracted {len(text)} characters")
            return text.strip()
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        """Split text into overlapping chunks"""
        print(f"\n✂️  Chunking text...")
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < text_length:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size * 0.5:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        # Filter out tiny chunks
        chunks = [c for c in chunks if len(c.strip()) > 50]
        print(f"✅ Created {len(chunks)} chunks")
        
        return chunks
    
    async def generate_voyage_embedding(self, text: str) -> dict:
        """Generate embedding using Voyage AI"""
        headers = {
            "Authorization": f"Bearer {self.voyage_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": text,
            "model": "voyage-large-2"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.voyage_url, headers=headers, json=payload)
            
            if response.status_code == 429:
                # Rate limit hit - wait 20 seconds
                return {"success": False, "error": "rate_limit", "retry_after": 20}
            
            if response.status_code != 200:
                return {"success": False, "error": f"API error: {response.status_code}"}
            
            result = response.json()
            if "data" in result and len(result["data"]) > 0:
                embedding = result["data"][0]["embedding"]
                return {"success": True, "embedding": embedding, "dimension": len(embedding)}
            
            return {"success": False, "error": "Invalid response format"}
    
    def pad_embedding_to_4096(self, embedding: list) -> list:
        """Pad embedding from 1536 to 4096 dimensions"""
        if len(embedding) >= 4096:
            return embedding[:4096]
        
        # Pad with zeros
        return embedding + [0.0] * (4096 - len(embedding))
    
    async def process_document(self, pdf_path: str, feature: str = "chat"):
        """Process document and store in database"""
        
        # Validate file
        if not os.path.exists(pdf_path):
            print(f"❌ Error: File not found: {pdf_path}")
            return
        
        file_path = Path(pdf_path)
        filename = file_path.name
        file_size = file_path.stat().st_size
        
        print(f"\n{'='*60}")
        print(f"📄 Processing Document")
        print(f"{'='*60}")
        print(f"File: {filename}")
        print(f"Size: {file_size / (1024*1024):.2f} MB")
        print(f"User ID: {self.user_id}")
        
        # Extract text
        text = self.extract_pdf_text(pdf_path)
        
        if not text or len(text) < 100:
            print(f"❌ Error: Insufficient text extracted from PDF")
            return
        
        # Chunk text
        chunks = self.chunk_text(text)
        
        # Create document record
        print(f"\n💾 Creating document record...")
        document_id = str(uuid.uuid4())
        
        # Calculate retention days (default 30 for admin)
        expires_at = datetime.now() + timedelta(days=365)  # 1 year for admin
        
        document_data = {
            "id": document_id,
            "user_id": self.user_id,
            "filename": filename,
            "file_type": "application/pdf",
            "file_size": file_size,
            "storage_path": f"offline/{self.user_id}/{document_id}.pdf",
            "processing_status": "processing",
            "processing_progress": 0,
            "processing_stage": "Generating embeddings...",
            "feature": feature,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now().isoformat(),
            "total_chunks": len(chunks),
            "chunks_with_embeddings": 0
        }
        
        self.supabase.table("documents").insert(document_data).execute()
        print(f"✅ Document record created: {document_id}")
        
        # Process chunks with embeddings
        print(f"\n🔄 Generating embeddings with Voyage AI...")
        print(f"   Rate limit: 3 requests/minute (20 seconds between requests)")
        print(f"   Estimated time: {len(chunks) * 20 / 60:.1f} minutes\n")
        
        embeddings_generated = 0
        embeddings_failed = 0
        
        for i, chunk in enumerate(chunks):
            # Show progress
            progress = int((i / len(chunks)) * 100)
            remaining_chunks = len(chunks) - i
            remaining_seconds = remaining_chunks * 20
            remaining_minutes = remaining_seconds / 60
            
            print(f"  ✓ Chunk {i+1}/{len(chunks)} ({progress}%) - {remaining_minutes:.1f} min remaining", end='\r')
            
            # Generate embedding
            result = await self.generate_voyage_embedding(chunk)
            
            if result["success"]:
                # Pad to 4096 dimensions
                embedding_1536 = result["embedding"]
                embedding_4096 = self.pad_embedding_to_4096(embedding_1536)
                
                # Split into 3 parts for indexing
                part1 = embedding_4096[:1365]
                part2 = embedding_4096[1365:2730]
                part3 = embedding_4096[2730:]
                
                # Format as PostgreSQL vectors
                embedding_str = '[' + ','.join(str(x) for x in embedding_4096) + ']'
                part1_str = '[' + ','.join(str(x) for x in part1) + ']'
                part2_str = '[' + ','.join(str(x) for x in part2) + ']'
                part3_str = '[' + ','.join(str(x) for x in part3) + ']'
                
                # Store chunk
                chunk_data = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "content": chunk,
                    "embedding": embedding_str,
                    "embedding_part1": part1_str,
                    "embedding_part2": part2_str,
                    "embedding_part3": part3_str,
                    "created_at": datetime.now().isoformat()
                }
                
                self.supabase.table("document_chunks").insert(chunk_data).execute()
                embeddings_generated += 1
                
                # Update progress every 10 chunks
                if (i + 1) % 10 == 0:
                    self.supabase.table("documents").update({
                        "processing_progress": progress,
                        "chunks_with_embeddings": embeddings_generated
                    }).eq("id", document_id).execute()
                
                # Wait 20 seconds to respect rate limit (3 RPM)
                if i < len(chunks) - 1:  # Don't wait after last chunk
                    await asyncio.sleep(20)
                
            elif result.get("error") == "rate_limit":
                # Rate limit hit - wait and retry
                print(f"\n   ⚠️  Rate limit hit, waiting {result['retry_after']} seconds...")
                await asyncio.sleep(result["retry_after"])
                
                # Retry this chunk
                result = await self.generate_voyage_embedding(chunk)
                if result["success"]:
                    # Process successful retry (same code as above)
                    embedding_1536 = result["embedding"]
                    embedding_4096 = self.pad_embedding_to_4096(embedding_1536)
                    part1 = embedding_4096[:1365]
                    part2 = embedding_4096[1365:2730]
                    part3 = embedding_4096[2730:]
                    embedding_str = '[' + ','.join(str(x) for x in embedding_4096) + ']'
                    part1_str = '[' + ','.join(str(x) for x in part1) + ']'
                    part2_str = '[' + ','.join(str(x) for x in part2) + ']'
                    part3_str = '[' + ','.join(str(x) for x in part3) + ']'
                    chunk_data = {
                        "document_id": document_id,
                        "chunk_index": i,
                        "content": chunk,
                        "embedding": embedding_str,
                        "embedding_part1": part1_str,
                        "embedding_part2": part2_str,
                        "embedding_part3": part3_str,
                        "created_at": datetime.now().isoformat()
                    }
                    self.supabase.table("document_chunks").insert(chunk_data).execute()
                    embeddings_generated += 1
                else:
                    embeddings_failed += 1
            else:
                embeddings_failed += 1
                print(f"\n   ❌ Failed to generate embedding for chunk {i+1}: {result.get('error')}")
        
        # Final update
        print(f"\n\n✅ Embedding generation complete!")
        print(f"   Generated: {embeddings_generated}/{len(chunks)}")
        print(f"   Failed: {embeddings_failed}/{len(chunks)}")
        
        # Mark document as completed
        self.supabase.table("documents").update({
            "processing_status": "completed",
            "processing_progress": 100,
            "processing_stage": "Completed",
            "processed_at": datetime.now().isoformat(),
            "chunks_with_embeddings": embeddings_generated
        }).eq("id", document_id).execute()
        
        print(f"\n{'='*60}")
        print(f"✅ Document processed successfully!")
        print(f"{'='*60}")
        print(f"Document ID: {document_id}")
        print(f"Filename: {filename}")
        print(f"Chunks: {len(chunks)}")
        print(f"Embeddings: {embeddings_generated}")
        print(f"\n🎉 Document is now ready for search in the app!")
        print(f"{'='*60}\n")


async def main():
    parser = argparse.ArgumentParser(description='Offline Document Processor with Voyage AI')
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('--user-id', required=True, help='User ID for document ownership')
    parser.add_argument('--feature', default='chat', help='Feature to enable RAG for (default: chat)')
    
    args = parser.parse_args()
    
    try:
        processor = OfflineDocumentProcessor(args.user_id)
        await processor.process_document(args.pdf_path, args.feature)
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
