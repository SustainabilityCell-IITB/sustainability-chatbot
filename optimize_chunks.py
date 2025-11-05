"""
Tool to find optimal chunk size for your document
Run this to test different chunk sizes and see statistics
"""
import config
from document_loader import load_document
from text_processor import preprocess_document
from embedder import create_embedder
import numpy as np

def analyze_chunk_size(chunk_size, overlap):
    """Analyze performance metrics for given chunk size"""
    print(f"\n{'='*60}")
    print(f"Testing CHUNK_SIZE={chunk_size}, OVERLAP={overlap}")
    print('='*60)
    
    # Load document
    text = load_document(config.DOCUMENT_PATH)
    doc_length = len(text)
    
    # Create chunks
    chunks = preprocess_document(text, chunk_size, overlap)
    num_chunks = len(chunks)
    
    # Calculate statistics
    chunk_lengths = [len(c) for c in chunks]
    avg_length = np.mean(chunk_lengths)
    min_length = np.min(chunk_lengths)
    max_length = np.max(chunk_lengths)
    
    # Sample chunks to check quality
    sample_indices = [0, num_chunks//4, num_chunks//2, 3*num_chunks//4, -1]
    
    print(f"\n📊 Statistics:")
    print(f"  Document length: {doc_length:,} characters")
    print(f"  Number of chunks: {num_chunks:,}")
    print(f"  Average chunk length: {avg_length:.1f} chars")
    print(f"  Min chunk length: {min_length} chars")
    print(f"  Max chunk length: {max_length} chars")
    print(f"  Coverage efficiency: {(num_chunks * avg_length / doc_length):.2%}")
    
    print(f"\n📝 Sample Chunks:")
    for i in sample_indices:
        chunk = chunks[i]
        preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
        print(f"  Chunk {i if i >= 0 else num_chunks+i}: ({len(chunk)} chars)")
        print(f"    {preview}")
        print()
    
    return {
        'chunk_size': chunk_size,
        'overlap': overlap,
        'num_chunks': num_chunks,
        'avg_length': avg_length,
        'coverage': num_chunks * avg_length / doc_length
    }

def recommend_chunk_size():
    """Test multiple chunk sizes and recommend the best one"""
    print("\n" + "="*60)
    print("CHUNK SIZE OPTIMIZATION TOOL")
    print("="*60)
    
    # Test different sizes
    test_configs = [
        (200, 30),   # Small chunks
        (300, 40),   # Medium-small
        (400, 50),   # Current setting
        (500, 60),   # Medium-large
        (600, 75),   # Large chunks
        (800, 100),  # Very large
    ]
    
    results = []
    for chunk_size, overlap in test_configs:
        result = analyze_chunk_size(chunk_size, overlap)
        results.append(result)
    
    # Recommendations
    print("\n" + "="*60)
    print("📊 COMPARISON & RECOMMENDATIONS")
    print("="*60)
    print(f"\n{'Size':<8} {'Overlap':<8} {'Chunks':<10} {'Avg Len':<10} {'Coverage':<10}")
    print("-" * 60)
    for r in results:
        print(f"{r['chunk_size']:<8} {r['overlap']:<8} {r['num_chunks']:<10} {r['avg_length']:<10.1f} {r['coverage']:<10.2%}")
    
    print("\n💡 RECOMMENDATIONS:")
    print("\nFor your document:")
    print("  • If retrieval is too vague → Use SMALLER chunks (300-400)")
    print("  • If responses lack context → Use LARGER chunks (500-600)")
    print("  • Current 400 is a good balanced starting point")
    print("\nOptimal overlap should be 10-15% of chunk size")
    print("\n⚠️  After changing, you need to:")
    print("  1. Update config.py")
    print("  2. Restart the server (chunks are re-embedded on startup)")
    print("  3. Test with real queries to see quality improvement")

if __name__ == "__main__":
    recommend_chunk_size()
