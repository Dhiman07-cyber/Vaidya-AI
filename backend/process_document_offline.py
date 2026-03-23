"""
Offline Document Processor
Processes PDF documents and uploads to database without needing the server running.
Perfect for admin testing and bulk document uploads.

Usage:
    python process_document_offline.py "path/to/document.pdf" --user-id YOUR_USER_ID
    python process_document_offline.py "path/to/document.pdf" --user-id YOUR_USER_ID --feature chat
"""
import os
import sys
import argparse
import asyncio
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import PyPDF2
from supabase import create_client

# Load environment variables
load_dotenv()

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{text}{Colors.END}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_progress(text):
    print(f"{Colors.YELLOW}⏳ {text}{Colors.END}", end='\r')


class OfflineDocumentProcessor:
    """Processes documents offline and uploads to database"""
    
    def __init__(self):
        """Initialize processor with database connection"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            raise Exception("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        
        self.supabase = create_client(supabase_url, supabase_key)
        self.voyage_provider = None
        self._init_voyage()
    
    def _init_voyage(self):
        """Initialize Voyage AI provider"""
        try:
            from services.providers.voyage import get_voyage_provider
            self.voyage_provider = get_voyage_provider()
            print_success("Voyage AI provider initialized")
        except Exception as e:
            print_error(f"Failed to initialize Voyage provider: {str(e)}")
            sys.exit(1)
    
    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        print_info(f"Extracting text from PDF...")
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                print_info(f"Total pages: {total_pages}")
                
                text = ""
                for i, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
                        
                        if (i + 1) % 50 == 0:
                            print_progress(f"Extracted {i + 1}/{total_pages} pages...")
                    except Exception as e:
                        print_error(f"Failed to extract page {i + 1}: {str(e)}")
                        continue
                
                print_success(f"Extracted {len(text)} characters from {total_pages} pages")
                return text.strip()
                
        except Exception as e:
            print_error(f"PDF extraction failed: {str(e)}")
            sys.exit(1)
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        """Split text into overlapping chunks"""
        print_info("Chunking text...")
        
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
        
        print_success(f"Created {len(chunks)} chunks")
        return chunks
    
    def pad_embedding_to_4096(self, embedding: list, original_dim: int) -> list:
        """Pad embedding to 4096 dimensions with zeros"""
        if len(embedding) >= 4096:
            return embedding[:4096]
        
        padded = embedding + [0.0] * (4096 - len(embedding))
        return padded
    
    async def generate_embeddings(self, chunks: list) -> list:
        """Generate embeddings for all chunks using Voyage AI"""
        print_header("Generating Embeddings with Voyage AI")
        print_info(f"Processing {len(chunks)} chunks (3 requests/minute rate limit)")
        print_info("This will take approximately {:.1f} minutes".format(len(chunks) / 3))
        
        api_key = os.getenv("VOYAGE_API_KEY")
        if not api_key:
            print_error("VOYAGE_API_KEY not found in .env")
            sys.exit(1)
        
        embeddings = []
        success_count = 0
        fail_count = 0
        
        for i, chunk in enumerate(chunks):
            try:
                # Generate embedding
                result = await self.voyage_provider.generate_embedding(
                    chunk,
                    api_key=api_key,
                    model="voyage-large-2"
                )
                
                if result["success"]:
                    # Pad to 4096 dimensions
                    padded = self.pad_embedding_to_4096(result["embedding"], result["dimension"])
                    embeddings.append(padded)
                    success_count += 1
                    
                    # Calculate progress and ETA
                    progress = ((i + 1) / len(chunks)) * 100
                    remaining = len(chunks) - (i + 1)
                    eta_seconds = remaining * 20  # 20 seconds per request (3 RPM)
                    eta_minutes = eta_seconds / 60
                    
                    print_progress(f"✓ Chunk {i + 1}/{len(chunks)} ({progress:.1f}%) - ETA: {eta_minutes:.1f} min")
                    
                    # Rate limiting: 3 requests per minute = 20 seconds between requests
                    if i < len(chunks) - 1:  # Don't wait after last chunk
                        await asyncio.sleep(20)
                else:
                    print_error(f"\nFailed chunk {i + 1}: {result.get('error')}")
                    embeddings.append(None)
                    fail_count += 1
                    
                    # If rate limited, wait longer
                    if "rate limit" in result.get('error', '').lower():
                        print_info("Rate limit hit, waiting 60 seconds...")
                        await asyncio.sleep(60)
                    
            except Exception as e:
                print_error(f"\nException on chunk {i + 1}: {str(e)}")
                embeddings.append(None)
                fail_count += 1
        
        print()  # New line after progress
        print_success(f"Embeddings complete: {success_count} success, {fail_count} failed")
        return embeddings
    
    def create_document_record(self, user_id: str, filename: str, file_size: int, feature: str) -> dict:
        """Create document record in database"""
        print_info("Creating document record...")
        
        try:
            # Calculate retention days (default 30 for admin testing)
            expires_at = datetime.now() + timedelta(days=30)
            
            document_data = {
                "user_id": user_id,
                "filename": filename,
                "file_type": "application/pdf",
                "file_size": file_size,
                "storage_path": f"offline/{uuid.uuid4()}.pdf",  # Placeholder
                "processing_status": "processing",
                "processing_progress": 0,
                "processing_stage": "Generating embeddings...",
                "feature": feature,
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("documents").insert(document_data).execute()
            
            if not result.data:
                raise Exception("Failed to create document record")
            
            document = result.data[0]
            print_success(f"Document record created: {document['id']}")
            return document
            
        except Exception as e:
            print_error(f"Failed to create document record: {str(e)}")
            sys.exit(1)
    
    def store_chunks_with_embeddings(self, document_id: str, chunks: list, embeddings: list):
        """Store chunks with embeddings in database"""
        print_header("Storing Chunks in Database")
        
        stored_count = 0
        failed_count = 0
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            try:
                # Update progress
                if i % 10 == 0:
                    progress = 50 + int((i / len(chunks)) * 45)  # 50-95%
                    self.supabase.table("documents").update({
                        "processing_progress": progress,
                        "processing_stage": f"Storing chunks ({i + 1}/{len(chunks)})..."
                    }).eq("id", document_id).execute()
                
                # Prepare chunk data
                embedding_str = None
                embedding_part1_str = None
                embedding_part2_str = None
                embedding_part3_str = None
                
                if embedding:
                    # Convert to PostgreSQL vector format
                    embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
                    
                    # Split into three parts for indexing
                    part1 = embedding[:1365]
                    part2 = embedding[1365:2730]
                    part3 = embedding[2730:]
                    embedding_part1_str = '[' + ','.join(str(x) for x in part1) + ']'
                    embedding_part2_str = '[' + ','.join(str(x) for x in part2) + ']'
                    embedding_part3_str = '[' + ','.join(str(x) for x in part3) + ']'
                
                chunk_data = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "content": chunk,
                    "embedding": embedding_str,
                    "embedding_part1": embedding_part1_str,
                    "embedding_part2": embedding_part2_str,
                    "embedding_part3": embedding_part3_str,
                    "created_at": datetime.now().isoformat()
                }
                
                self.supabase.table("document_chunks").insert(chunk_data).execute()
                stored_count += 1
                
                print_progress(f"Stored {i + 1}/{len(chunks)} chunks...")
                
            except Exception as e:
                print_error(f"\nFailed to store chunk {i}: {str(e)}")
                failed_count += 1
        
        print()  # New line
        print_success(f"Stored {stored_count} chunks, {failed_count} failed")
        
        # Update document status
        self.supabase.table("documents").update({
            "processing_status": "completed",
            "processing_progress": 100,
            "processing_stage": "Completed",
            "processed_at": datetime.now().isoformat(),
            "total_chunks": len(chunks),
            "chunks_with_embeddings": stored_count
        }).eq("id", document_id).execute()
    
    async def process_document(self, pdf_path: str, user_id: str, feature: str = "chat"):
        """Main processing function"""
        print_header("📄 Offline Document Processor")
        print_info(f"File: {pdf_path}")
        print_info(f"User ID: {user_id}")
        print_info(f"Feature: {feature}")
        
        # Validate file
        if not os.path.exists(pdf_path):
            print_error(f"File not found: {pdf_path}")
            sys.exit(1)
        
        filename = os.path.basename(pdf_path)
        file_size = os.path.getsize(pdf_path)
        print_info(f"File size: {file_size / (1024 * 1024):.2f} MB")
        
        # Step 1: Extract text
        print_header("Step 1: Extract Text")
        text = self.extract_pdf_text(pdf_path)
        
        if not text or len(text) < 100:
            print_error("Insufficient text extracted from PDF")
            sys.exit(1)
        
        # Step 2: Chunk text
        print_header("Step 2: Chunk Text")
        chunks = self.chunk_text(text)
        
        # Step 3: Create document record
        print_header("Step 3: Create Document Record")
        document = self.create_document_record(user_id, filename, file_size, feature)
        document_id = document["id"]
        
        # Step 4: Generate embeddings
        embeddings = await self.generate_embeddings(chunks)
        
        # Step 5: Store in database
        self.store_chunks_with_embeddings(document_id, chunks, embeddings)
        
        # Final summary
        print_header("✅ Processing Complete!")
        print_success(f"Document ID: {document_id}")
        print_success(f"Total chunks: {len(chunks)}")
        print_success(f"Embeddings: {sum(1 for e in embeddings if e is not None)}")
        print_info("\n📱 Document is now available in the UI!")
        print_info(f"   - View at: /documents")
        print_info(f"   - Use in: Chat, MCQ, Explain, High-Yield")
        print_info(f"   - RAG search: Fully functional")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Process PDF documents offline and upload to database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python process_document_offline.py "document.pdf" --user-id abc-123
  python process_document_offline.py "C:\\Books\\Guyton.pdf" --user-id abc-123 --feature chat
        """
    )
    
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--user-id", required=True, help="User ID (UUID)")
    parser.add_argument("--feature", default="chat", choices=["chat", "mcq", "flashcard", "explain", "highyield"],
                       help="Feature to enable RAG for (default: chat)")
    
    args = parser.parse_args()
    
    try:
        processor = OfflineDocumentProcessor()
        await processor.process_document(args.pdf_path, args.user_id, args.feature)
    except KeyboardInterrupt:
        print_error("\n\nProcessing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nFatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
