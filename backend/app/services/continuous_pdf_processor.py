"""
Continuous PDF Processor - 고해상도 연속 이미지 처리 시스템
페이지 경계 문제 해결을 위한 하나의 긴 이미지 접근법
"""

import asyncio
import json
import os
import base64
import io
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import fitz  # PyMuPDF
from sqlalchemy.orm import Session
from sqlalchemy import text
import openai
import anthropic
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ContinuousPDFProcessor:
    """연속 이미지 처리 기반 PDF 처리 시스템"""
    
    def __init__(self):
        self.openai_client = None
        self.claude_client = None
        self.temp_dir = Path("temp_processing")
        self.temp_dir.mkdir(exist_ok=True)
        
    def set_openai_key(self, api_key: str):
        """OpenAI API 키 설정"""
        self.openai_client = openai.AsyncOpenAI(api_key=api_key)
        
    def set_claude_key(self, api_key: str):
        """Claude API 키 설정"""
        self.claude_client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def process_pdf_continuous_pipeline(self, upload_id: int, pdf_path: str, db: Session) -> Dict[str, Any]:
        """연속 이미지 처리 파이프라인 실행"""
        try:
            print(f"[시작] Continuous Image Processing Pipeline - Upload {upload_id}")
            
            # 1단계: PDF를 하나의 긴 연속 이미지로 변환
            continuous_result = await self._convert_pdf_to_continuous_image(upload_id, pdf_path, db)
            if not continuous_result['success']:
                return continuous_result
                
            # 2단계: GPT Vision으로 연속 이미지를 청크별로 Markdown 변환
            markdown_result = await self._convert_continuous_image_to_markdown(upload_id, continuous_result, db)
            if not markdown_result['success']:
                return markdown_result
                
            # 3단계: Ultra Enhanced Processor로 문제 구조화
            final_results = await self._structure_continuous_content(upload_id, markdown_result, db)
            
            return {
                'success': True,
                'upload_id': upload_id,
                'processing_summary': final_results,
                'continuous_image_info': continuous_result.get('image_info', {}),
                'questions_extracted': len(final_results.get('questions', [])),
                'materials_generated': len(final_results.get('materials', []))
            }
            
        except Exception as e:
            logger.error(f"Continuous PDF 처리 파이프라인 오류: {str(e)}")
            await self._log_processing_step(upload_id, "continuous_pipeline_error", "failed", 
                                          {"error": str(e)}, db)
            return {'success': False, 'error': str(e)}
    
    async def _convert_pdf_to_continuous_image(self, upload_id: int, pdf_path: str, db: Session) -> Dict[str, Any]:
        """1단계: PDF를 하나의 긴 연속 이미지로 변환"""
        try:
            await self._log_processing_step(upload_id, "pdf_to_continuous_image", "processing", {}, db)
            
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            print(f"Converting {total_pages} pages to one continuous high-resolution image...")
            
            # 고해상도 설정 (4배 확대로 최고 품질)
            scale_factor = 4.0
            mat = fitz.Matrix(scale_factor, scale_factor)
            
            # 모든 페이지의 이미지 수집
            page_images = []
            total_width = 0
            max_width = 0
            total_height = 0
            
            for page_num in range(total_pages):
                page = doc[page_num]
                
                # 고해상도로 페이지 렌더링
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # PIL Image로 변환
                img_data = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_data))
                
                page_images.append({
                    'image': pil_image,
                    'page_number': page_num + 1,
                    'width': pil_image.width,
                    'height': pil_image.height
                })
                
                total_height += pil_image.height
                max_width = max(max_width, pil_image.width)
                
                print(f"  Page {page_num + 1}: {pil_image.width}x{pil_image.height}")
            
            doc.close()
            
            # 연속 이미지 생성 (모든 페이지를 세로로 연결)
            print(f"Creating continuous image: {max_width}x{total_height}")
            
            # 흰색 배경으로 큰 이미지 생성
            continuous_image = Image.new('RGB', (max_width, total_height), 'white')
            
            # 각 페이지를 순서대로 배치
            current_y = 0
            page_boundaries = []  # 페이지 경계 정보 저장
            
            for page_info in page_images:
                page_img = page_info['image']
                
                # 중앙 정렬로 페이지 배치
                x_offset = (max_width - page_img.width) // 2
                continuous_image.paste(page_img, (x_offset, current_y))
                
                # 페이지 경계 정보 저장
                page_boundaries.append({
                    'page_number': page_info['page_number'],
                    'start_y': current_y,
                    'end_y': current_y + page_img.height,
                    'x_offset': x_offset,
                    'width': page_img.width,
                    'height': page_img.height
                })
                
                current_y += page_img.height
                
                print(f"  Placed page {page_info['page_number']} at y={current_y - page_img.height}")
            
            # 연속 이미지 저장
            continuous_image_path = self.temp_dir / f"continuous_{upload_id}.png"
            continuous_image.save(continuous_image_path, quality=95, optimize=True)
            
            image_info = {
                'path': str(continuous_image_path),
                'width': max_width,
                'height': total_height,
                'total_pages': total_pages,
                'file_size': os.path.getsize(continuous_image_path),
                'page_boundaries': page_boundaries,
                'scale_factor': scale_factor
            }
            
            print(f"Continuous image created:")
            print(f"  - Size: {max_width}x{total_height}")
            print(f"  - File size: {image_info['file_size'] / (1024*1024):.1f} MB")
            print(f"  - Pages: {total_pages}")
            
            await self._log_processing_step(upload_id, "pdf_to_continuous_image", "completed", {
                'image_dimensions': f"{max_width}x{total_height}",
                'total_pages': total_pages,
                'file_size_mb': round(image_info['file_size'] / (1024*1024), 2)
            }, db)
            
            return {
                'success': True,
                'image_info': image_info
            }
            
        except Exception as e:
            logger.error(f"PDF to continuous image conversion error: {str(e)}")
            await self._log_processing_step(upload_id, "pdf_to_continuous_image", "failed", 
                                          {"error": str(e)}, db)
            return {'success': False, 'error': str(e)}
    
    async def _convert_continuous_image_to_markdown(self, upload_id: int, continuous_result: Dict, db: Session) -> Dict[str, Any]:
        """2단계: 연속 이미지를 겹치는 청크로 분할하여 Markdown 변환"""
        try:
            await self._log_processing_step(upload_id, "continuous_to_markdown", "processing", {}, db)
            
            if not self.openai_client:
                print("ERROR: OpenAI API key not set")
                return {'success': False, 'error': 'OpenAI API key not set'}
            
            image_info = continuous_result['image_info']
            image_path = image_info['path']
            total_height = image_info['height']
            width = image_info['width']
            
            print(f"Processing continuous image with overlapping chunks...")
            
            # 청크 설정 (페이지 경계 문제 해결을 위해 겹치는 구간 설정)
            chunk_height = 3000  # 각 청크 높이 (약 1-2페이지 분량)
            overlap_height = 800  # 겹치는 구간 (문제 분할 방지)
            
            chunks_info = []
            current_y = 0
            chunk_index = 0
            
            while current_y < total_height:
                # 청크 경계 계산
                chunk_end_y = min(current_y + chunk_height, total_height)
                
                chunks_info.append({
                    'chunk_index': chunk_index,
                    'start_y': current_y,
                    'end_y': chunk_end_y,
                    'height': chunk_end_y - current_y,
                    'width': width
                })
                
                print(f"  Chunk {chunk_index}: y={current_y}-{chunk_end_y} (height={chunk_end_y - current_y})")
                
                # 다음 청크 시작점 (겹치는 구간 고려)
                current_y += chunk_height - overlap_height
                chunk_index += 1
                
                # 마지막 청크 처리
                if chunk_end_y >= total_height:
                    break
            
            print(f"Total chunks created: {len(chunks_info)}")
            
            # 원본 이미지 로드
            original_image = Image.open(image_path)
            
            # 각 청크를 Markdown으로 변환
            all_chunks_markdown = []
            total_tokens_used = 0
            
            for chunk_info in chunks_info:
                print(f"Processing chunk {chunk_info['chunk_index'] + 1}/{len(chunks_info)}...")
                
                # 청크 이미지 추출
                chunk_image = original_image.crop((
                    0,
                    chunk_info['start_y'],
                    chunk_info['width'],
                    chunk_info['end_y']
                ))
                
                # 청크 이미지를 base64로 인코딩
                buffer = io.BytesIO()
                chunk_image.save(buffer, format='PNG')
                base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                try:
                    # GPT Vision으로 청크를 Markdown으로 변환
                    prompt = f"""
이 이미지는 연속 PDF 문서의 청크 {chunk_info['chunk_index'] + 1}번입니다.
이 청크에는 여러 페이지의 내용이 연결되어 있을 수 있으며, 문제가 이전 청크에서 시작되어 이 청크에서 끝나거나, 이 청크에서 시작되어 다음 청크로 이어질 수 있습니다.

🎯 **핵심 요구사항**:
1. **완전한 문제 식별**: 이 청크에서 완전히 보이는 문제들을 모두 추출
2. **부분 문제 표시**: 시작만 있거나 끝만 있는 불완전한 문제도 모두 포함
3. **모든 선택지 추출**: ①②③④, 1)2)3)4), (A)(B)(C)(D) 등 모든 형태
4. **표/그림/코드 완전 보존**: 복잡한 내용도 텍스트로 상세히 설명
5. **텍스트 품질**: OCR 오류 최소화를 위해 정확한 텍스트 추출

📋 **출력 형식**:
```
# Chunk {chunk_info['chunk_index'] + 1}

## [문제번호 또는 PARTIAL_START/PARTIAL_END 표시]
[문제 내용을 완전히 작성]
[선택지들을 모두 작성]

## [다음 문제...]
```

⚠️ **특별 처리**:
- 문제가 중간에 잘린 경우: "## PARTIAL_START_Q[번호]" 또는 "## PARTIAL_END_Q[번호]"로 표시
- 표나 그래프: 구조와 내용을 모두 텍스트로 변환
- 빈 구간: 건너뛰지 말고 "[빈 공간]"으로 표시
- 추가 설명 없이 오직 Markdown만 출력
                    """.strip()
                    
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{base64_image}",
                                            "detail": "high"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=8000,  # 더 많은 토큰으로 완전한 추출
                        temperature=0.1   # 정확성을 위해 낮은 온도
                    )
                    
                    chunk_markdown = response.choices[0].message.content.strip()
                    
                    all_chunks_markdown.append({
                        'chunk_index': chunk_info['chunk_index'],
                        'markdown_content': chunk_markdown,
                        'start_y': chunk_info['start_y'],
                        'end_y': chunk_info['end_y'],
                        'tokens_used': response.usage.total_tokens
                    })
                    
                    total_tokens_used += response.usage.total_tokens
                    
                    print(f"  Chunk {chunk_info['chunk_index'] + 1} converted - {len(chunk_markdown)} chars, {response.usage.total_tokens} tokens")
                    
                    # API 레이트 리미트 방지
                    await asyncio.sleep(1.0)
                    
                except Exception as chunk_error:
                    print(f"  Failed to convert chunk {chunk_info['chunk_index']}: {chunk_error}")
                    all_chunks_markdown.append({
                        'chunk_index': chunk_info['chunk_index'],
                        'markdown_content': f"# Chunk {chunk_info['chunk_index'] + 1}\n\n[청크 변환 실패: {str(chunk_error)}]",
                        'start_y': chunk_info['start_y'],
                        'end_y': chunk_info['end_y'],
                        'tokens_used': 0
                    })
            
            # 모든 청크 결합
            complete_markdown = "\n\n---\n\n".join([chunk['markdown_content'] for chunk in all_chunks_markdown])
            
            print(f"Continuous image to Markdown conversion completed:")
            print(f"  - Total chunks: {len(all_chunks_markdown)}")
            print(f"  - Total markdown length: {len(complete_markdown)} characters")
            print(f"  - Total tokens used: {total_tokens_used}")
            
            # 샘플 출력
            print(f"=== 연속 처리 Markdown 결과 샘플 (처음 1500자) ===")
            print(complete_markdown[:1500])
            print("=== 샘플 끝 ===")
            
            await self._log_processing_step(upload_id, "continuous_to_markdown", "completed", {
                'total_chunks': len(all_chunks_markdown),
                'markdown_length': len(complete_markdown),
                'tokens_used': total_tokens_used
            }, db)
            
            return {
                'success': True,
                'markdown_content': complete_markdown,
                'chunks_processed': len(all_chunks_markdown),
                'chunks_info': all_chunks_markdown,
                'tokens_used': total_tokens_used
            }
            
        except Exception as e:
            logger.error(f"Continuous image to Markdown conversion error: {str(e)}")
            await self._log_processing_step(upload_id, "continuous_to_markdown", "failed", 
                                          {"error": str(e)}, db)
            return {'success': False, 'error': str(e)}
    
    async def _structure_continuous_content(self, upload_id: int, markdown_result: Dict, db: Session) -> Dict[str, Any]:
        """3단계: Ultra Enhanced Processor로 연속 콘텐츠 구조화"""
        try:
            await self._log_processing_step(upload_id, "continuous_structuring", "processing", {}, db)
            
            if not self.claude_client:
                print("ERROR: Claude API key not set")
                return {'success': False, 'questions': [], 'materials': [], 'error': 'Claude API key not set'}
            
            # Ultra Enhanced PDF Processor 사용
            from app.services.ultra_enhanced_pdf_processor import UltraEnhancedPDFProcessor
            
            ultra_processor = UltraEnhancedPDFProcessor(self.claude_client)
            
            # Markdown을 청크로 분할 (Ultra Enhanced Processor 호환)
            markdown_content = markdown_result.get('markdown_content', '')
            chunks_info = markdown_result.get('chunks_info', [])
            
            # 청크별 Markdown 추출
            chunks = [chunk_info['markdown_content'] for chunk_info in chunks_info]
            
            print(f"Processing {len(chunks)} chunks with Ultra Enhanced Pipeline...")
            
            # Ultra Enhanced 처리 실행
            processing_result = await ultra_processor.process_chunks_ultra(chunks)
            
            # 결과를 데이터베이스에 저장
            questions = processing_result.get('questions', [])
            
            saved_questions = 0
            saved_materials = 0
            
            if questions:
                for question in questions:
                    try:
                        # 데이터베이스에 문제 저장
                        db.execute(
                            text("""
                                INSERT INTO extracted_questions 
                                (pdf_upload_id, question_number, question_text, passage, options, 
                                 correct_answer, explanation, difficulty_level, category, 
                                 additional_info, created_at) 
                                VALUES 
                                (:pdf_upload_id, :question_number, :question_text, :passage, :options,
                                 :correct_answer, :explanation, :difficulty_level, :category,
                                 :additional_info, :created_at)
                            """),
                            {
                                'pdf_upload_id': upload_id,
                                'question_number': question.get('question_number', 0),
                                'question_text': question.get('question_text', ''),
                                'passage': question.get('passage', ''),
                                'options': json.dumps(question.get('options', []), ensure_ascii=False),
                                'correct_answer': question.get('correct_answer'),
                                'explanation': question.get('explanation'),
                                'difficulty_level': question.get('difficulty_level', 'medium'),
                                'category': question.get('category', 'general'),
                                'additional_info': json.dumps({
                                    'processing_method': 'continuous_image',
                                    'confidence': question.get('confidence', 'medium'),
                                    'has_table': question.get('has_table', False),
                                    'has_figure': question.get('has_figure', False),
                                    'has_code': question.get('has_code', False),
                                    'special_handling': question.get('special_handling', 'none'),
                                    'validation_status': question.get('validation_status', 'unknown')
                                }, ensure_ascii=False),
                                'created_at': datetime.now()
                            }
                        )
                        saved_questions += 1
                        
                    except Exception as save_error:
                        print(f"Failed to save question {question.get('question_number')}: {save_error}")
                
                db.commit()
            
            final_result = {
                'success': True,
                'questions': questions,
                'materials': [],  # 추후 구현
                'chapters': [],  # 추후 구현
                'processing_stats': processing_result.get('stage_stats', {}),
                'saved_questions': saved_questions,
                'saved_materials': saved_materials
            }
            
            print(f"Continuous structuring completed:")
            print(f"  - Questions extracted: {len(questions)}")
            print(f"  - Questions saved: {saved_questions}")
            print(f"  - Processing stats: {processing_result.get('stage_stats', {})}")
            
            await self._log_processing_step(upload_id, "continuous_structuring", "completed", {
                'questions_extracted': len(questions),
                'questions_saved': saved_questions,
                'materials_saved': saved_materials,
                'processing_stats': processing_result.get('stage_stats', {})
            }, db)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Continuous content structuring error: {str(e)}")
            await self._log_processing_step(upload_id, "continuous_structuring", "failed", 
                                          {"error": str(e)}, db)
            return {'success': False, 'questions': [], 'materials': [], 'error': str(e)}
    
    async def _log_processing_step(self, upload_id: int, step_name: str, status: str, 
                                 step_data: Dict[str, Any], db: Session):
        """처리 단계 로깅"""
        try:
            db.execute(
                text("""
                    INSERT INTO processing_steps 
                    (pdf_upload_id, step_name, status, step_data, created_at)
                    VALUES (:pdf_upload_id, :step_name, :status, :step_data, :created_at)
                """),
                {
                    'pdf_upload_id': upload_id,
                    'step_name': step_name,
                    'status': status,
                    'step_data': json.dumps(step_data, ensure_ascii=False),
                    'created_at': datetime.now()
                }
            )
            db.commit()
        except Exception as e:
            print(f"Failed to log processing step: {e}")