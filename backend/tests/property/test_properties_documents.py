"""
Property-Based Tests for Document Service
Tests universal properties related to document processing and RAG
Feature: medical-ai-platform
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import MagicMock, AsyncMock, patch
from services.documents import DocumentService
import uuid
import io


# Custom strategies for generating test data
def valid_text():
    """Generate valid text content"""
    return st.text(min_size=10, max_size=1000)


def valid_filename():
    """Generate valid filenames"""
    return st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='.-_')).map(lambda x: x + '.pdf')


def valid_query():
    """Generate valid search queries"""
    return st.text(min_size=1, max_size=200)


# Feature: medical-ai-platform, Property 15: PDF upload generates embeddings
@given(
    text_content=valid_text()
)
@settings(max_examples=100, deadline=None)  # Disable deadline due to model loading time
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_pdf_embedding_generation_property(text_content):
    """
    Property 15: For any uploaded PDF file, text extraction and embedding 
    generation should complete successfully, resulting in embeddings stored 
    in the database.
    
    Validates: Requirements 7.2
    """
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Generate test IDs
    document_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    # Mock document retrieval
    mock_doc_response = MagicMock()
    mock_doc_response.data = [{
        "id": document_id,
        "user_id": user_id,
        "filename": "test.pdf",
        "file_type": "pdf",
        "storage_path": "documents/test.pdf",
        "processing_status": "pending"
    }]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_doc_response
    
    # Mock status updates
    mock_update_response = MagicMock()
    mock_update_response.data = [{"id": document_id}]
    mock_update = MagicMock()
    mock_update.execute.return_value = mock_update_response
    mock_supabase.table.return_value.update.return_value.eq.return_value = mock_update
    
    # Mock storage download - create a simple PDF with text
    mock_pdf_content = create_mock_pdf_with_text(text_content)
    mock_supabase.storage.from_.return_value.download.return_value = mock_pdf_content
    
    # Mock embeddings insertion
    mock_embeddings_response = MagicMock()
    mock_embeddings_response.data = [{"id": str(uuid.uuid4())}]
    mock_embeddings_insert = MagicMock()
    mock_embeddings_insert.execute.return_value = mock_embeddings_response
    mock_supabase.table.return_value.insert.return_value = mock_embeddings_insert
    
    # Create document service with mock client
    doc_service = DocumentService(supabase_client=mock_supabase)
    
    # Act: Process PDF
    result = await doc_service.process_pdf(document_id)
    
    # Assert: Processing completed and embeddings were generated
    assert result is not None
    assert result["status"] == "completed"
    assert result["document_id"] == document_id
    assert result["chunks_processed"] > 0
    
    # Verify embeddings were inserted
    mock_embeddings_insert.execute.assert_called()
    
    # Verify status was updated to completed
    assert mock_update.execute.call_count >= 2  # At least processing and completed


# Feature: medical-ai-platform, Property 18: Document embeddings persist
@given(
    text_content=valid_text()
)
@settings(max_examples=100, deadline=None)  # Disable deadline due to model loading time
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_embedding_persistence_property(text_content):
    """
    Property 18: For any processed document, embeddings should be stored 
    in the embeddings table with correct document_id and vector values.
    
    Validates: Requirements 8.4
    """
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Generate test IDs
    document_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    # Mock document retrieval
    mock_doc_response = MagicMock()
    mock_doc_response.data = [{
        "id": document_id,
        "user_id": user_id,
        "filename": "test.pdf",
        "file_type": "pdf",
        "storage_path": "documents/test.pdf",
        "processing_status": "pending"
    }]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_doc_response
    
    # Mock status updates
    mock_update_response = MagicMock()
    mock_update_response.data = [{"id": document_id}]
    mock_update = MagicMock()
    mock_update.execute.return_value = mock_update_response
    mock_supabase.table.return_value.update.return_value.eq.return_value = mock_update
    
    # Mock storage download
    mock_pdf_content = create_mock_pdf_with_text(text_content)
    mock_supabase.storage.from_.return_value.download.return_value = mock_pdf_content
    
    # Track embeddings insertions
    inserted_embeddings = []
    
    def capture_embeddings(data):
        inserted_embeddings.extend(data)
        mock_response = MagicMock()
        mock_response.data = [{"id": str(uuid.uuid4())} for _ in data]
        return mock_response
    
    mock_embeddings_insert = MagicMock()
    mock_embeddings_insert.execute.side_effect = lambda: capture_embeddings(
        mock_supabase.table.return_value.insert.call_args[0][0]
    )
    mock_supabase.table.return_value.insert.return_value = mock_embeddings_insert
    
    # Create document service with mock client
    doc_service = DocumentService(supabase_client=mock_supabase)
    
    # Act: Process PDF
    result = await doc_service.process_pdf(document_id)
    
    # Assert: Embeddings were persisted with correct structure
    assert len(inserted_embeddings) > 0
    
    for embedding_data in inserted_embeddings:
        # Verify each embedding has required fields
        assert "document_id" in embedding_data
        assert embedding_data["document_id"] == document_id
        assert "chunk_text" in embedding_data
        assert "chunk_index" in embedding_data
        assert "embedding" in embedding_data
        
        # Verify embedding is a list of floats (vector)
        assert isinstance(embedding_data["embedding"], list)
        assert len(embedding_data["embedding"]) > 0
        assert all(isinstance(x, float) for x in embedding_data["embedding"])


# Feature: medical-ai-platform, Property 19: Semantic search returns relevant results
@given(
    query_text=valid_query()
)
@settings(max_examples=100, deadline=None)  # Disable deadline due to model loading time
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_semantic_search_relevance_property(query_text):
    """
    Property 19: For any semantic search query, results should be ordered 
    by similarity score (most relevant first).
    
    Validates: Requirements 8.5
    """
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Generate test IDs
    user_id = str(uuid.uuid4())
    doc_id_1 = str(uuid.uuid4())
    doc_id_2 = str(uuid.uuid4())
    
    # Mock embeddings with different similarity scores
    # Create embeddings that will have varying similarity to the query
    mock_embeddings_data = [
        {
            "id": str(uuid.uuid4()),
            "document_id": doc_id_1,
            "chunk_text": "Medical education content about cardiology",
            "chunk_index": 0,
            "embedding": [0.1] * 384  # Mock embedding vector
        },
        {
            "id": str(uuid.uuid4()),
            "document_id": doc_id_1,
            "chunk_text": "Neurology and brain function",
            "chunk_index": 1,
            "embedding": [0.5] * 384  # Different mock embedding
        },
        {
            "id": str(uuid.uuid4()),
            "document_id": doc_id_2,
            "chunk_text": "Pharmacology and drug interactions",
            "chunk_index": 0,
            "embedding": [0.3] * 384  # Another mock embedding
        }
    ]
    
    # Document info for each document ID
    document_info = {
        doc_id_1: {"filename": "cardiology.pdf", "file_type": "pdf"},
        doc_id_2: {"filename": "pharmacology.pdf", "file_type": "pdf"}
    }
    
    # Track call count for debugging
    call_count = {"documents": 0, "embeddings": 0, "doc_info": 0}
    
    # Set up table() to return different mocks based on the table name and call pattern
    def mock_table_handler(table_name):
        mock_chain = MagicMock()
        
        if table_name == "documents":
            call_count["documents"] += 1
            
            # Create a mock that can handle both patterns:
            # 1. select().eq().eq().execute() - for getting user's documents
            # 2. select().eq().execute() - for getting document info by ID
            
            # For getting user's documents (first call)
            if call_count["documents"] == 1:
                mock_response = MagicMock()
                mock_response.data = [{"id": doc_id_1}, {"id": doc_id_2}]
                mock_chain.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response
            else:
                # For subsequent calls to get document info by ID
                # We need to determine which document is being requested
                # This is tricky with mocks, so we'll make it return appropriate data
                def mock_select(*args):
                    select_mock = MagicMock()
                    
                    def mock_eq(field, value):
                        eq_mock = MagicMock()
                        # Return document info based on the document_id being queried
                        response_mock = MagicMock()
                        if value in document_info:
                            response_mock.data = [document_info[value]]
                        else:
                            response_mock.data = []
                        eq_mock.execute.return_value = response_mock
                        return eq_mock
                    
                    select_mock.eq = mock_eq
                    return select_mock
                
                mock_chain.select = mock_select
            
        elif table_name == "embeddings":
            call_count["embeddings"] += 1
            # Return embeddings data
            mock_response = MagicMock()
            mock_response.data = mock_embeddings_data
            mock_chain.select.return_value.in_.return_value.execute.return_value = mock_response
        
        return mock_chain
    
    mock_supabase.table.side_effect = mock_table_handler
    
    # Create document service with mock client
    doc_service = DocumentService(supabase_client=mock_supabase)
    
    # Act: Perform semantic search
    results = await doc_service.semantic_search(user_id, query_text, top_k=3)
    
    # Assert: Results are ordered by similarity (descending)
    assert len(results) > 0, "Semantic search should return results"
    
    # Verify results are sorted by similarity score (most relevant first)
    for i in range(len(results) - 1):
        assert results[i]["similarity_score"] >= results[i + 1]["similarity_score"], \
            "Results should be ordered by similarity score (descending)"
    
    # Verify each result has required fields
    for result in results:
        assert "chunk_text" in result
        assert "document_id" in result
        assert "similarity_score" in result
        assert isinstance(result["similarity_score"], float)
        assert -1.0 <= result["similarity_score"] <= 1.0  # Cosine similarity range is -1 to 1


# Feature: medical-ai-platform, Property 16: Upload counts tracked against quotas
@given(
    user_id=st.uuids().map(str),
    plan=st.sampled_from(['free', 'student', 'pro']),
    initial_uploads=st.integers(min_value=0, max_value=10)
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_upload_counts_tracked_property(user_id, plan, initial_uploads):
    """
    Property 16: For any PDF or image upload, the corresponding counter 
    (pdf_uploads or images_used) should be incremented for the user.
    
    Validates: Requirements 7.6
    """
    from services.rate_limiter import RateLimiter
    from datetime import date
    
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    today = str(date.today())
    
    # Mock user table response
    user_data = {
        "plan": plan,
        "role": None
    }
    mock_user_response = MagicMock()
    mock_user_response.data = [user_data]
    
    # Initial usage data
    initial_usage = {
        'id': 'usage-id-123',
        'user_id': user_id,
        'date': today,
        'tokens_used': 100,
        'requests_count': 5,
        'pdf_uploads': initial_uploads,
        'mcqs_generated': 3,
        'images_used': 1,
        'flashcards_generated': 4,
    }
    
    # Mock existing usage counter
    mock_usage_response = MagicMock()
    mock_usage_response.data = [initial_usage.copy()]
    
    # Mock update response
    mock_update_response = MagicMock()
    mock_update_response.data = [{'id': 'usage-id-123'}]
    
    # Track what update was called with
    update_data_captured = {}
    
    def mock_table_operations(table_name):
        mock_table = MagicMock()
        
        if table_name == "users":
            # Mock select chain for users
            mock_select = MagicMock()
            mock_eq = MagicMock()
            mock_eq.execute.return_value = mock_user_response
            mock_select.eq.return_value = mock_eq
            mock_table.select.return_value = mock_select
        elif table_name == "usage_counters":
            # Mock select chain
            mock_select = MagicMock()
            mock_eq1 = MagicMock()
            mock_eq2 = MagicMock()
            mock_eq2.execute.return_value = mock_usage_response
            mock_eq1.eq.return_value = mock_eq2
            mock_select.eq.return_value = mock_eq1
            mock_table.select.return_value = mock_select
            
            # Mock update chain
            def capture_update(data):
                update_data_captured.update(data)
                mock_update = MagicMock()
                mock_eq_update = MagicMock()
                mock_eq_update.execute.return_value = mock_update_response
                mock_update.eq.return_value = mock_eq_update
                return mock_update
            
            mock_table.update.side_effect = capture_update
        
        return mock_table
    
    mock_supabase.table.side_effect = mock_table_operations
    
    # Create rate limiter with mock client
    rate_limiter = RateLimiter(supabase_client=mock_supabase)
    
    # Act: Simulate PDF upload by incrementing usage with 'pdf' feature
    await rate_limiter.increment_usage(user_id, tokens=0, feature='pdf')
    
    # Assert: PDF upload counter should be incremented
    assert 'pdf_uploads' in update_data_captured, \
        "pdf_uploads counter should be updated when feature='pdf'"
    
    assert update_data_captured['pdf_uploads'] == initial_uploads + 1, \
        f"pdf_uploads should be incremented by 1. Expected: {initial_uploads + 1}, Got: {update_data_captured['pdf_uploads']}"
    
    # Property: requests_count should also be incremented
    assert 'requests_count' in update_data_captured, \
        "requests_count should be updated"
    assert update_data_captured['requests_count'] == initial_usage['requests_count'] + 1, \
        "requests_count should be incremented by 1"
    
    # Reset for image upload test
    update_data_captured.clear()
    mock_usage_response.data = [initial_usage.copy()]
    
    # Act: Simulate image upload by incrementing usage with 'image' feature
    await rate_limiter.increment_usage(user_id, tokens=0, feature='image')
    
    # Assert: Image upload counter should be incremented
    assert 'images_used' in update_data_captured, \
        "images_used counter should be updated when feature='image'"
    
    assert update_data_captured['images_used'] == initial_usage['images_used'] + 1, \
        f"images_used should be incremented by 1. Expected: {initial_usage['images_used'] + 1}, Got: {update_data_captured['images_used']}"


# Feature: medical-ai-platform, Property 17: RAG responses include citations
@given(
    query_text=valid_query()
)
@settings(max_examples=100, deadline=None)  # Disable deadline due to model loading time
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_rag_citations_property(query_text):
    """
    Property 17: For any chat response that uses RAG with user documents, 
    the response should include citations referencing the source documents.
    
    Validates: Requirements 8.3
    """
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Generate test IDs
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    
    # Mock session verification
    mock_session_response = MagicMock()
    mock_session_response.data = [{"id": session_id, "user_id": user_id}]
    
    # Mock user message insertion
    mock_user_msg_response = MagicMock()
    mock_user_msg_response.data = [{"id": str(uuid.uuid4()), "session_id": session_id}]
    
    # Mock user documents (has completed documents)
    mock_docs_response = MagicMock()
    mock_docs_response.data = [{
        "id": doc_id,
        "user_id": user_id,
        "filename": "medical_notes.pdf",
        "processing_status": "completed"
    }]
    
    # Mock semantic search results
    mock_search_results = [
        {
            "chunk_text": "Medical concept about cardiology",
            "document_id": doc_id,
            "document_filename": "medical_notes.pdf",
            "chunk_index": 0,
            "similarity_score": 0.85
        },
        {
            "chunk_text": "Additional medical information",
            "document_id": doc_id,
            "document_filename": "medical_notes.pdf",
            "chunk_index": 1,
            "similarity_score": 0.75
        }
    ]
    
    # Mock AI response
    mock_ai_response = MagicMock()
    mock_ai_response.data = [{
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": "assistant",
        "content": "Based on the sources, here's the answer [Source 1]",
        "citations": {
            "sources": [
                {
                    "source_number": 1,
                    "document_id": doc_id,
                    "document_filename": "medical_notes.pdf",
                    "chunk_index": 0,
                    "similarity_score": 0.85
                }
            ]
        }
    }]
    
    # Mock session update
    mock_session_update = MagicMock()
    mock_session_update.data = [{"id": session_id}]
    
    # Track table calls
    call_count = {"chat_sessions": 0, "messages": 0, "documents": 0}
    
    def mock_table_handler(table_name):
        mock_chain = MagicMock()
        
        if table_name == "chat_sessions":
            call_count["chat_sessions"] += 1
            if call_count["chat_sessions"] == 1:
                # First call: session verification
                mock_chain.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_session_response
            else:
                # Subsequent calls: session update
                mock_chain.update.return_value.eq.return_value.execute.return_value = mock_session_update
        
        elif table_name == "messages":
            call_count["messages"] += 1
            if call_count["messages"] == 1:
                # First call: user message insertion
                mock_chain.insert.return_value.execute.return_value = mock_user_msg_response
            else:
                # Second call: AI message insertion
                mock_chain.insert.return_value.execute.return_value = mock_ai_response
        
        elif table_name == "documents":
            # Get user documents
            mock_chain.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_docs_response
        
        return mock_chain
    
    mock_supabase.table.side_effect = mock_table_handler
    
    # Mock document service methods
    from services.documents import DocumentService
    with patch.object(DocumentService, 'get_user_documents', new_callable=AsyncMock) as mock_get_docs, \
         patch.object(DocumentService, 'semantic_search', new_callable=AsyncMock) as mock_search:
        
        mock_get_docs.return_value = mock_docs_response.data
        mock_search.return_value = mock_search_results
        
        # Mock model router
        from services.model_router import ModelRouterService
        with patch.object(ModelRouterService, 'select_provider', new_callable=AsyncMock) as mock_select, \
             patch.object(ModelRouterService, 'execute_with_fallback', new_callable=AsyncMock) as mock_execute:
            
            mock_select.return_value = "gemini"
            mock_execute.return_value = {
                "success": True,
                "content": "Based on the sources, here's the answer [Source 1]",
                "tokens_used": 100
            }
            
            # Mock rate limiter
            from services.rate_limiter import RateLimiter
            with patch.object(RateLimiter, 'increment_usage', new_callable=AsyncMock):
                
                # Create chat service with mock client
                from services.chat import ChatService
                chat_service = ChatService(supabase_client=mock_supabase)
                
                # Act: Send message (should trigger RAG)
                result = await chat_service.send_message(
                    user_id=user_id,
                    session_id=session_id,
                    message=query_text,
                    generate_response=True
                )
                
                # Assert: Response should include citations
                assert result is not None
                assert "citations" in result
                assert result["citations"] is not None
                
                # Verify citations structure
                citations = result["citations"]
                assert "sources" in citations
                assert len(citations["sources"]) > 0
                
                # Verify each citation has required fields
                for source in citations["sources"]:
                    assert "source_number" in source
                    assert "document_id" in source
                    assert "document_filename" in source
                    assert "chunk_index" in source
                    assert "similarity_score" in source
                
                # Verify semantic search was called
                mock_search.assert_called_once()


def create_mock_pdf_with_text(text: str) -> bytes:
    """
    Create a mock PDF file with the given text content
    
    Args:
        text: Text content to include in the PDF
        
    Returns:
        Bytes representing a PDF file
    """
    import PyPDF2
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    # Create a PDF in memory
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Add text to PDF (simple approach - split into lines)
    y_position = 750
    for line in text.split('\n'):
        if y_position < 50:
            c.showPage()
            y_position = 750
        c.drawString(50, y_position, line[:80])  # Limit line length
        y_position -= 15
    
    c.save()
    buffer.seek(0)
    
    return buffer.read()
