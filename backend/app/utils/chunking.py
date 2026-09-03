from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class Chunk:
    content: str
    metadata: Dict[str, Any]
    chunk_index: int
    start_char: int
    end_char: int


class DocumentChunker:
    """Advanced document chunking with multiple strategies."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        strategy: str = "recursive"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy
    
    def chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Main entry point for chunking."""
        if self.strategy == "recursive":
            return self._recursive_chunk(text, metadata)
        elif self.strategy == "semantic":
            return self._semantic_chunk(text, metadata)
        elif self.strategy == "sentence":
            return self._sentence_chunk(text, metadata)
        else:
            return self._recursive_chunk(text, metadata)
    
    def _recursive_chunk(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Recursive character-based chunking (similar to LangChain)."""
        separators = ["\n\n", "\n", ". ", " ", ""]
        chunks = []
        
        def _split_recursive(text: str, separators: List[str]) -> List[str]:
            if len(text) <= self.chunk_size:
                return [text]
            
            for sep in separators:
                if sep == "":
                    # Final fallback: hard split
                    return [
                        text[i:i + self.chunk_size]
                        for i in range(0, len(text), self.chunk_size - self.chunk_overlap)
                    ]
                
                parts = text.split(sep)
                if len(parts) > 1:
                    result = []
                    current_chunk = []
                    current_length = 0
                    
                    for part in parts:
                        part_len = len(part) + len(sep) if current_chunk else len(part)
                        
                        if current_length + part_len > self.chunk_size and current_chunk:
                            result.append(sep.join(current_chunk))
                            # Keep overlap
                            overlap_text = sep.join(current_chunk)
                            overlap_text = overlap_text[-self.chunk_overlap:] if len(overlap_text) > self.chunk_overlap else overlap_text
                            current_chunk = [overlap_text, part] if overlap_text else [part]
                            current_length = len(part)
                        else:
                            current_chunk.append(part)
                            current_length += part_len
                    
                    if current_chunk:
                        result.append(sep.join(current_chunk))
                    
                    return result
            
            return [text]
        
        raw_chunks = _split_recursive(text, separators)
        
        # Create Chunk objects with proper metadata
        current_pos = 0
        for i, chunk_text in enumerate(raw_chunks):
            start_pos = text.find(chunk_text, current_pos)
            end_pos = start_pos + len(chunk_text)
            
            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "chunk_length": len(chunk_text),
                "start_char": start_pos,
                "end_char": end_pos,
            }
            
            chunks.append(Chunk(
                content=chunk_text.strip(),
                metadata=chunk_metadata,
                chunk_index=i,
                start_char=start_pos,
                end_char=end_pos
            ))
            
            current_pos = end_pos
        
        return chunks
    
    def _sentence_chunk(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Sentence-based chunking with overlap."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_start = 0
        
        for i, sentence in enumerate(sentences):
            sentence_len = len(sentence)
            
            if current_length + sentence_len > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunk_end = chunk_start + len(chunk_text)
                
                chunks.append(Chunk(
                    content=chunk_text,
                    metadata={**metadata, "chunk_index": len(chunks)},
                    chunk_index=len(chunks),
                    start_char=chunk_start,
                    end_char=chunk_end
                ))
                
                # Overlap: keep last few sentences
                overlap_sentences = []
                overlap_len = 0
                for s in reversed(current_chunk):
                    if overlap_len + len(s) > self.chunk_overlap:
                        break
                    overlap_sentences.insert(0, s)
                    overlap_len += len(s)
                
                current_chunk = overlap_sentences + [sentence]
                current_length = overlap_len + sentence_len
                chunk_start = chunk_end - overlap_len
            else:
                current_chunk.append(sentence)
                current_length += sentence_len
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(Chunk(
                content=chunk_text,
                metadata={**metadata, "chunk_index": len(chunks)},
                chunk_index=len(chunks),
                start_char=chunk_start,
                end_char=chunk_start + len(chunk_text)
            ))
        
        return chunks
    
    def _semantic_chunk(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Semantic chunking based on topic shifts (simplified)."""
        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            if current_length + len(para) > self.chunk_size and current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(Chunk(
                    content=chunk_text,
                    metadata={**metadata, "chunk_index": len(chunks)},
                    chunk_index=len(chunks),
                    start_char=0,
                    end_char=len(chunk_text)
                ))
                current_chunk = [para]
                current_length = len(para)
            else:
                current_chunk.append(para)
                current_length += len(para)
        
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(Chunk(
                content=chunk_text,
                metadata={**metadata, "chunk_index": len(chunks)},
                chunk_index=len(chunks),
                start_char=0,
                end_char=len(chunk_text)
            ))
        
        return chunks