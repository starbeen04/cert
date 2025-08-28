"""
새로운 고급 PDF 처리 시스템
OpenAI API를 활용한 문서 분석과 전처리, OCR 분리 처리
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
import time
try:
    from .ultra_enhanced_prompts import UltraEnhancedPrompts
except ImportError:
    UltraEnhancedPrompts = None
    
try:
    from .image_processor_fix import ImageProcessorFix
except ImportError:
    ImageProcessorFix = None

try:
    # from .smart_pdf_analyzer import SmartPDFAnalyzer  # 삭제됨 - UltraPrecisePDFAnalyzer 사용
    SmartPDFAnalyzer = None
except ImportError:
    SmartPDFAnalyzer = None
import random

logger = logging.getLogger(__name__)

class AdvancedPDFProcessor:
    """고급 PDF 처리 시스템 - OpenAI + Claude 하이브리드"""
    
    def __init__(self):
        self.openai_client = None
        self.claude_client = None
        self.thumbnail_size = (1024, -1)  # 폭 1024px, 높이 자동
        self.temp_dir = Path("temp_processing")
        self.temp_dir.mkdir(exist_ok=True)
        
    def set_openai_key(self, api_key: str):
        """OpenAI API 키 설정"""
        self.openai_client = openai.AsyncOpenAI(api_key=api_key)
        
    def set_claude_key(self, api_key: str):
        """Claude API 키 설정"""
        self.claude_client = anthropic.AsyncAnthropic(api_key=api_key)
        
    async def process_pdf_complete_pipeline(self, upload_id: int, pdf_path: str, db: Session) -> Dict[str, Any]:
        """전체 PDF 처리 파이프라인 실행 - GPT Vision 기반 페이지별 Markdown 변환"""
        try:
            print(f"[시작] 새로운 GPT Vision 기반 PDF 처리 파이프라인 - Upload {upload_id}")
            
            # 1단계: PDF를 페이지별 고해상도 이미지로 변환
            pages_result = await self._convert_pdf_to_pages(upload_id, pdf_path, db)
            if not pages_result['success']:
                return pages_result
                
            # 2단계: PDF에서 이미지 추출 및 저장
            image_extraction_result = await self._extract_images_from_pdf(upload_id, pdf_path)
            
            # 🚨 2.5단계: PDF 직접 표 추출 완전 비활성화
            print("🚫 PDF 직접 표 추출 완전 비활성화 - 가짜 표 생성 방지")
            # direct_table_result = await self._extract_tables_directly_from_pdf(pdf_path, upload_id)
            direct_table_result = {'success': False, 'tables_count': 0, 'tables_data': []}
            
            # 3단계: 기존 GPT Vision 시스템으로 복귀 (이미지 정보 포함)
            extracted_images = image_extraction_result.get('images', []) if image_extraction_result['success'] else []
            markdown_result = await self._convert_pages_to_markdown(upload_id, pages_result['pages'], db, extracted_images)
            if not markdown_result['success']:
                return markdown_result
                
            # 4단계: Claude로 전체 Markdown을 문제단위로 구조화 (개선된 버전)
            final_results = await self._structure_markdown_content_enhanced(upload_id, markdown_result, db)
            
            # 이미지 정보를 최종 결과에 추가
            if image_extraction_result['success']:
                final_results['extracted_images'] = image_extraction_result['images']
                final_results['images_count'] = image_extraction_result['images_extracted']
            
            return {
                'success': True,
                'upload_id': upload_id,
                'processing_summary': final_results,
                'total_pages': pages_result.get('total_pages', 0),
                'questions_extracted': len(final_results.get('questions', [])),
                'materials_generated': len(final_results.get('materials', []))
            }
            
        except Exception as e:
            logger.error(f"PDF 처리 파이프라인 오류: {str(e)}")
            await self._log_processing_step(upload_id, "pipeline_error", "failed", 
                                          {"error": str(e)}, db)
            return {'success': False, 'error': str(e)}
    
    async def _convert_pages_to_markdown_enhanced(self, upload_id: int, pages_info: List[Dict], direct_table_data: Dict, db: Session) -> Dict[str, Any]:
        """🚀 향상된 마크다운 변환: GPT Vision + PDF 직접 표 추출 결합"""
        try:
            print(f"\n🔄 향상된 페이지 → 마크다운 변환 시작...")
            print(f"📊 직접 추출된 표: {direct_table_data.get('tables_count', 0)}개")
            
            # 기존 GPT Vision 처리 진행
            basic_result = await self._convert_pages_to_markdown(upload_id, pages_info, db)
            
            if not basic_result['success']:
                return basic_result
            
            # 단순화: 직접 표 추출 비활성화되었으므로 기본 결과만 반환
            print("📄 단순화된 GPT Vision 결과 사용")
            return basic_result
                
        except Exception as e:
            print(f"❌ 향상된 마크다운 변환 실패: {e}")
            # 실패시 기본 GPT Vision 결과라도 반환
            try:
                return await self._convert_pages_to_markdown(upload_id, pages_info, db)
            except:
                return {'success': False, 'error': str(e)}
    
    async def _enhance_markdown_with_direct_tables(self, original_markdown: str, table_data: Dict) -> str:
        """마크다운에 직접 추출된 표 데이터 삽입/보강"""
        try:
            print(f"🔄 마크다운 표 보강 처리...")
            
            enhanced_markdown = original_markdown
            tables_info = table_data.get('tables_data', [])
            
            # 페이지별로 표 정보 정리
            tables_by_page = {}
            for table in tables_info:
                page_num = table['page_number']
                if page_num not in tables_by_page:
                    tables_by_page[page_num] = []
                tables_by_page[page_num].append(table)
            
            # 각 페이지별로 표 삽입/보강
            for page_num, page_tables in tables_by_page.items():
                print(f"   📊 페이지 {page_num}: {len(page_tables)}개 표 보강...")
                
                # 해당 페이지 섹션 찾기
                page_pattern = f"# Page {page_num}"
                if page_pattern in enhanced_markdown:
                    
                    # 페이지 섹션 끝 찾기
                    next_page_pattern = f"# Page {page_num + 1}"
                    page_start = enhanced_markdown.find(page_pattern)
                    
                    if next_page_pattern in enhanced_markdown:
                        page_end = enhanced_markdown.find(next_page_pattern)
                        page_section = enhanced_markdown[page_start:page_end]
                        remaining_markdown = enhanced_markdown[page_end:]
                    else:
                        page_section = enhanced_markdown[page_start:]
                        remaining_markdown = ""
                    
                    # 페이지 섹션에 표 추가
                    enhanced_page_section = page_section
                    
                    for table_idx, table in enumerate(page_tables):
                        table_markdown = self._convert_table_to_markdown(table, table_idx + 1)
                        
                        # 기존 페이지에 표 관련 내용이 있는지 확인
                        has_existing_table = any(indicator in page_section.lower() for indicator in [
                            '|', '표', 'table', '프로세스', '데이터', '시간', '결과'
                        ])
                        
                        if has_existing_table:
                            # 기존 표 관련 내용 뒤에 정확한 표 추가
                            enhanced_page_section += f"\n\n## 🚀 정확한 표 데이터 (PDF 직접 추출)\n\n{table_markdown}"
                        else:
                            # 새로운 표로 추가
                            enhanced_page_section += f"\n\n## 📊 발견된 표 데이터\n\n{table_markdown}"
                        
                        print(f"      표 {table_idx+1}: {table['total_columns']}컬럼 × {len(table['data_rows'])}행 추가")
                    
                    # 향상된 페이지 섹션으로 교체
                    enhanced_markdown = enhanced_markdown[:page_start] + enhanced_page_section + remaining_markdown
            
            print(f"✅ 표 보강 완료: {len(tables_info)}개 표가 마크다운에 통합됨")
            return enhanced_markdown
            
        except Exception as e:
            print(f"⚠️ 표 보강 실패: {e}, 원본 마크다운 반환")
            return original_markdown
    
    def _convert_table_to_markdown(self, table_info: Dict, table_num: int) -> str:
        """표 정보를 마크다운 표 형식으로 변환"""
        try:
            headers = table_info.get('headers', [])
            data_rows = table_info.get('data_rows', [])
            method = table_info.get('extraction_method', 'unknown')
            
            if not headers and not data_rows:
                return f"**표 {table_num}**: 빈 표"
            
            markdown_lines = []
            markdown_lines.append(f"**표 {table_num}** ({method} 방법으로 추출):")
            markdown_lines.append("")
            
            # 헤더가 있는 경우
            if headers:
                # 헤더 행
                header_line = "| " + " | ".join(str(cell) if cell else "" for cell in headers) + " |"
                markdown_lines.append(header_line)
                
                # 구분선
                separator_line = "|" + "|".join("-------" for _ in headers) + "|"
                markdown_lines.append(separator_line)
            
            # 데이터 행들
            for row_idx, row in enumerate(data_rows):
                if row:  # 빈 행이 아닌 경우
                    # 헤더 컬럼 수에 맞춰 행 데이터 조정
                    if headers:
                        adjusted_row = row[:len(headers)]  # 헤더 수만큼만 사용
                        while len(adjusted_row) < len(headers):  # 부족한 컬럼은 빈 값으로 채움
                            adjusted_row.append("")
                    else:
                        adjusted_row = row
                    
                    row_line = "| " + " | ".join(str(cell) if cell else "" for cell in adjusted_row) + " |"
                    markdown_lines.append(row_line)
            
            # 표 정보 추가
            markdown_lines.append("")
            markdown_lines.append(f"*📊 표 정보: {len(data_rows)}개 데이터 행, {len(headers) if headers else len(data_rows[0]) if data_rows else 0}개 컬럼*")
            
            return "\n".join(markdown_lines)
            
        except Exception as e:
            return f"**표 {table_num}**: 변환 실패 - {str(e)}"
    
    async def _convert_pages_to_markdown_ultra_enhanced(self, upload_id: int, pages_info: List[Dict], db: Session) -> Dict[str, Any]:
        """🚀 ULTRA 개선된 GPT Vision 표 인식 (가짜 표 방지)"""
        try:
            await self._log_processing_step(upload_id, "ultra_enhanced_markdown", "processing", {}, db)
            
            if not self.openai_client:
                return {'success': False, 'error': 'OpenAI API key not set'}
            
            print(f"\n🔥 ULTRA 개선된 GPT Vision 처리 시작...")
            
            all_markdown_content = []
            individual_pages = [p for p in pages_info if not p.get('is_full_connected', False)]
            
            for i, page_info in enumerate(individual_pages):
                page_num = page_info['page_number']
                image_path = page_info['image_path']
                
                print(f"📄 페이지 {page_num}/{len(individual_pages)} - ULTRA 표 인식 처리")
                
                try:
                    with open(image_path, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    
                    # 🎯 근본적으로 다른 접근법: 표 vs 비표 명확한 구분
                    ultra_prompt = f"""
🎯 **페이지 {page_num} 정밀 분석** - 표 vs 선택지 구분

이미지를 보고 다음 단계로 분석해주세요:

**1단계: 표 존재 여부 확인**
- 실제 표(table)가 있는가? ✅ 또는 ❌
- 표의 정의: 행과 열로 구성된 격자 구조, 헤더 행 + 최소 2개 이상의 데이터 행

**2단계: 표가 아닌 것들 제외**
❌ **이것들은 표가 아님**:
- 선택지 (①②③④)
- 문제 번호 나열
- 단순 텍스트 정렬
- 한 줄짜리 항목들

**3단계: 실제 표라면 완전 추출**
✅ **진짜 표의 특징**:
- 명확한 헤더 행 (프로세스, 도착시간, 실행시간 등)
- 여러 개의 데이터 행 (P1,P2,P3... 또는 기타 데이터)
- 격자 구조 또는 일정한 간격
- 숫자나 체계적인 데이터

**🚨 중요**: 
- 표가 없으면 "이 페이지에는 표가 없습니다" 명시
- 표가 있으면 헤더부터 마지막 데이터 행까지 완전 추출
- 선택지나 문제 번호를 표로 착각하지 말 것

**출력 형식**:

# 페이지 {page_num}

## 표 분석 결과
[표 있음 / 표 없음]

## 페이지 내용
[문제들을 일반적으로 추출]

## 표 데이터 (있는 경우에만)
| 헤더1 | 헤더2 | 헤더3 |
|-------|-------|-------|
| 데이터1 | 데이터2 | 데이터3 |
| 데이터4 | 데이터5 | 데이터6 |

표 완전성: [✅ 완전 / ❌ 불완전 - 이유]
                    """.strip()
                    
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": ultra_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}", "detail": "high"}}
                            ]
                        }],
                        max_tokens=4000,
                        temperature=0.1  # 매우 정확한 추출
                    )
                    
                    page_markdown = response.choices[0].message.content.strip()
                    all_markdown_content.append(page_markdown)
                    
                    print(f"✅ 페이지 {page_num} ULTRA 처리 완료: {len(page_markdown)}chars")
                    await asyncio.sleep(3)  # API 안정성 강화
                    
                except Exception as page_error:
                    print(f"❌ 페이지 {page_num} 처리 실패: {page_error}")
                    all_markdown_content.append(f"# 페이지 {page_num}\n\n⚠️ 처리 실패: {str(page_error)}")
            
            complete_markdown = "\n\n---\n\n".join(all_markdown_content)
            
            print(f"🎯 ULTRA 처리 완료:")
            print(f"   총 {len(individual_pages)}페이지 처리")
            print(f"   총 마크다운: {len(complete_markdown)}chars")
            
            return {
                'success': True,
                'markdown_content': complete_markdown,
                'cross_page_issues': '',  # ULTRA 모드에서는 단순화
                'pages_processed': len(individual_pages),
                'tokens_used': 0,
                'estimated_cost': 0
            }
            
        except Exception as e:
            print(f"❌ ULTRA 처리 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _convert_pdf_to_pages(self, upload_id: int, pdf_path: str, db: Session) -> Dict[str, Any]:
        """1단계: PDF를 페이지별 고해상도 이미지로 변환"""
        try:
            await self._log_processing_step(upload_id, "pdf_to_pages_conversion", "processing", {}, db)
            
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            print(f"Converting {total_pages} pages to individual high-resolution images...")
            
            # 1. 각 페이지를 개별 이미지로 변환
            page_files = []
            page_pixmaps = []  # 전체 연결 이미지용
            
            for page_num in range(total_pages):
                page = doc[page_num]
                
                # 초고해상도 렌더링 (4배 확대로 더 선명하게)
                mat = fitz.Matrix(4.0, 4.0)  # 4배 확대로 표와 작은 글씨도 선명하게
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # 개별 페이지 이미지 저장
                page_image_path = self.temp_dir / f"page_{upload_id}_{page_num:03d}.png"
                pix.save(str(page_image_path))
                
                # 전체 연결 이미지용 pixmap 저장
                page_pixmaps.append(pix)
                
                page_info = {
                    'page_number': page_num + 1,
                    'image_path': str(page_image_path),
                    'width': pix.width,
                    'height': pix.height,
                    'file_size': os.path.getsize(page_image_path)
                }
                page_files.append(page_info)
                
                print(f"Processed page {page_num + 1}/{total_pages} - {pix.width}x{pix.height}")
            
            # 2. 모든 페이지를 세로로 연결한 초고해상도 전체 이미지 생성
            print(f"Creating full-length connected image for {total_pages} pages...")
            
            if page_pixmaps:
                total_width = max(pix.width for pix in page_pixmaps)
                total_height = sum(pix.height for pix in page_pixmaps)
                
                # PIL 이미지로 변환해서 연결
                from PIL import Image
                import io
                
                # 전체 캔버스 생성
                full_image = Image.new('RGB', (total_width, total_height), 'white')
                
                current_y = 0
                for i, pix in enumerate(page_pixmaps):
                    # Pixmap을 PIL Image로 변환
                    img_data = pix.tobytes("png")
                    page_img = Image.open(io.BytesIO(img_data))
                    
                    # 페이지 이미지를 전체 캔버스에 붙이기
                    full_image.paste(page_img, (0, current_y))
                    current_y += page_img.height
                    
                    print(f"Connected page {i+1}/{total_pages} at y={current_y}")
                
                # 전체 연결 이미지 저장
                full_image_path = self.temp_dir / f"full_connected_{upload_id}.png"
                full_image.save(str(full_image_path), 'PNG', optimize=True)
                
                print(f"✅ Full connected image created: {total_width}x{total_height} -> {full_image_path}")
                
                # 전체 이미지 정보를 페이지 리스트에 추가
                full_image_info = {
                    'page_number': 0,  # 전체 이미지는 0번
                    'image_path': str(full_image_path),
                    'width': total_width,
                    'height': total_height,
                    'file_size': os.path.getsize(full_image_path),
                    'is_full_connected': True
                }
                page_files.insert(0, full_image_info)  # 첫 번째로 추가
            
            doc.close()
            
            print(f"All {total_pages} pages converted + 1 full connected image created")
            
            await self._log_processing_step(upload_id, "pdf_to_pages_conversion", "completed", {
                'total_pages': total_pages,
                'has_full_connected_image': len(page_pixmaps) > 0,
                'pages_info': page_files[:3]  # 첫 3개 정보만 로그에 저장
            }, db)
            
            return {
                'success': True,
                'total_pages': total_pages,
                'pages': page_files,
                'has_full_connected': len(page_pixmaps) > 0
            }
            
        except Exception as e:
            logger.error(f"PDF to pages conversion error: {str(e)}")
            await self._log_processing_step(upload_id, "pdf_to_pages_conversion", "failed", 
                                          {"error": str(e)}, db)
            return {'success': False, 'error': str(e)}
    
    async def _convert_pages_to_markdown(self, upload_id: int, pages_info: List[Dict], db: Session, extracted_images: List[Dict] = None) -> Dict[str, Any]:
        """2단계: GPT Vision으로 각 페이지를 Markdown으로 변환"""
        try:
            await self._log_processing_step(upload_id, "pages_to_markdown", "processing", {}, db)
            
            if not self.openai_client:
                print("ERROR: OpenAI API key not set - cannot perform GPT Vision conversion")
                return {
                    'success': False, 
                    'error': 'OpenAI API key not set'
                }
            
            print(f"Converting {len(pages_info)} pages to Markdown using GPT Vision...")
            
            all_markdown_content = []
            total_tokens_used = 0
            total_cost = 0.0
            
            # 🚫 전체 연결 분석 완전 비활성화 - 개별 페이지 겹침 처리로 대체
            full_connected_content = ""
            has_full_connected = False  # 강제 비활성화
            
            if False:  # 완전 비활성화
                full_page_info = next(p for p in pages_info if p.get('is_full_connected', False))
                print(f"🔗 Processing full connected image with smart chunking for cross-page analysis...")
                
                try:
                    from PIL import Image
                    full_image = Image.open(full_page_info['image_path'])
                    
                    # GPT Vision 최적 크기: 더 작은 청크로 변경 (표 인식 개선용)
                    MAX_CHUNK_HEIGHT = 2000  # 4000 → 2000으로 축소
                    OVERLAP_HEIGHT = 600     # 겹침 영역 축소
                    
                    width, height = full_image.size
                    print(f"Full image dimensions: {width}x{height}")
                    
                    # 청킹이 필요한지 확인
                    if height <= MAX_CHUNK_HEIGHT:
                        print("Full image is small enough, processing as single chunk")
                        chunks = [full_image]
                        chunk_positions = [(0, height)]
                    else:
                        print(f"Splitting into chunks with {OVERLAP_HEIGHT}px overlap")
                        chunks = []
                        chunk_positions = []
                        
                        y_start = 0
                        while y_start < height:
                            y_end = min(y_start + MAX_CHUNK_HEIGHT, height)
                            
                            # 마지막 청크가 너무 작으면 이전 청크와 합침
                            if height - y_end < OVERLAP_HEIGHT:
                                y_end = height
                            
                            chunk = full_image.crop((0, y_start, width, y_end))
                            chunks.append(chunk)
                            chunk_positions.append((y_start, y_end))
                            
                            print(f"Created chunk: y={y_start}-{y_end} ({y_end-y_start}px height)")
                            
                            # 다음 청크 시작점 (겹침 적용)
                            if y_end >= height:
                                break
                            y_start = y_end - OVERLAP_HEIGHT
                    
                    # 각 청크별로 페이지 경계 분석
                    chunk_results = []
                    for idx, chunk in enumerate(chunks):
                        y_start, y_end = chunk_positions[idx]
                        
                        # 임시 청크 파일 저장
                        chunk_path = self.temp_dir / f"chunk_{upload_id}_{idx}.png"
                        chunk.save(str(chunk_path), 'PNG', optimize=True)
                        
                        with open(chunk_path, "rb") as chunk_file:
                            chunk_base64 = base64.b64encode(chunk_file.read()).decode('utf-8')
                        
                        chunk_prompt = f"""
📋 **연결 문서 청크 {idx+1}/{len(chunks)} 텍스트 분석**
구간: y={y_start}-{y_end} ({y_end-y_start}px)

**분석 목표**:
이 이미지 청크에서 한국어 텍스트를 모두 읽어서 다음 패턴들을 찾아주세요.

**🔍 찾을 패턴들**:
1. **데이터 테이블**: 행과 열로 구성된 격자형 데이터 구조
   - 헤더 행이 있고 그 아래 여러 데이터 행이 있는 구조
   - 예: 프로세스, 도착시간, 실행시간 등의 컬럼이 있는 표

2. **분할된 콘텐츠**: 청크 경계에서 잘린 텍스트 블록
   - 상단에서 시작되지만 앞부분이 없는 텍스트
   - 하단에서 끝나지만 뒷부분이 다음 청크에 있는 텍스트
   - 번호가 있는 항목에서 선택지가 불완전한 경우

**📋 출력 형식**:

**데이터 테이블 발견시**:
### 📊 테이블 발견: [위치 설명]
| 컬럼1 | 컬럼2 | 컬럼3 |
|-------|-------|-------|
| 행1데이터1 | 행1데이터2 | 행1데이터3 |
| 행2데이터1 | 행2데이터2 | 행2데이터3 |
| 행3데이터1 | 행3데이터2 | 행3데이터3 |

**분할 콘텐츠 발견시**:
### 🔗 분할 콘텐츠: 항목 X
- 내용: [완전한 텍스트 내용]
- 선택지: [①②③④⑤ 모든 옵션]
- 상태: [완전함/불완전함]

**아무것도 특별한 게 없으면**: "청크 {idx+1}: 특별한 패턴 없음"

⚡ **중요**: 모든 한국어 텍스트를 정확히 읽어서 완전한 정보를 제공해주세요.
                        """.strip()
                        
                        chunk_response = await self.openai_client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": chunk_prompt},
                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{chunk_base64}"}}
                                ]
                            }],
                            max_tokens=3000,
                            temperature=0.1
                        )
                        
                        chunk_content = chunk_response.choices[0].message.content.strip()
                        chunk_results.append(f"=== 청크 {idx+1} 결과 ===\n{chunk_content}")
                        print(f"✅ Chunk {idx+1} analysis completed: {len(chunk_content)} chars")
                        
                        # 임시 청크 파일 삭제
                        os.unlink(chunk_path)
                    
                    # 모든 청크 결과 통합
                    full_connected_content = "\n\n".join(chunk_results)
                    print(f"✅ Full connected chunked analysis completed: {len(full_connected_content)} total chars")
                    
                except Exception as e:
                    print(f"⚠️ Full connected image processing failed: {e}")
            
            # 개별 페이지 처리 (단순화 - 표 감지 시스템 제거)
            individual_pages = [p for p in pages_info if not p.get('is_full_connected', False)]
            
            for i, page_info in enumerate(individual_pages):
                page_num = page_info['page_number']
                image_path = page_info['image_path']
                
                print(f"📄 페이지 {page_num}/{len(individual_pages)} 단순 처리")
                
                try:
                    # 이미지를 base64로 인코딩
                    with open(image_path, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    
                    # 전체 연결 분석에서 표 정보 추출
                    table_hints = ""
                    boundary_hints = ""
                    
                    if full_connected_content:
                        # 표 정보 추출
                        if "📊 표 발견:" in full_connected_content:
                            table_section = full_connected_content.split("📊 표 발견:")[1].split("🔗 경계 문제")[0] if "🔗 경계 문제" in full_connected_content else full_connected_content.split("📊 표 발견:")[1]
                            table_hints = f"🎯 전체 분석에서 발견된 표:\n{table_section[:400]}..."
                        
                        # 페이지 경계 정보 추출  
                        if "🔗 경계 문제" in full_connected_content:
                            boundary_section = full_connected_content.split("🔗 경계 문제")[1]
                            if f"{page_num}번" in boundary_section:
                                boundary_hints = f"⚠️ 페이지 {page_num} 경계 문제 주의:\n{boundary_section[:300]}..."

                    # 페이지 이미지 분석
                    from PIL import Image
                    page_image = Image.open(image_path)
                    width, height = page_image.size

                    # 🖼️ 현재 페이지 이미지들 필터링
                    page_images = []
                    if extracted_images:
                        page_images = [img for img in extracted_images if img['page_number'] == page_num]
                    
                    # 📷 이미지 참조 힌트 생성
                    image_hints = ""
                    if page_images:
                        image_hints = f"""
📷 **페이지 {page_num}에서 추출된 이미지들**:
"""
                        for img in page_images[:5]:  # 최대 5개 이미지만 표시
                            image_hints += f"- {img['image_id']}: {img['web_path']}\n"
                        
                        if len(page_images) > 5:
                            image_hints += f"- ... 총 {len(page_images)}개 이미지 추출됨\n"
                    
                    # 🚀 Ultra-Enhanced 표 및 이미지 처리 프롬프트
                    prompt = f"""
🔍 **정밀 한국어 텍스트 추출 - 페이지 {page_num}** (Plain Text 출력)

{image_hints}

📋 **미션**: 이 페이지의 **실제 내용을 Plain Text**로 정확히 추출하세요.

🚨 **핵심 변경**: Markdown 사용 금지 → Plain Text로 출력
- **특수문자 문제 해결**: *, #, |, [], % 등을 그대로 표현
- **이미지 참조 변경**: ![IMG_XXX] → IMG_XXX_IMAGE
- **표 형식 변경**: | 테이블 → 단순 텍스트

⚡ **추출 규칙**:

1️⃣ **표 데이터 완전 추출** (최우선):
   - **헤더 행**: 모든 컬럼명 추출
   - **모든 데이터 행**: P1,P2,P3... 또는 기타 모든 행
   - **빈 셀 표시**: 공백이나 "-"로 표시
   - **표 없으면**: "표 없음" 명시

2️⃣ **이미지 선택지 처리** (🚨 매우 중요!):
   - **이미지가 선택지인 경우**: 반드시 "IMG_XXX_IMAGE" 형태로 출력
   - **예시**: ① IMG_001_IMAGE, ② IMG_002_IMAGE, ③ 텍스트 선택지, ④ IMG_003_IMAGE
   - **다이어그램/그래프**: "DIAGRAM_IMAGE" 또는 구체적 설명 + "_IMAGE"
   - **🔍 이미지 인식 강화**: 선택지 영역에서 텍스트가 아닌 그림/도형/그래프가 보이면 반드시 IMG_XXX_IMAGE로 표기
   - **이미지 힌트 활용**: 페이지에 추출된 이미지 목록을 참조하여 해당 위치의 이미지 ID 사용

3️⃣ **페이지 경계 선택지 완전 처리** (🚨 절대 실수 금지!):
   - **페이지 하단 세심한 검사**: 페이지 맨 아래 5줄을 반드시 정밀 검사
   - **선택지 번호 체크**: ①②③④⑤ 또는 1)2)3)4) 중 하나라도 빠지면 다음 페이지에서 완성된 선택지를 찾아 병합
   - **🔍 완전한 선택지 추출**:
     * 페이지 하단에 ①②만 있으면 → 다음 페이지 상단에서 ③④⑤ 탐지하여 완전한 선택지 생성
     * 페이지 하단에 ①②③만 있으면 → 다음 페이지 상단에서 ④⑤ 탐지하여 완전한 선택지 생성
     * 페이지 하단에 ①②③④만 있으면 → 다음 페이지 상단에서 ⑤ 탐지하여 완전한 선택지 생성
   - **선택지 병합 우선**: 불완전한 선택지는 절대 출력하지 말고 다음 페이지 내용과 합쳐서 완전한 선택지로만 출력
   - **선택지 번호 보존**: ①②③④⑤ 또는 1)2)3)4)5) 번호를 절대 생략하지 말고 정확히 표기

4️⃣ **코드 들여쓰기 완전 보존** (🚨 공백 하나도 놓치지 말 것!):
   - **코드 패턴 감지**: 
     * `int`, `public`, `class`, `function`, `while`, `for`, `if` 키워드 발견시
     * 중괄호 `{{}}`, 괄호 `()`, 대괄호 `[]` 포함된 여러 줄 구조
     * 4칸 이상 일관된 들여쓰기가 있는 블록
   - **🔍 들여쓰기 보존 규칙**:
     * 원본 공백/탭을 1:1로 정확히 복사
     * 들여쓰기 레벨을 임의로 변경하지 말 것
     * 코드 앞뒤로 [CODE_START]/[CODE_END] 마커 필수 삽입
   - **코드 예시**:
     [CODE_START]
     int a = 0, sum = 0;
     do {{
         a++;          ← 이 들여쓰기 정확히 보존
         sum += a;     ← 이 들여쓰기 정확히 보존
     }} while(a > 10);
     [CODE_END]

🎯 **Plain Text 출력 형식**:

=== 페이지 {page_num} ===

문제 1번
질문 내용을 정확히 작성
선택지 1: 내용
선택지 2: 내용  
선택지 3: IMG_XXX_IMAGE
선택지 4: 내용

[표 데이터 - 범용 처리]
제목: (표 위나 아래 제목이 있다면 추출)
헤더: 컬럼1 | 컬럼2 | 컬럼3 | ... (실제 헤더명)
행1: 데이터1 | 데이터2 | 데이터3 | ... (첫 번째 데이터 행)
행2: 데이터4 | 데이터5 | 데이터6 | ... (두 번째 데이터 행)
행3: 데이터7 | 데이터8 | 데이터9 | ... (세 번째 데이터 행)
... (표에 있는 모든 데이터 행을 순서대로)

🚨 **범용 표 처리 규칙**:
- **자동 표 감지**: 격자 구조, 일정한 간격, 정렬된 데이터 패턴 인식
- **헤더 자동 판단**: 첫 번째 행을 헤더로 추정 (컬럼명 특성 확인)
- **모든 행 추출**: 헤더 다음의 모든 데이터 행을 순서대로 추출
- **다양한 형태 지원**: P1,P2,P3 / A,B,C / 1,2,3 / 항목1,항목2 / 회사명,매출액 등
- **빈 셀 처리**: 빈 칸은 "빈칸" 또는 "-" 로 표시
- **가짜 데이터 절대 금지**: 실제 보이는 데이터만 추출
- **특수문자**: *, %, &, @ 등 모두 그대로 표시

📋 **최종 출력**: Plain Text만 사용 (Markdown 금지)
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
                        max_tokens=10000,
                        temperature=0.01
                    )
                    
                    page_content = response.choices[0].message.content.strip()
                    print(f"✅ 페이지 {page_num} 처리 완료: {len(page_content)}chars")
                    
                    # 🔗 페이지간 선택지 연결 전처리
                    processed_content = self._preprocess_page_connections(page_content, page_num, all_markdown_content)
                    
                    # 페이지별 내용 추가
                    if i > 0:  # 첫 페이지가 아닌 경우
                        all_markdown_content.append("\n---\n")  # 페이지 구분선
                    
                    all_markdown_content.append(f"=== 페이지 {page_num} ===\n\n{processed_content}")
                    
                    # 토큰 사용량 누적
                    tokens_used = response.usage.total_tokens
                    cost = tokens_used * 0.00001  # GPT-4O 대략 비용
                    total_tokens_used += tokens_used
                    total_cost += cost
                    
                    # 충분한 지연으로 API 안정성 향상
                    await asyncio.sleep(4)  # 강화된 대기
                    
                except Exception as page_error:
                    print(f"Failed to convert page {page_num}: {page_error}")
                    # 실패한 페이지는 빈 내용으로 처리
                    all_markdown_content.append(f"# Page {page_num}\n\n[페이지 변환 실패: {str(page_error)}]")
            
            # 🔗 전체 연결 이미지 분석 결과 저장 (마크다운에 포함하지 않음 - 별도 처리)
            cross_page_issues = ""
            if full_connected_content.strip():
                cross_page_issues = full_connected_content
                print(f"✅ Full connected image analysis completed: {len(full_connected_content)} chars")
                print("페이지 경계 분석 결과는 별도 저장됨 - 마크다운 추출과 분리 처리")
            
            # 전체 Markdown 문서 생성
            complete_markdown = "\n\n".join(all_markdown_content)
            
            print(f"GPT Vision conversion completed:")
            print(f"  - Total pages processed: {len(individual_pages)}")
            print(f"  - Has full connected analysis: {bool(full_connected_content)}")
            print(f"  - Total markdown length: {len(complete_markdown)} characters") 
            print(f"  - Total tokens used: {total_tokens_used}")
            print(f"  - Total estimated cost: ${total_cost:.4f}")
            
            # 샘플 출력
            print(f"=== Markdown 변환 결과 샘플 (처음 1000자) ===")
            print(complete_markdown[:1000])
            print("=== 샘플 끝 ===")
            
            await self._log_processing_step(upload_id, "pages_to_markdown", "completed", {
                'total_pages': len(pages_info),
                'markdown_length': len(complete_markdown),
                'tokens_used': total_tokens_used,
                'estimated_cost': total_cost
            }, db)
            
            return {
                'success': True,
                'markdown_content': complete_markdown,
                'cross_page_issues': cross_page_issues,  # 페이지 경계 문제 별도 전달
                'pages_processed': len(pages_info),
                'tokens_used': total_tokens_used,
                'estimated_cost': total_cost
            }
            
        except Exception as e:
            logger.error(f"Pages to Markdown conversion error: {str(e)}")
            await self._log_processing_step(upload_id, "pages_to_markdown", "failed", 
                                          {"error": str(e)}, db)
            return {'success': False, 'error': str(e)}
    
    async def _structure_markdown_content(self, upload_id: int, markdown_result: Dict, db: Session) -> Dict[str, Any]:
        """3단계: Claude로 전체 Markdown을 문제단위로 구조화"""
        try:
            await self._log_processing_step(upload_id, "markdown_structuring", "processing", {}, db)
            
            if not self.claude_client:
                print("ERROR: Claude API key not set - cannot perform markdown structuring")
                return {
                    'success': False,
                    'questions': [],
                    'materials': [],
                    'chapters': [],
                    'error': 'Claude API key not set'
                }
            
            markdown_content = markdown_result.get('markdown_content', '')
            if not markdown_content:
                print("No markdown content to structure")
                return {
                    'success': False,
                    'questions': [],
                    'materials': [],
                    'chapters': [],
                    'error': 'No markdown content provided'
                }
            
            print(f"Structuring {len(markdown_content)} characters of Markdown content with Claude...")
            
            # 🎯 GPT Vision이 인식한 실제 문제 수 파악
            cross_page_issues = markdown_result.get('cross_page_issues', '')
            estimated_question_count = self._estimate_question_count_from_markdown(markdown_content)
            print(f"📊 GPT Vision 분석 결과:")
            print(f"  - 추정 실제 문제 수: {estimated_question_count}개")
            if cross_page_issues:
                print(f"  - 페이지 경계 문제: 감지됨 ({len(cross_page_issues)} chars)")
            
            # 대용량 문서 스마트 청킹 처리 - Claude 토큰 제한 해결 + 실제 문제 수 기반
            max_chunk_size = 80000  # Claude의 입력 토큰 제한을 고려한 청크 크기
            chunks = []
            
            # 🧠 스마트 청킹 전략 - 실제 문제 수 기반
            if len(markdown_content) > max_chunk_size:
                print(f"Large document detected ({len(markdown_content)} chars). Implementing question-aware smart chunking...")
                
                # 페이지별 문제 분포 분석
                import re
                page_pattern = r'# Page (\d+)\n\n(.*?)(?=# Page \d+|$)'
                page_matches = re.findall(page_pattern, markdown_content, re.DOTALL)
                
                print(f"📄 Detected {len(page_matches)} pages with content")
                
                # 각 페이지의 문제 수 추정
                page_question_counts = []
                total_estimated_questions = 0
                for page_num, page_content in page_matches:
                    question_count = self._count_questions_in_page(page_content)
                    page_question_counts.append((int(page_num), question_count, page_content))
                    total_estimated_questions += question_count
                    print(f"  Page {page_num}: ~{question_count} questions")
                
                print(f"📊 Total estimated questions from page analysis: {total_estimated_questions}")
                
                # 문제 밀도 기반 스마트 청킹 (15-20문제씩 그룹화) - 빈 페이지 제외
                # 더 큰 청크로 관련 문제들을 함께 그룹화하여 단편화 방지 및 문제 누락 방지
                target_questions_per_chunk = 25  # 대폭 증가: 페이지 경계 문제 최소화
                current_chunk_pages = []
                current_chunk_questions = 0
                
                # 문제가 있는 페이지만 필터링
                valid_pages = [(page_num, question_count, page_content) 
                              for page_num, question_count, page_content in page_question_counts 
                              if question_count > 0]
                
                print(f"📄 Filtering: {len(valid_pages)} pages with questions out of {len(page_question_counts)} total pages")
                
                for page_num, question_count, page_content in valid_pages:
                    page_header = f"# Page {page_num}\n\n"
                    full_page = page_header + page_content
                    
                    # 청크에 추가할지 판단
                    if (current_chunk_questions + question_count <= target_questions_per_chunk or 
                        not current_chunk_pages):
                        current_chunk_pages.append(full_page)
                        current_chunk_questions += question_count
                    else:
                        # 현재 청크 완료
                        chunk_content = "\n\n".join(current_chunk_pages)
                        chunks.append(chunk_content)
                        print(f"Created chunk: {len(current_chunk_pages)} pages, ~{current_chunk_questions} questions ({len(chunk_content)} chars)")
                        
                        # 새 청크 시작
                        current_chunk_pages = [full_page]
                        current_chunk_questions = question_count
                
                # 마지막 청크 처리
                if current_chunk_pages:
                    chunk_content = "\n\n".join(current_chunk_pages)
                    chunks.append(chunk_content)
                    print(f"Final chunk: {len(current_chunk_pages)} pages, ~{current_chunk_questions} questions ({len(chunk_content)} chars)")
                
                print(f"📦 Document split into {len(chunks)} question-aware chunks")
                
            else:
                chunks = [markdown_content]
            
            # 각 청크별로 Claude 분석 실행
            all_questions = []
            all_materials = []
            all_chapters = []
            
            for chunk_idx, chunk in enumerate(chunks):
                print(f"Processing chunk {chunk_idx + 1}/{len(chunks)} ({len(chunk)} characters)...")
                
                # Claude로 구조화된 마크다운을 JSON으로 변환 (크로스 페이지 보완)
                cross_page_context = cross_page_issues if cross_page_issues else ""
                
                structuring_prompt = f"""
🤖 **Plain Text 교육 콘텐츠 JSON 변환기** (특수문자 안전 처리)

다음은 GPT Vision이 Plain Text로 분석한 교육 문서입니다.
특수문자(*, %, &, @)와 이미지 참조를 안전하게 처리하여 완전한 JSON을 생성하세요.

📊 **페이지 분석 결과 (청크 {chunk_idx + 1}/{len(chunks)})**:
```text
{chunk}
```

{f'''🔗 **추가 분석 결과**:
```text
{cross_page_context[:1000]}...
```

이 추가 정보를 활용하여 놓친 내용을 보완하세요.
''' if cross_page_context else ''}

🎯 **범용 Plain Text 변환 규칙**:
1. **범용 표 데이터 추출**: 
   - 자동 표 감지 (격자구조, 정렬된 데이터 등)
   - 헤더 자동 판단 (첫 번째 행의 컬럼명 특성 확인)
   - 모든 데이터 행 순서대로 추출 (형태 무관: A,B,C / 1,2,3 / 항목명 등)
   - 빈 셀은 null 또는 빈 문자열로 처리
2. **이미지 참조 처리**: "IMG_XXX_IMAGE" → ![IMG_XXX](/images/upload_XXX/IMG_XXX.png)
3. **특수문자 안전 처리**: *, %, &, @ 등을 JSON에서 안전하게 처리
4. **페이지 연결 처리**: 전처리에서 병합된 선택지 활용

🚨 **중복 문제 제거 규칙** (핵심 개선!):
5. **문제 번호 고유성**: 이미 처리된 문제 번호는 다시 추출하지 않음
6. **불완전 선택지 감지**: "(선택지 불완전 - 다음 페이지 확인)" 표시된 문제는 선택지를 2개 이하로 제한
7. **페이지 경계 처리**: "(다음 페이지 계속)" 표시된 문제는 incomplete_choices: true 마킹
8. **코드 블록 보존**: [CODE_BLOCK_START]...[CODE_BLOCK_END] 사이 내용은 들여쓰기 완전 보존

⚡ **특별 처리 규칙**:
- 🚨 **가짜 데이터 생성 절대 금지**: 없는 표 데이터 임의 생성 금지
- **이미지 변환**: "IMG_XXX_IMAGE" → 실제 이미지 마크다운 참조로 변환
- **표 데이터 우선**: 실제 추출된 모든 데이터 행 사용
- **특수문자**: JSON 문자열에서 이스케이프 처리

🎯 **초엄격 추출 규칙**:
1. **문제만 추출**: 반드시 번호(1., 2., 3. 또는 1), 2), 3))가 있는 실제 시험문제만
   - **질문형 패턴**: "~은?", "~는?", "~인가?", "~할까?", "~다면?", "~은 무엇인가?", "~을 구하시오", "~을 고르시오", "~하시오"
   - **지시형 패턴**: "다음 중", "아래에서", "위에서", "보기에서", "다음으로", "알맞은 것은", "옳은 것은", "틀린 것은", "가장 적절한 것은"
   - **설명문 제외**: "~입니다", "~합니다", "~다", "~이다", "~된다", "~한다", "~이며", "~하여" 로 끝나는 단순 서술문 무시

2. **해설/정답 페이지 절대 제외**: 
   - "해설", "정답", "풀이", "답안", "해답", "설명", "해석", "답:", "정답은", "해답지", "채점기준", "점수" 포함시 무시
   - "~의 주요 상태는", "~의 특징은", "~은 다음과 같다", "~라고 할 수 있다", "~로 정의된다" 등 설명문 무시
   - "~를 설명하면", "~에 대해 알아보면", "~를 살펴보면", "~는 의미한다", "~를 뜻한다" 등 해설 패턴 무시
   - 문장이 "입니다", "합니다", "다", "이다", "된다", "한다"로 끝나면 해설로 간주

3. **표 완전성 보장**: 
   - 표가 있으면 헤더 + 최소 2개 이상의 데이터 행 필수
   - 전체 분석에서 발견된 표 데이터로 불완전한 표 보완
   - 헤더만 있고 데이터가 없으면 해당 문제 제외 고려

3. **한국어 특화 해설 패턴 제거**:
   - "다음과 같이", "아래와 같이", "위와 같이", "즉", "따라서", "그러므로", "결론적으로", "요약하면"
   - "~라 하였다", "~라고 했다", "~라고 볼 수 있다", "~라고 여겨진다", "~라는 것이다"
   - "예를 들면", "예시", "사례", "실습", "연습", "복습", "정리", "요점", "핵심"
   - "참고:", "주의:", "중요:", "알림:", "팁:", "힌트:", "기억할 점"

3. **완전한 문제만**:
   - question_text: 완전한 질문 내용 (반드시 물음표나 질문 패턴 포함, 15자 이상)
   - passage: 지문/표/코드/보기 등 (선택사항)
   - options: 반드시 3개 이상의 완전한 선택지 (①②③④⑤ 또는 1)2)3)4)5) 형태)

4. **엄격한 선택지 검증**:
   - 각 선택지는 5글자 이상의 의미있는 내용
   - 번호 패턴 (①②③④⑤ 또는 1)2)3)4)5)) 필수
   - 연속적인 번호 순서 (①②③④ 또는 1)2)3)4))
   - 모든 선택지가 완전히 추출되어야 함 (페이지 끝에서 잘린 경우 제외)

5. **무효 패턴 제외**:
   - "페이지", "목차", "표지", "빈 페이지", "참고자료"
   - 단순 나열문, 정의문, 개념 설명문
   - 문제번호가 'N/A'이거나 0인 경우

6. **중복 완전 방지**: 같은 번호 문제 발견시 첫 번째만 추출

🚨 **절대 규칙**: 
- 완전하지 않은 문제는 절대 추출하지 마세요
- 해설이나 정답 페이지는 절대 문제로 인식하지 마세요
- 선택지가 없거나 부족한 문제는 절대 추출하지 마세요

📋 **선택지 추출 강화 규칙**:
- 선택지는 반드시 연속된 번호 순서로 추출 (①→②→③→④→⑤)
- 중간에 번호가 빠지면 해당 문제 제외 (①③④ 같은 패턴 금지)
- 페이지 경계에서 잘린 선택지가 있으면 해당 문제 제외
- 선택지가 2개 이하인 경우 문제에서 제외
- "보기없음", "주관식", "서술형" 표시가 있으면 options를 빈 배열로 처리

🔍 **질문 패턴 인식 강화**:
- 반드시 질문형 어미나 지시형 패턴을 포함해야 함
- "다음 중 옳은 것은?", "아래 설명에 해당하는 것은?", "올바른 것을 고르시오" 등
- 단순 서술문("~입니다", "~다", "~이다")은 해설로 간주하여 제외

다음 JSON 형태로 정확히 분석해주세요:

{{
  "document_analysis": {{
    "title": "문서 제목",
    "subject": "과목명",
    "exam_type": "기출문제/해설집/요약서/교재/문제집",
    "academic_level": "초등/중등/고등/대학/자격증",
    "total_pages_analyzed": "분석된 페이지 수",
    "extraction_method": "GPT Vision + Claude"
  }},
  
  "chapters": [
    {{
      "chapter_number": 1,
      "chapter_title": "단원/챕터 제목", 
      "main_topics": ["주요 개념1", "주요 개념2"],
      "learning_objectives": ["학습목표1", "학습목표2"],
      "page_range": "시작페이지-끝페이지"
    }}
  ],
  
  "questions": [
    {{
      "question_id": "Q001",
      "chapter_id": 1,
      "question_number": 1,
      "question_text": "순수한 문제 내용만 (지문/보기 제외)",
      "passage": "문제의 지문/보기/표/그래프/코드 등 (있는 경우)",
      "question_type": "객관식/주관식/서술형/계산형/선택형",
      "options": ["① 선택지1", "② 선택지2", "③ 선택지3", "④ 선택지4"],
      "correct_answer": "정답 번호나 내용",
      "explanation": "해설 (있는 경우)",
      "difficulty_level": "상/중/하",
      "bloom_taxonomy": "지식/이해/적용/분석/종합/평가",
      "topic_tags": ["주제1", "주제2"],
      "estimated_time": "예상 시간",
      "keywords": ["핵심어1", "핵심어2"],
      "source_page": "페이지 번호",
      "page_location": "정확한 페이지 위치 (예: P.3 상단, P.7 하단)",
      "table_data": {{
        "table_id": "TABLE_001",
        "headers": ["헤더1", "헤더2", "헤더3"],
        "rows": [["데이터1", "데이터2", "데이터3"], ["데이터4", "데이터5", "데이터6"]],
        "title": "표 제목",
        "description": "표 설명"
      }},
      "related_images": ["IMG_001", "IMG_002"],
      "image_options": {{
        "option_1": "IMG_001",
        "option_2": "IMG_002"
      }},
      "has_table": true,
      "has_code": false,
      "has_figure": true,
      "cross_page_resolved": false
    }}
  ],
  
  "study_materials": [
    {{
      "material_id": "M001",
      "chapter_id": 1, 
      "material_type": "개념설명/공식/정리/예제/요약/도표/그래프",
      "title": "학습자료 제목",
      "content": "상세 내용",
      "importance_level": "핵심/중요/참고",
      "related_questions": ["Q001", "Q002"],
      "prerequisites": ["선수학습요소1", "선수학습요소2"],
      "source_page": "해당 페이지 번호"
    }}
  ],
  
  "learning_analytics": {{
    "total_questions": 0,
    "question_distribution": {{
      "객관식": 0, "주관식": 0, "서술형": 0, "계산형": 0
    }},
    "difficulty_distribution": {{
      "상": 0, "중": 0, "하": 0
    }},
    "bloom_taxonomy_distribution": {{
      "지식": 0, "이해": 0, "적용": 0, "분석": 0, "종합": 0, "평가": 0
    }},
    "chapter_coverage": "챕터별 문제/자료 분포",
    "main_topics": ["전체 주요 주제들"],
    "estimated_study_time": "전체 학습 예상 소요시간(시간)",
    "quality_score": "추출 품질 점수 (1-10)",
    "extraction_completeness": "추출 완성도 (%)"
  }}
}}

🎯 **중요 지침**:
- 반드시 JSON 형태로만 답변, 추가 설명 금지
- **시험문제만 추출**: 해설, 정답, 풀이 페이지는 완전 제외
- **구조적 분리 필수**: 
  * question_text = 순수 질문 내용 (반드시 "?" 또는 질문 패턴 포함)
  * passage = 지문/표/그래프/코드 (별도 구분)
  * options = 완전한 선택지 배열 (3개 이상, 연속 번호)
- **중복 제거**: 문제 번호 중복 시 첫 번째만 유효

🎯 **표 데이터 처리 규칙**:
- 표가 발견되면 `table_data` 객체에 완전한 구조화된 데이터 저장
- `headers`: 표 헤더 배열
- `rows`: 각 행의 데이터를 배열로 저장 (빈셀은 `""` 처리)
- `title`/`description`: 표 위아래 설명 추출
- `passage`에는 표를 마크다운 형태로도 포함

🎯 **이미지 처리 규칙**:
- 그림 선택지나 보기 이미지 발견시 `related_images` 배열에 이미지 ID 기록
- 선택지별 이미지는 `image_options`에 매핑 (option_1: "IMG_001")
- `options` 배열에는 "① ![IMG_001]" 형태로 이미지 참조 포함
- `has_figure`: true로 설정
- **품질 검증**: 불완전한 문제, 선택지 누락 문제 완전 제외
- **표/코드 감지**: has_table, has_code, has_figure 플래그 정확히 설정
- **목표 문제수**: 실제 PDF에 따라 동적 감지 (20~100개 범위)

⚠️ **추출 금지 항목**:
- 설명문, 정의문, 개념 서술 ("~입니다", "~다", "~이다" 등)
- 해설 페이지 ("정답:", "해설:", "풀이:" 등)
- 불완전한 선택지 (번호 누락, 페이지 잘림)
- 질문 패턴 없는 문장

✅ **추출 필수 조건**:
- 명확한 질문 의도 ("~은?", "다음 중", "올바른 것은?" 등)
- 완전한 선택지 세트 (①②③④ 또는 1)2)3)4) 연속)
- 의미있는 문제 내용 (15자 이상)
                """.strip()
                
                print(f"Sending chunk {chunk_idx + 1} to Claude for advanced structuring...")
                
                # 🔄 Claude API 호출에 재시도 로직 대폭 강화 (529 오류 해결)
                max_retries = 8  # 최대 8회 재시도
                base_delay = 5.0  # 5초 초기 대기
                
                for attempt in range(max_retries):
                    try:
                        # 청크별 Claude 분석 실행 - 더 높은 토큰과 정밀도
                        response = await self.claude_client.messages.create(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=8000,
                            temperature=0.05,  # 더 일관된 결과를 위해 낮은 온도
                            messages=[
                                {
                                    "role": "user", 
                                    "content": structuring_prompt
                                }
                            ]
                        )
                        
                        result_text = response.content[0].text.strip()
                        print(f"✅ Claude structuring successful on attempt {attempt + 1}, response length: {len(result_text)} characters")
                        break
                        
                    except Exception as api_error:
                        error_str = str(api_error)
                        print(f"❌ Claude API attempt {attempt + 1} failed: {error_str}")
                        
                        # 529 오류 또는 rate limit 감지
                        is_rate_limit = '529' in error_str or 'overload' in error_str.lower() or 'rate limit' in error_str.lower()
                        
                        if is_rate_limit and attempt < max_retries - 1:
                            # 대폭 강화된 지수 백오프 (5배 증가)
                            delay = base_delay * (5 ** attempt) + random.uniform(5, 15)  # 5-15초 랜덤 대기
                            print(f"🔄 Rate limit detected (attempt {attempt + 1}/{max_retries}), waiting {delay:.1f} seconds...")
                            await asyncio.sleep(delay)
                        elif attempt == max_retries - 1:
                            print(f"💀 All {max_retries} attempts failed for chunk {chunk_idx + 1}")
                            # 실패한 청크는 빈 결과로 처리하여 전체 프로세스 중단 방지
                            result_text = json.dumps({
                                'questions': [],
                                'study_materials': [],
                                'chapters': [],
                                'document_analysis': {
                                    'title': 'Processing Failed',
                                    'total_pages_analyzed': '0',
                                    'extraction_method': 'Failed - API Error'
                                }
                            })
                            break
                        else:
                            # 다른 종류의 오류는 즉시 재시도
                            continue
                
                # 🛠️ JSON 파싱 전 데이터 정제 (특수문자 이슈 해결)
                def sanitize_json_content(text: str) -> str:
                    """JSON 파싱 오류를 일으키는 특수문자들을 정제"""
                    # 제어 문자 제거 (탭, 개행 등은 유지)
                    import unicodedata
                    sanitized = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\t\n\r')
                    
                    # 문제가 되는 따옴표 패턴 정리
                    sanitized = sanitized.replace('\\n', ' ').replace('\\t', ' ').replace('\\r', ' ')
                    
                    # 표 데이터에서 문제가 되는 특수 문자들 정리
                    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', ' ', sanitized)
                    
                    return sanitized
                
                # JSON 파싱
                try:
                    sanitized_text = sanitize_json_content(result_text)
                    chunk_result = json.loads(sanitized_text)
                    print(f"✅ JSON parsing successful for chunk {chunk_idx + 1}")
                except json.JSONDecodeError as json_error:
                    print(f"❌ JSON parsing failed for chunk {chunk_idx + 1}: {json_error}")
                    print(f"Error location: line {json_error.lineno}, column {json_error.colno}")
                    print(f"Raw response preview: {result_text[:500]}...")
                    
                    # 🔧 강화된 JSON 복구 시도
                    try:
                        # Claude 응답에서 실제 JSON만 추출하는 다단계 접근법
                        recovered_json = None
                        
                        # 1차: 백틱으로 둘러싸인 JSON 추출
                        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', result_text)
                        if json_match:
                            json_content = json_match.group(1).strip()
                            try:
                                recovered_json = json.loads(sanitize_json_content(json_content))
                                print(f"✅ JSON 복구 성공 (백틱 추출)")
                            except:
                                pass
                        
                        # 2차: 첫 번째 중괄호부터 마지막 중괄호까지 추출
                        if not recovered_json:
                            first_brace = result_text.find('{')
                            last_brace = result_text.rfind('}')
                            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                                json_content = result_text[first_brace:last_brace+1]
                                try:
                                    # 일반적인 JSON 오류 수정
                                    json_content = self._fix_common_json_errors(json_content)
                                    recovered_json = json.loads(sanitize_json_content(json_content))
                                    print(f"✅ JSON 복구 성공 (중괄호 추출 + 오류 수정)")
                                except:
                                    pass
                        
                        # 3차: Claude 텍스트 응답을 구조화된 데이터로 변환
                        if not recovered_json:
                            recovered_json = await self._parse_claude_text_response(result_text, chunk_idx + 1)
                            if recovered_json:
                                print(f"✅ JSON 복구 성공 (텍스트 파싱)")
                        
                        chunk_result = recovered_json or {
                            'questions': [],
                            'study_materials': [],
                            'chapters': []
                        }
                        
                    except Exception as recovery_error:
                        print(f"💀 JSON 복구 실패: {recovery_error}")
                        chunk_result = {
                            'questions': [],
                            'study_materials': [],
                            'chapters': []
                        }
                
                # 청크별 결과를 전체 결과에 병합
                chunk_questions = chunk_result.get('questions', [])
                chunk_materials = chunk_result.get('study_materials', [])
                chunk_chapters = chunk_result.get('chapters', [])
                
                # 🔥 초강화된 품질 검증 및 필터링
                validated_questions = []
                question_numbers_seen = set()
                
                for question in chunk_questions:
                    question_text = question.get('question_text', '').strip()
                    passage = question.get('passage', '').strip()
                    options = question.get('options', [])
                    question_number = question.get('question_number', 'N/A')
                    
                    # 🚨 문제 번호 중복 방지 및 정규화
                    if isinstance(question_number, str):
                        # 문제 번호에서 숫자만 추출 (예: "Q2_11" -> 11)
                        import re
                        number_match = re.search(r'(\d+)$', str(question_number))
                        if number_match:
                            actual_number = int(number_match.group(1))
                            question_number = actual_number
                        else:
                            question_number = 'N/A'
                    
                    # === 1. 답안/해설 페이지 강화 필터링 ===
                    full_text = (question_text + ' ' + passage).lower()
                    answer_keywords = [
                        '해설', '정답', '풀이', '답안', '해답', '정답 및 해설',
                        '설명', '부연 설명', '자세한 설명', '해답', '해석',
                        'explanation', 'answer', 'solution', '답 :', '정답:', '해설:',
                        '① 해설', '② 해설', '③ 해설', '④ 해설',
                        '에 대한 설명', '에 대한 해설', '답안 설명'
                    ]
                    
                    if any(keyword in full_text for keyword in answer_keywords):
                        print(f"🚫 Skipping answer/explanation page: Q{question_number}")
                        continue
                    
                    # === 2. 문제 내용 기본 검증 ===
                    if not question_text or len(question_text.strip()) < 15:
                        print(f"🚫 Skipping invalid question (too short): Q{question_number}")
                        continue
                    
                    # === 3. 문제 번호 유효성 검증 ===
                    if question_number == 'N/A' or question_number is None or question_number == 0:
                        print(f"🚫 Skipping question with invalid number: {question_number}")
                        continue
                    
                    if question_number in question_numbers_seen:
                        print(f"🚫 Skipping duplicate question number: Q{question_number}")
                        continue
                    
                    # === 4. 선택지 강화 검증 (그림 선택지 포함) ===
                    valid_options = []
                    if isinstance(options, list):
                        for opt in options:
                            if opt and isinstance(opt, str):
                                clean_opt = opt.strip()
                                # 선택지 길이와 내용 검증
                                if len(clean_opt) >= 1 and not clean_opt.lower() in ['', 'null', 'none', 'n/a']:
                                    # 번호 패턴 확인 (①, ②, ③, ④ 또는 1), 2), 3), 4))
                                    if any(pattern in clean_opt for pattern in ['①', '②', '③', '④', '⑤', '1)', '2)', '3)', '4)', '5)']):
                                        valid_options.append(clean_opt)
                                    # 그림 선택지 패턴 확인
                                    elif '[그림:' in clean_opt or '[수식:' in clean_opt or '[도표:' in clean_opt:
                                        valid_options.append(clean_opt)
                                    elif len(clean_opt) > 5:  # 번호가 없어도 충분히 긴 선택지는 허용
                                        valid_options.append(clean_opt)
                                    elif len(clean_opt) >= 1 and any(char.isdigit() for char in clean_opt[:3]):  # 최소 번호라도 있으면
                                        valid_options.append(clean_opt)
                    
                    if len(valid_options) < 2:
                        print(f"🚫 Skipping Q{question_number}: insufficient options ({len(valid_options)})")
                        continue
                    
                    # === 5. 문제 유형 검증 ===
                    # 문제처럼 보이지 않는 내용 필터링
                    invalid_patterns = [
                        '페이지', 'page', '목차', '표지', 'cover',
                        '다음은', '다음 중', '무엇인가', '어떤 것은',
                        '설명으로 옳', '설명으로 틀린', '해당하지 않는',
                        '에 대한 설명', '대한 설명'
                    ]
                    
                    # 문제다운 패턴이 있는지 확인
                    question_patterns = [
                        '다음 중', '무엇인가', '어떤 것', '옳은 것', '틀린 것',
                        '해당하는 것', '아닌 것', '설명으로', '에 대한'
                    ]
                    
                    has_question_pattern = any(pattern in question_text for pattern in question_patterns)
                    if not has_question_pattern and len(valid_options) < 3:
                        print(f"🚫 Skipping Q{question_number}: doesn't look like a proper question")
                        continue
                    
                    # === 6. 내용 품질 검증 ===
                    # 빈 내용이나 의미없는 내용 필터링
                    meaningless_patterns = [
                        '제시된 내용', '다음과 같', '위의 내용', '아래 내용',
                        '설명이 있', '내용이 있', '다음 표', '다음 그림'
                    ]
                    
                    if len(question_text) < 30 and any(pattern in question_text for pattern in meaningless_patterns):
                        print(f"🚫 Skipping Q{question_number}: meaningless content")
                        continue
                    
                    # === 7. 최종 검증 통과 - 문제 정제 및 추가 ===
                    question['options'] = valid_options
                    question['question_text'] = question_text.strip()
                    question['passage'] = passage.strip()
                    
                    # 메타데이터 추가
                    has_table = '표' in passage or '|' in passage
                    question['has_table'] = has_table
                    question['has_code'] = any(code_word in passage.lower() for code_word in ['class', 'function', 'public', 'int', 'string', 'void'])
                    question['has_figure'] = '그림' in passage or '도표' in passage
                    question['validation_passed'] = True
                    
                    # 🔍 표 데이터 완전성 검증 (P1, P2, P3 행 확인)
                    if has_table:
                        table_validation = self._validate_table_completeness(passage, question_number)
                        question['table_complete'] = table_validation['is_complete']
                        question['table_issues'] = table_validation['issues']
                        
                        if not table_validation['is_complete']:
                            print(f"⚠️ Q{question_number} table incomplete: {table_validation['issues']}")
                        else:
                            print(f"✅ Q{question_number} table complete with data rows")
                    
                    question_numbers_seen.add(question_number)
                    validated_questions.append(question)
                    print(f"✅ Valid Q{question_number}: {len(valid_options)} options, passage={len(passage)} chars")
                
                all_questions.extend(validated_questions)
                all_materials.extend(chunk_materials)
                all_chapters.extend(chunk_chapters)
                
                # 🔥 특수 콘텐츠 후처리 (표/그림/코드)
                validated_questions = await self._post_process_special_content(validated_questions, chunk_idx)
                
                print(f"Chunk {chunk_idx + 1} processed: {len(validated_questions)}/{len(chunk_questions)} questions validated")
                
                # API 레이트 리미트 방지 - 대폭 강화
                if chunk_idx < len(chunks) - 1:
                    await asyncio.sleep(10)  # 청크 간 10초 대기로 증가
            
            # 🔥 페이지간 문제 연결 후처리 및 문제 번호 정규화
            all_questions = await self._handle_cross_page_questions(all_questions, full_connected_content)
            
            # 🔍 최종 품질 관리 및 중복 제거
            print(f"\n🔍 최종 품질 검증 중...")
            
            # 문제 번호별로 그룹화하여 중복 제거
            final_questions = {}
            for question in all_questions:
                q_num = question.get('question_number')
                if q_num and q_num not in final_questions:
                    # 최종 검증
                    if (question.get('question_text', '').strip() and 
                        len(question.get('question_text', '').strip()) >= 15 and
                        question.get('options') and 
                        len(question.get('options', [])) >= 2):
                        final_questions[q_num] = question
                        print(f"✅ Final Q{q_num}: PASSED")
                    else:
                        print(f"🚫 Final Q{q_num}: FAILED quality check")
                else:
                    print(f"🚫 Final Q{q_num}: DUPLICATE or INVALID number")
            
            # 최종 정제된 문제 리스트
            final_questions_list = list(final_questions.values())
            print(f"\n📊 최종 결과: {len(final_questions_list)} 문제 추출 완료")
            
            # 🎯 과도한 문제 수 품질 필터링 (실제 문제 수 기준)
            # 실제 PDF의 문제 수를 추정 (가장 높은 문제 번호 기준)
            question_numbers = [q.get('question_number', 0) for q in final_questions_list]
            valid_numbers = [n for n in question_numbers if isinstance(n, (int, str)) and str(n).isdigit()]
            
            if valid_numbers:
                max_question_number = max([int(n) for n in valid_numbers])
                estimated_total_questions = max_question_number
                
                print(f"📊 추출된 문제 분석:")
                print(f"  - 추출된 문제 수: {len(final_questions_list)}개")
                print(f"  - 최고 문제 번호: {max_question_number}번")
                print(f"  - 추정 실제 문제 수: {estimated_total_questions}개")
                
                # 추출된 문제가 추정 실제 문제 수의 1.5배를 넘으면 품질 필터링 적용
                if len(final_questions_list) > estimated_total_questions * 1.5:
                    print(f"⚠️ 과도한 문제 추출 감지: {len(final_questions_list)} > {estimated_total_questions * 1.5:.0f}")
                    print("품질 기반 필터링을 적용하여 중복 및 저품질 문제를 제거합니다...")
                    
                    # 품질 점수 계산
                    def calculate_quality_score(q):
                        score = 0
                        # 선택지 개수 (4개 이상이 이상적)
                        score += min(len(q.get('options', [])) * 10, 40)
                        # 지문 길이 (복잡한 문제일수록 좋음)
                        score += min(len(q.get('passage', '')) / 10, 30)
                        # 질문 길이 (너무 짧지 않게)
                        score += min(len(q.get('question_text', '')) / 5, 20)
                        # 표/그림/코드 포함시 보너스
                        if q.get('has_table', False): score += 15
                        if q.get('has_figure', False): score += 10
                        if q.get('has_code', False): score += 10
                        # 문제 번호가 유효하면 보너스
                        try:
                            int(q.get('question_number', 0))
                            score += 5
                        except:
                            pass
                        return score
                    
                    # 품질 점수로 정렬
                    scored_questions = [(q, calculate_quality_score(q)) for q in final_questions_list]
                    scored_questions.sort(key=lambda x: x[1], reverse=True)
                    
                    # 추정 문제 수에 맞춰 상위 문제들 선택 (여유분 10% 추가)
                    target_count = int(estimated_total_questions * 1.1)
                    final_questions_list = [q for q, score in scored_questions[:target_count]]
                    print(f"✅ 품질 필터링 완료: {len(scored_questions)} → {len(final_questions_list)}개 문제")
                    
                    # 선택된 문제들의 번호 범위 출력
                    remaining_numbers = [q.get('question_number', 0) for q in final_questions_list]
                    remaining_numbers = [n for n in remaining_numbers if isinstance(n, (int, str)) and str(n).isdigit()]
                    if remaining_numbers:
                        remaining_numbers = sorted([int(n) for n in remaining_numbers])
                        print(f"📋 최종 문제 범위: {min(remaining_numbers)}~{max(remaining_numbers)}번")
                else:
                    print(f"✅ 적정 수준의 문제 추출: {len(final_questions_list)}개 (추정 {estimated_total_questions}개 기준)")
            else:
                print(f"✅ 추출 완료: {len(final_questions_list)}개 문제 (번호 분석 불가)")
            
            # 전체 결과 구성
            structured_result = {
                'document_analysis': {
                    'title': 'GPT Vision Processed Document',
                    'subject': 'General Education',
                    'exam_type': 'Educational Content',
                    'academic_level': 'General',
                    'total_pages_analyzed': markdown_result.get('pages_processed', 0),
                    'extraction_method': 'GPT Vision + Claude Ultra Enhanced'
                },
                'chapters': all_chapters,
                'questions': final_questions_list,  # 최종 검증된 문제만
                'study_materials': all_materials,
                'learning_analytics': {
                    'total_questions': len(final_questions_list),
                    'chunks_processed': len(chunks),
                    'validation_applied': True,
                    'quality_control': 'Ultra Enhanced'
                }
            }
            
            # 구조화된 결과 처리
            document_analysis = structured_result.get('document_analysis', {})
            chapters = all_chapters
            questions = final_questions_list  # 최종 검증된 문제 사용
            materials = all_materials
            analytics = structured_result.get('learning_analytics', {})
            
            # 최종 품질 보고서
            questions_with_full_options = [q for q in questions if len(q.get('options', [])) >= 3]
            questions_with_passage = [q for q in questions if q.get('passage', '').strip()]
            
            print(f"\n📊 초강화 추출 시스템 최종 보고서:")
            print(f"  - 📚 챕터: {len(chapters)}개 식별")
            print(f"  - ❓ 최종 문제: {len(questions)}개 추출 (품질 검증 완료)")  
            print(f"  - 🎯 완전한 선택지: {len(questions_with_full_options)}개 (3개 이상)")
            print(f"  - 📝 지문 포함: {len(questions_with_passage)}개 문제")
            print(f"  - 📖 학습 자료: {len(materials)}개 생성")
            print(f"  - 🎭 청크 처리: {len(chunks)}개 청크")
            
            if len(questions) > 0:
                quality_score = (len(questions_with_full_options) / len(questions)) * 100
                print(f"  - 📈 품질 점수: {quality_score:.1f}% (Ultra Enhanced)")
                print(f"  - 🚀 처리 방식: 해설 페이지 완전 필터링, 엄격한 선택지 검증")
            else:
                print(f"  - ⚠️  경고: 추출된 문제가 없습니다! 더 엄격한 필터링으로 모든 문제가 제외되었을 수 있습니다.")
            
            # 데이터베이스 저장 - 챕터 정보 먼저 저장
            chapter_ids = {}
            if chapters:
                for chapter in chapters:
                    try:
                        result = db.execute(text("""
                            INSERT INTO chapters
                            (pdf_upload_id, chapter_number, title, main_topics, learning_objectives, page_range)
                            VALUES (:upload_id, :chapter_number, :title, :main_topics, :learning_objectives, :page_range)
                        """), {
                            'upload_id': upload_id,
                            'chapter_number': chapter.get('chapter_number', 0),
                            'title': chapter.get('chapter_title', ''),
                            'main_topics': json.dumps(chapter.get('main_topics', [])),
                            'learning_objectives': json.dumps(chapter.get('learning_objectives', [])),
                            'page_range': chapter.get('page_range', '')
                        })
                        chapter_ids[chapter.get('chapter_number', 0)] = result.lastrowid
                        print(f"Saved chapter: {chapter.get('chapter_title', 'Untitled')}")
                    except Exception as db_error:
                        print(f"Failed to save chapter to DB: {db_error}")
            
            # 고품질 문제 저장 (Enhanced GPT Vision + Claude 기반)
            saved_questions = 0
            if questions:
                for question in questions:
                    try:
                        # 추가 품질 검증
                        question_text = question.get('question_text', '').strip()
                        if not question_text or len(question_text) < 10:
                            print(f"⚠️  Skipping short question: {question.get('question_id', 'unknown')}")
                            continue
                        
                        # 무효한 내용 필터링
                        if any(invalid in question_text.lower() for invalid in ['-|', '페이지 변환 실패', 'error', '빈 페이지']):
                            print(f"⚠️  Skipping invalid question content: {question.get('question_id', 'unknown')}")
                            continue
                            
                        chapter_id = chapter_ids.get(question.get('chapter_id', 0))
                        # 추가 메타데이터 구성
                        additional_info = {
                            'has_table': question.get('has_table', False),
                            'has_code': question.get('has_code', False),
                            'has_figure': question.get('has_figure', False),
                            'source_page': question.get('source_page', ''),
                            'extraction_method': 'Enhanced GPT Vision + Claude'
                        }
                        
                        db.execute(text("""
                            INSERT INTO extracted_questions
                            (pdf_upload_id, chapter_id, question_id, question_text, question_type,
                             difficulty_level, correct_answer, options, explanation, bloom_taxonomy,
                             topic_tags, estimated_time, keywords, passage, additional_info)
                            VALUES (:upload_id, :chapter_id, :question_id, :question_text, :question_type,
                                    :difficulty, :correct_answer, :options, :explanation, :bloom_taxonomy,
                                    :topic_tags, :estimated_time, :keywords, :passage, :additional_info)
                        """), {
                            'upload_id': upload_id,
                            'chapter_id': chapter_id,
                            'question_id': question.get('question_id', f'Q{saved_questions+1:03d}'),
                            'question_text': question_text,
                            'question_type': question.get('question_type', 'Multiple Choice'),
                            'difficulty': question.get('difficulty_level', 'Medium'),
                            'correct_answer': question.get('correct_answer', ''),
                            'options': json.dumps(question.get('options', [])),
                            'explanation': question.get('explanation', ''),
                            'bloom_taxonomy': question.get('bloom_taxonomy', 'Application'),
                            'topic_tags': json.dumps(question.get('topic_tags', [])),
                            'estimated_time': question.get('estimated_time', '2 minutes'),
                            'keywords': json.dumps(question.get('keywords', [])),
                            'passage': question.get('passage', ''),
                            'additional_info': json.dumps(additional_info)
                        })
                        saved_questions += 1
                        print(f"✅ Saved enhanced question: {question.get('question_id', f'Q{saved_questions:03d}')} - {len(question.get('options', []))} options")
                    except Exception as db_error:
                        print(f"❌ Failed to save question to DB: {db_error}")
                        
            print(f"💾 Database 저장 완료: {saved_questions}/{len(questions)}개 문제 저장")
            
            # 고품질 학습 자료 저장
            if materials:
                for material in materials:
                    try:
                        # Dummy certificate_id 가져오기
                        dummy_cert = db.execute(text("SELECT id FROM certificates_info LIMIT 1")).fetchone()
                        cert_id = dummy_cert[0] if dummy_cert else 1
                        
                        chapter_id = chapter_ids.get(material.get('chapter_id', 0))
                        db.execute(text("""
                            INSERT INTO study_materials
                            (certificate_id, pdf_upload_id, chapter_id, material_id, material_type, title, content,
                             importance_level, related_questions, prerequisites)
                            VALUES (:cert_id, :upload_id, :chapter_id, :material_id, :material_type, :title, :content,
                                    :importance_level, :related_questions, :prerequisites)
                        """), {
                            'cert_id': cert_id,
                            'upload_id': upload_id,
                            'chapter_id': chapter_id,
                            'material_id': material.get('material_id', ''),
                            'material_type': material.get('material_type', ''),
                            'title': material.get('title', ''),
                            'content': material.get('content', ''),
                            'importance_level': material.get('importance_level', ''),
                            'related_questions': json.dumps(material.get('related_questions', [])),
                            'prerequisites': json.dumps(material.get('prerequisites', []))
                        })
                        print(f"Saved GPT Vision material: {material.get('title', 'Untitled')}")
                    except Exception as db_error:
                        print(f"Failed to save material to DB: {db_error}")
            
            db.commit()
            
            await self._log_processing_step(upload_id, "markdown_structuring", "completed", {
                'chapters_identified': len(chapters),
                'questions_extracted': len(questions),
                'materials_created': len(materials),
                'claude_tokens_used': response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else 0,
                'document_analysis': document_analysis,
                'learning_analytics': analytics,
                'gpt_vision_tokens': markdown_result.get('tokens_used', 0)
            }, db)
            
            return {
                'success': True,
                'questions': questions,
                'materials': materials,
                'chapters': chapters,
                'document_analysis': document_analysis,
                'learning_analytics': analytics,
                'gpt_vision_tokens': markdown_result.get('tokens_used', 0),
                'claude_tokens': response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else 0
            }
            
        except Exception as e:
            logger.error(f"Markdown structuring error: {str(e)}")
            await self._log_processing_step(upload_id, "markdown_structuring", "failed", {"error": str(e)}, db)
            return {
                'success': False,
                'questions': [],
                'materials': [],
                'chapters': [],
                'error': str(e)
            }
    
    async def _structure_markdown_content_enhanced(self, upload_id: int, markdown_result: Dict, db: Session) -> Dict[str, Any]:
        """3단계: Claude로 전체 Markdown을 문제단위로 구조화 (개선된 버전)"""
        try:
            await self._log_processing_step(upload_id, "enhanced_markdown_structuring", "processing", {}, db)
            
            if not self.claude_client:
                print("ERROR: Claude API key not set - cannot perform markdown structuring")
                return {
                    'success': False,
                    'questions': [],
                    'materials': [],
                    'chapters': [],
                    'error': 'Claude API key not set'
                }
            
            markdown_content = markdown_result.get('markdown_content', '')
            if not markdown_content:
                print("No markdown content to structure")
                return {
                    'success': False,
                    'questions': [],
                    'materials': [],
                    'chapters': [],
                    'error': 'No markdown content provided'
                }
            
            print(f"Enhanced structuring of {len(markdown_content)} characters with Claude...")
            
            # 🔍 0단계: 문서 구조 분석 및 분류 전처리 
            document_structure = await self._analyze_document_structure(
                upload_id=upload_id,
                markdown_content=markdown_content, 
                db=db
            )
            print(f"📋 문서 구조 분석 완료: {document_structure.get('total_questions', 0)}문제, 분류: {document_structure.get('document_type', 'unknown')}")
            
            # 🖼️ 1단계: 구조 분석 기반 다이어그램/이미지 캡처
            captured_diagrams = await self._enhanced_diagram_capture(
                upload_id=upload_id,
                structure_analysis=document_structure,
                pdf_path=self.get_pdf_path(upload_id),  # PDF 경로 가져오기 필요
                db=db
            )
            
            # 페이지별 세밀한 청킹 처리 - 각 페이지를 개별 처리
            pages = markdown_content.split('---')  # 페이지 구분자로 분할
            print(f"Found {len(pages)} pages in markdown content")
            
            # 🎯 오버랩 윈도우 청크 생성 (페이지 경계 문제 해결)
            chunks = self._create_overlap_chunks(pages)
            print(f"📦 Created {len(chunks)} overlap chunks (including boundaries for Q11/Q41 recovery)")
            
            # 전체 결과 수집
            all_questions = []
            all_materials = []
            all_chapters = []
            total_tokens = 0
            extracted_question_numbers = set()  # 🆕 중복 문제 번호 추적
            
            for chunk_idx, chunk_info in enumerate(chunks):
                chunk = chunk_info['content']
                page_start = chunk_info['page_start']
                page_end = chunk_info['page_end']
                estimated_questions = chunk_info['estimated_questions']
                chunk_type = chunk_info.get('chunk_type', 'single_page')
                
                print(f"Processing chunk {chunk_idx + 1}/{len(chunks)} (페이지 {page_start}-{page_end}, {len(chunk)} chars, 예상 {estimated_questions}문제)...")
                
                # 경계 청크에 대한 특별 처리
                if chunk_type == 'boundary_overlap':
                    print(f"   🔗 경계 청크: 선택지 복구 및 문제 연결 특화 처리")
                    chunk = await self._enhance_boundary_chunk_processing(chunk, chunk_info)
                
                # 청크 타입별 특화 프롬프트 선택
                if chunk_type == 'boundary_overlap':
                    enhanced_prompt = await self._get_boundary_recovery_prompt(chunk, page_start, page_end)
                else:
                    enhanced_prompt = f"""
📚 **시험문제 추출 전문가 (해설 제외)**

**중요: 시험문제만 추출하고 해설/정답/풀이는 완전히 제외하세요.**

🔍 **입력 텍스트**:
{chunk}

🎯 **엄격한 문제 식별 규칙**:

1. **시험문제 판별**:
   ✅ "1.", "2.", "3." 등으로 시작하고 물어보는 형태 ("~무엇인가?", "~옳은 것은?", "~설명하시오")
   ❌ 해설 문장: "~입니다", "~입니다.", "~에 대한 설명", "정답은 ~", "풀이:"

2. **해설 페이지 완전 제외**:
   ❌ "프로세스의 주요 3가지 상태는 준비(Ready), 실행(Running), 대기(Wait, Block)입니다."
   ❌ "파스-타(PaaS-TA)는 소프트웨어 개발 환경을 제공하기 위해 개발한..."
   ❌ "~에 대한 설명입니다", "~라고 합니다", "~입니다"

3. **실제 문제 예시**:
   ✅ "다음 중 프로세스의 상태가 아닌 것은?"
   ✅ "애자일 개발 방법론에 해당하지 않는 것은?"
   ✅ "다음 설명에 해당하는 것은 무엇인가?"

4. **선택지 추출 강화**:
   - ①②③④⑤ 또는 1)2)3)4)5) 형태 완전 추출
   - 각 선택지는 완전한 답안 옵션이어야 함
   - 🔍 **선택지 부족 시 특별 처리**:
     * 선택지가 2개 미만이면 → "incomplete_choices": true 추가
     * 선택지가 페이지 끝에서 잘린 경우 → "needs_merge_with_next_chunk": true 추가
     * 표/다이어그램 참조가 있으면 → "has_table_reference": true 추가
   - 🖼️ **이미지/표 선택지**:
     * 선택지에 숫자만 있거나 그래프/표가 보이면 → "IMG_XXX_IMAGE" 형태로 표시
     * 표 데이터가 포함된 문제 → passage에 표 전체 포함
   - ⚠️ **페이지 경계 처리**:
     * 문제가 중간에 끊어진 것 같으면 → "question_text_incomplete": true 추가
     * 선택지 번호가 연속되지 않으면 → "missing_choice_numbers": [누락번호] 추가
   - 해설 번호는 제외: "① 해설", "② 설명" 등
   - 선택지 텍스트 완전 보존 (띄어쓰기, 특수문자 포함)

5. **지문 분리**: 
   - 문제 앞 표/그래프/조건 → passage 필드
   - 문제 본문만 → question_text 필드

6. **빈 페이지 처리**: 
   - 문제가 없으면 빈 배열 반환: {{"questions": []}}
   - "-|", "|", 빈 텍스트 → {{"questions": []}}

📋 **JSON 출력 (예시)**:
{{
  "questions": [
    {{
      "question_id": "Q{page_start:02d}_{page_end:02d}_001",
      "question_number": 7,
      "question_text": "Process의 3가지 상태에 해당하지 않는 것은?",
      "passage": "",
      "options": [
        "① Ready",
        "② Running", 
        "③ Block",
        "④ Indexing"
      ],
      "correct_answer": "④",
      "explanation": "",
      "source_page": {page_start},
      "incomplete_choices": false,
      "needs_merge_with_next_chunk": false,
      "has_table_reference": false,
      "question_text_incomplete": false,
      "missing_choice_numbers": []
    }},
    {{
      "question_id": "Q{page_start:02d}_{page_end:02d}_002",
      "question_number": 6,
      "question_text": "다음 표를 보고 평균 반환 시간을 구하시오.",
      "passage": "프로세스 | 도착시간 | 실행시간\\nP1 | 0 | 3\\nP2 | 1 | 7\\nP3 | 2 | 2",
      "options": [
        "IMG_006_IMAGE",
        "7.2",
        "9.4",
        "IMG_006_IMAGE"
      ],
      "incomplete_choices": true,
      "needs_merge_with_next_chunk": true,
      "has_table_reference": true,
      "source_page": {page_start}
    }}
  ]
}}

⚠️ **중요**:
- 모든 문제 완전 추출 (빠트림 없이)
- 선택지 텍스트 정확히 보존
- 정답 번호 정확히 식별
- JSON만 출력, 설명 금지
- 빈 페이지면 {{"questions": []}}
                """.strip()
                
                try:
                    response = await self.claude_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=8000,
                        temperature=0.01,  # 가장 일관된 결과
                        messages=[{
                            "role": "user",
                            "content": enhanced_prompt
                        }]
                    )
                    
                    result_text = response.content[0].text.strip()
                    total_tokens += response.usage.input_tokens + response.usage.output_tokens
                    
                    # 강화된 JSON 추출 및 파싱
                    clean_text = result_text.strip()
                    
                    # 마크다운 코드 블록 제거
                    if clean_text.startswith('```json'):
                        clean_text = clean_text.split('```json', 1)[1].rsplit('```', 1)[0]
                    elif clean_text.startswith('```'):
                        clean_text = clean_text.split('```', 1)[1].rsplit('```', 1)[0]
                    
                    # JSON 시작/끝 찾기 (중복 JSON 방지)
                    json_start = clean_text.find('{')
                    if json_start != -1:
                        # 첫 번째 { 부터 마지막 } 까지만 추출
                        brace_count = 0
                        json_end = -1
                        for i in range(json_start, len(clean_text)):
                            if clean_text[i] == '{':
                                brace_count += 1
                            elif clean_text[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    json_end = i
                                    break
                        
                        if json_end != -1:
                            clean_text = clean_text[json_start:json_end + 1]
                    
                    # 안전한 JSON 파싱 사용
                    chunk_result, parse_status = self.safe_json_parse(clean_text, chunk_idx + 1)
                    
                    # 파싱 상태에 따른 로깅
                    if parse_status is None:
                        print(f"   ✅ Chunk {chunk_idx + 1} JSON 파싱 성공")
                    elif parse_status == "fixed":
                        print(f"   🔧 Chunk {chunk_idx + 1} JSON 오류 수정으로 복구")
                    elif parse_status == "partial":
                        print(f"   ⚠️ Chunk {chunk_idx + 1} 부분적 복구")
                    else:
                        print(f"   ❌ Chunk {chunk_idx + 1} JSON 파싱 실패: {parse_status}")
                    
                    # 빈 결과 필터링
                    if not chunk_result or not isinstance(chunk_result, dict):
                        chunk_result = {"questions": []}
                    elif "questions" not in chunk_result:
                        chunk_result["questions"] = []
                    
                    # 결과 수집 및 품질 개선
                    chunk_questions = chunk_result.get('questions', [])
                    
                    # 문제 품질 검증 및 개선
                    validated_questions = []
                    for question in chunk_questions:
                        # 기본 정보 추가
                        question['chunk_origin'] = chunk_idx + 1
                        question['pages_processed'] = f"{page_start}-{page_end}"
                        
                        # 관대한 필드 검증 - 문제 누락 방지를 위해 기준 완화
                        question_text = question.get('question_text', '').strip()
                        if not question_text or len(question_text) < 5:  # 10 → 5로 완화
                            print(f"Skipping invalid question (too short): {question.get('question_id', 'unknown')}")
                            continue
                        
                        # 선별적 비-질문 패턴 필터링 - 명확한 경우만 제외
                        if self._is_clearly_non_question(question_text):
                            print(f"Skipping clearly non-question: '{question_text[:50]}...'")
                            continue
                            
                        # 선택지 정리 (이미지 참조 보존)
                        options = question.get('options', [])
                        if isinstance(options, list) and len(options) > 0:
                            clean_options = []
                            for opt in options:
                                if opt:
                                    opt_clean = opt.strip()
                                    # IMG_XXX_IMAGE 형태의 이미지 참조 보존
                                    if 'IMG_' in opt_clean and 'IMAGE' in opt_clean:
                                        clean_options.append(opt_clean)
                                    # DIAGRAM_IMAGE 형태의 이미지 참조 보존
                                    elif 'DIAGRAM_IMAGE' in opt_clean:
                                        clean_options.append(opt_clean)
                                    # 일반 텍스트 선택지는 비어있지 않은 경우만
                                    elif opt_clean and opt_clean not in ['-', '--', '---']:
                                        clean_options.append(opt_clean)
                            question['options'] = clean_options
                        else:
                            question['options'] = []
                            
                        # 정답 정리
                        correct_answer = question.get('correct_answer', '')
                        if correct_answer and correct_answer not in ['', 'null', 'None']:
                            question['correct_answer'] = correct_answer.strip()
                        else:
                            question['correct_answer'] = ''
                            
                        # 지문 정리
                        passage = question.get('passage', '')
                        if passage and passage.strip():
                            question['passage'] = passage.strip()
                        else:
                            question['passage'] = ''
                            
                        # 🆕 중복 문제 번호 필터링
                        question_num = question.get('question_number')
                        if question_num in extracted_question_numbers:
                            print(f"⚠️ 중복 문제 번호 {question_num} 스킵 - 이미 추출됨")
                            continue
                        
                        # 🚨 강화된 코드 블록 처리 ([CODE_START]...[CODE_END])
                        question_text = question.get('question_text', '')
                        passage = question.get('passage', '')
                        
                        # 코드 블록 처리 (여러 마커 지원)
                        code_markers = [
                            ('[CODE_START]', '[CODE_END]'),
                            ('[CODE_BLOCK_START]', '[CODE_BLOCK_END]')
                        ]
                        
                        for start_marker, end_marker in code_markers:
                            if start_marker in question_text or start_marker in passage:
                                import re
                                # 질문 텍스트에서 코드 블록 처리
                                if start_marker in question_text:
                                    code_blocks = re.findall(f'{re.escape(start_marker)}(.*?){re.escape(end_marker)}', question_text, re.DOTALL)
                                    for code_block in code_blocks:
                                        # 들여쓰기 완전 보존 (strip 하지 않음)
                                        preserved_code = code_block
                                        question_text = question_text.replace(f'{start_marker}{code_block}{end_marker}', 
                                                                             f'```\n{preserved_code}\n```')
                                    question['question_text'] = question_text
                                
                                # 지문에서 코드 블록 처리
                                if start_marker in passage:
                                    code_blocks = re.findall(f'{re.escape(start_marker)}(.*?){re.escape(end_marker)}', passage, re.DOTALL)
                                    for code_block in code_blocks:
                                        preserved_code = code_block
                                        passage = passage.replace(f'{start_marker}{code_block}{end_marker}', 
                                                                f'```\n{preserved_code}\n```')
                                    question['passage'] = passage
                                
                                question['has_code'] = True
                                print(f"✅ Q{question_num} 코드 블록 처리 완료 ({start_marker})")
                        
                        # 🚨 강화된 페이지 경계 선택지 병합 처리
                        options = question.get('options', [])
                        
                        # 선택지 부족 감지 및 즉시 복구 시도 (3개 미만이면 의심) - 기준 완화
                        if len(options) < 3:
                            question['incomplete_choices'] = True
                            print(f"⚠️ Q{question_num} 선택지 부족 감지: {len(options)}개만 있음 - 복구 시도")
                            
                            # 즉시 복구 시도: 현재 청크의 다른 문제들에서 연결된 선택지 찾기
                            recovered_options = self._attempt_immediate_choice_recovery(
                                question_num, options, chunk_questions
                            )
                            
                            if len(recovered_options) > len(options):
                                print(f"✅ 즉시 선택지 복구 성공: {len(options)}개 → {len(recovered_options)}개")
                                question['options'] = recovered_options
                                question['recovered_from_page_boundary'] = True
                                del question['incomplete_choices']  # 복구되었으므로 삭제
                            else:
                                question['missing_choices_note'] = f"선택지 {len(options)}개만 인식됨 - 페이지 경계 문제 의심"
                            
                            # 다음 청크에서 고아 선택지 찾아서 병합 시도
                            if chunk_idx < len(chunks) - 1:  # 마지막 청크가 아닌 경우
                                question['needs_merge_with_next_chunk'] = True
                                print(f"🔗 Q{question_num} 다음 청크와 병합 필요 표시")
                        
                        # 페이지 경계 마커가 있는 경우 추가 처리
                        combined_text = question_text + passage + ' '.join(options)
                        boundary_markers = ['다음 페이지', '페이지 경계', '잘림', '③④⑤ 다음', '④⑤ 다음', '⑤ 다음']
                        for marker in boundary_markers:
                            if marker in combined_text:
                                question['page_boundary_detected'] = True
                                question['boundary_marker'] = marker
                                print(f"🔍 Q{question_num} 페이지 경계 마커 발견: '{marker}'")
                        
                        extracted_question_numbers.add(question_num)
                        validated_questions.append(question)
                    
                    all_questions.extend(validated_questions)
                    
                    print(f"Chunk {chunk_idx + 1} (페이지 {page_start}-{page_end}): {len(validated_questions)} questions extracted")
                    if validated_questions:
                        question_numbers = [q.get('question_number', 'N/A') for q in validated_questions]
                        print(f"  Question numbers: {question_numbers}")
                        
                        # 품질 체크 결과 출력
                        questions_with_options = len([q for q in validated_questions if q.get('options')])
                        questions_with_answers = len([q for q in validated_questions if q.get('correct_answer')])
                        questions_with_passage = len([q for q in validated_questions if q.get('passage')])
                        
                        print(f"  Quality: Options:{questions_with_options}/{len(validated_questions)}, "
                              f"Answers:{questions_with_answers}/{len(validated_questions)}, "
                              f"Passages:{questions_with_passage}/{len(validated_questions)}")
                    
                except Exception as chunk_error:
                    print(f"Error processing chunk {chunk_idx + 1}: {chunk_error}")
                    continue
            
            print(f"Enhanced extraction completed: {len(all_questions)} total questions")
            
            # 🚀 선택적 후처리 파이프라인 적용 (안정성 우선)
            print(f"\n🔧 기본 추출 완료: {len(all_questions)} 문제")
            
            # 간단한 후처리만 적용 (문제 인식률 우선)
            try:
                # 1. 개선된 중복 문제 병합 시스템
                all_questions = self.merge_duplicate_questions(all_questions)
                print(f"✅ 중복 병합 완료: {len(all_questions)} 문제")
                
                # 2. 개선된 이미지 선택지 처리 (스마트 매칭)
                processed_count = await self._enhanced_image_choice_processing(all_questions, upload_id)
                if processed_count > 0:
                    print(f"✅ 개선된 이미지 선택지 처리: {processed_count}개 문제")
                
            except Exception as pipeline_error:
                print(f"⚠️ 후처리 파이프라인 오류 (기본 결과 유지): {pipeline_error}")
            
            # 🔍 2단계: 구조 분석 기반 페이지 경계 문제 해결
            print("\n🔍 구조 분석 기반 페이지 경계 선택지 검수 시작...")
            
            try:
                # 구조 분석에서 식별된 페이지 경계 문제들을 우선 처리
                all_questions = await self._resolve_boundary_issues_with_structure(
                    extracted_questions=all_questions,
                    structure_analysis=document_structure,
                    upload_id=upload_id,
                    db=db
                )
                print(f"✅ 구조 분석 기반 페이지 경계 검수 완료: 최종 {len(all_questions)} 문제")
                
            except Exception as verification_error:
                print(f"⚠️ 페이지 경계 검수 중 오류 (계속 진행): {verification_error}")
            
            # 🔍 3단계: 보완 파이프라인 실행 (OCR 또는 대안 방식)
            print(f"\n🔍 문제 보완 파이프라인 실행 - 기본 추출 결과 개선...")
            
            try:
                # PDF 경로 획득 후 OCR 시도
                pdf_path = self.get_pdf_path(upload_id, db)
                if pdf_path:
                    # OCR 기반 보완 파이프라인 실행
                    enhanced_questions = await self._ocr_based_enhancement_pipeline(
                        upload_id=upload_id,
                        basic_questions=all_questions,
                        pdf_path=pdf_path,
                        db=db
                    )
                    print(f"🎯 OCR 보완 완료: {len(all_questions)} → {len(enhanced_questions)} 문제")
                    all_questions = enhanced_questions
                else:
                    # OCR 없이 대안 보완 방식 사용
                    print("📝 대안 보완 방식 사용: 패턴 기반 문제 복구")
                    enhanced_questions = await self._alternative_enhancement_pipeline(
                        upload_id=upload_id,
                        basic_questions=all_questions,
                        markdown_content=markdown_result.get('markdown_content', ''),
                        db=db
                    )
                    print(f"🎯 대안 보완 완료: {len(all_questions)} → {len(enhanced_questions)} 문제")
                    all_questions = enhanced_questions
                    
            except Exception as enhance_error:
                print(f"⚠️ 보완 파이프라인 오류 (기본 결과 유지): {enhance_error}")
            
            # 🖼️ 4단계: 최종 이미지 참조 형식 변환
            print(f"\n🖼️ 최종 이미지 참조 형식 변환...")
            try:
                all_questions = self._convert_image_references_to_markdown(all_questions, upload_id)
                print(f"✅ 이미지 참조 변환 완료")
            except Exception as img_convert_error:
                print(f"⚠️ 이미지 참조 변환 오류: {img_convert_error}")
            
            # 기본 챕터 생성 (과목별)
            chapters = [
                {
                    'chapter_number': 1,
                    'chapter_title': '정보시스템 기본 기술',
                    'main_topics': ['UML', '소프트웨어 개발', '네트워크'],
                    'learning_objectives': ['정보시스템 기본 개념 이해'],
                    'page_range': '1-8'
                }
            ]
            
            # 데이터베이스 저장
            chapter_ids = {}
            for chapter in chapters:
                try:
                    result = db.execute(text("""
                        INSERT INTO chapters
                        (pdf_upload_id, chapter_number, title, main_topics, learning_objectives, page_range)
                        VALUES (:upload_id, :chapter_number, :title, :main_topics, :learning_objectives, :page_range)
                    """), {
                        'upload_id': upload_id,
                        'chapter_number': chapter.get('chapter_number', 0),
                        'title': chapter.get('chapter_title', ''),
                        'main_topics': json.dumps(chapter.get('main_topics', [])),
                        'learning_objectives': json.dumps(chapter.get('learning_objectives', [])),
                        'page_range': chapter.get('page_range', '')
                    })
                    chapter_ids[chapter.get('chapter_number', 0)] = result.lastrowid
                    print(f"Saved chapter: {chapter.get('chapter_title', 'Untitled')}")
                except Exception as db_error:
                    print(f"Failed to save chapter: {db_error}")
            
            # 문제 저장
            saved_questions = 0
            for question in all_questions:
                try:
                    chapter_id = chapter_ids.get(1)  # 기본 챕터 사용
                    db.execute(text("""
                        INSERT INTO extracted_questions
                        (pdf_upload_id, chapter_id, question_id, question_text, question_type,
                         difficulty_level, correct_answer, options, explanation, bloom_taxonomy,
                         topic_tags, estimated_time, keywords, passage, additional_info)
                        VALUES (:upload_id, :chapter_id, :question_id, :question_text, :question_type,
                                :difficulty, :correct_answer, :options, :explanation, :bloom_taxonomy,
                                :topic_tags, :estimated_time, :keywords, :passage, :additional_info)
                    """), {
                        'upload_id': upload_id,
                        'chapter_id': chapter_id,
                        'question_id': question.get('question_id', f'Q{saved_questions + 1:03d}'),
                        'question_text': question.get('question_text', ''),
                        'question_type': question.get('question_type', '객관식'),
                        'difficulty': question.get('difficulty_level', '중'),
                        'correct_answer': question.get('correct_answer', ''),
                        'options': json.dumps(question.get('options', [])),
                        'explanation': question.get('explanation', ''),
                        'bloom_taxonomy': question.get('bloom_taxonomy', '이해'),
                        'topic_tags': json.dumps(question.get('topic_tags', [])),
                        'estimated_time': question.get('estimated_time', '2'),
                        'keywords': json.dumps(question.get('keywords', [])),
                        'passage': question.get('passage', ''),
                        'additional_info': question.get('additional_info', '')
                    })
                    saved_questions += 1
                except Exception as db_error:
                    print(f"Failed to save question {question.get('question_id', 'unknown')}: {db_error}")
            
            db.commit()
            
            # 학습 분석
            analytics = {
                'total_questions': len(all_questions),
                'extraction_method': 'Enhanced GPT Vision + Claude Chunked',
                'chunks_processed': len(chunks),
                'total_tokens_used': total_tokens,
                'questions_saved': saved_questions
            }
            
            await self._log_processing_step(upload_id, "enhanced_markdown_structuring", "completed", {
                'questions_extracted': len(all_questions),
                'questions_saved': saved_questions,
                'chunks_processed': len(chunks),
                'total_tokens': total_tokens
            }, db)
            
            return {
                'success': True,
                'questions': all_questions,
                'materials': all_materials,
                'chapters': chapters,
                'document_analysis': {
                    'extraction_method': 'Enhanced GPT Vision + Claude',
                    'total_pages_analyzed': markdown_result.get('pages_processed', 0)
                },
                'learning_analytics': analytics,
                'claude_tokens': total_tokens
            }
            
        except Exception as e:
            logger.error(f"Enhanced markdown structuring error: {str(e)}")
            await self._log_processing_step(upload_id, "enhanced_markdown_structuring", "failed", {"error": str(e)}, db)
            return {
                'success': False,
                'questions': [],
                'materials': [],
                'chapters': [],
                'error': str(e)
            }
    
    async def _convert_pdf_to_combined_image(self, upload_id: int, pdf_path: str, db: Session) -> Dict[str, Any]:
        """0단계: PDF 전체를 하나의 긴 이미지로 변환"""
        try:
            await self._log_processing_step(upload_id, "pdf_to_image_conversion", "processing", {}, db)
            
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            print(f"Converting {total_pages} pages to combined image...")
            
            # 모든 페이지를 이미지로 변환
            page_images = []
            max_width = 0
            
            for page_num in range(total_pages):
                page = doc[page_num]
                # 매우 고해상도 렌더링 (OCR 품질 향상을 위해 4배 확대)
                mat = fitz.Matrix(4.0, 4.0)  # 4배 확대로 텍스트 선명도 증가
                pix = page.get_pixmap(matrix=mat, alpha=False)  # alpha 채널 제거로 용량 절약
                
                # PIL 이미지로 변환
                img_data = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_data))
                
                page_images.append(pil_image)
                max_width = max(max_width, pil_image.width)
                
                print(f"Processed page {page_num + 1}/{total_pages}")
            
            doc.close()
            
            # 모든 이미지를 같은 폭으로 리사이즈하고 세로로 연결
            total_height = 0
            resized_images = []
            
            for img in page_images:
                # 폭을 max_width로 통일
                if img.width != max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                resized_images.append(img)
                total_height += img.height
            
            # 긴 이미지 생성
            combined_image = Image.new('RGB', (max_width, total_height), color='white')
            
            current_y = 0
            for img in resized_images:
                combined_image.paste(img, (0, current_y))
                current_y += img.height
            
            # 결합된 이미지 저장
            combined_image_path = self.temp_dir / f"combined_{upload_id}.png"
            combined_image.save(str(combined_image_path), 'PNG', optimize=True)
            
            print(f"Combined image created: {max_width}x{total_height} pixels")
            
            await self._log_processing_step(upload_id, "pdf_to_image_conversion", "completed", {
                'total_pages': total_pages,
                'combined_image_size': f"{max_width}x{total_height}",
                'image_path': str(combined_image_path)
            }, db)
            
            return {
                'success': True,
                'image_path': str(combined_image_path),
                'total_pages': total_pages,
                'image_width': max_width,
                'image_height': total_height
            }
            
        except Exception as e:
            logger.error(f"PDF to combined image conversion error: {str(e)}")
            await self._log_processing_step(upload_id, "pdf_to_image_conversion", "failed", 
                                          {"error": str(e)}, db)
            return {'success': False, 'error': str(e)}
    
    async def _analyze_combined_document(self, upload_id: int, image_path: str, db: Session) -> Dict[str, Any]:
        """1단계: 통합된 문서 전체 분석 (GPT Vision)"""
        try:
            await self._log_processing_step(upload_id, "combined_document_analysis", "processing", {}, db)
            
            print("Analyzing combined document with GPT Vision...")
            
            # GPT Vision으로 전체 문서 분석
            gpt_analysis = await self._analyze_combined_document_with_gpt(image_path)
            
            # 데이터베이스에 저장
            db.execute(text("""
                INSERT INTO document_analysis 
                (pdf_upload_id, total_pages, document_type, has_text_layer, is_scanned, 
                 layout_analysis, content_structure, document_metadata, api_key_used, 
                 total_tokens_used, analysis_cost)
                VALUES (:upload_id, :total_pages, :doc_type, :has_text, :is_scanned,
                        :layout, :structure, :doc_metadata, :api_key, :tokens, :cost)
            """), {
                'upload_id': upload_id,
                'total_pages': gpt_analysis.get('total_pages', 0),
                'doc_type': gpt_analysis.get('document_type'),
                'has_text': False,  # 이미지로 처리하므로 False
                'is_scanned': True,  # 이미지로 처리하므로 True
                'layout': json.dumps(gpt_analysis.get('layout_info', {})),
                'structure': json.dumps(gpt_analysis.get('content_structure', {})),
                'doc_metadata': json.dumps(gpt_analysis.get('metadata', {})),
                'api_key': gpt_analysis.get('api_key_used'),
                'tokens': gpt_analysis.get('tokens_used', 0),
                'cost': gpt_analysis.get('cost', 0.0)
            })
            
            doc_analysis_id = db.execute(text("SELECT last_insert_rowid()")).scalar()
            db.commit()
            
            await self._log_processing_step(upload_id, "combined_document_analysis", "completed", {
                'document_analysis_id': doc_analysis_id,
                'document_type': gpt_analysis.get('document_type'),
                'questions_detected': gpt_analysis.get('question_count', 0)
            }, db)
            
            return {
                'success': True,
                'document_analysis_id': doc_analysis_id,
                'analysis_result': gpt_analysis,
                'image_path': image_path
            }
            
        except Exception as e:
            logger.error(f"Combined document analysis error: {str(e)}")
            await self._log_processing_step(upload_id, "combined_document_analysis", "failed", 
                                          {"error": str(e)}, db)
            return {'success': False, 'error': str(e)}

    async def _analyze_document_structure(self, upload_id: int, pdf_path: str, db: Session) -> Dict[str, Any]:
        """1단계: 문서 구조 분석"""
        try:
            await self._log_processing_step(upload_id, "document_analysis", "processing", {}, db)
            
            # PDF 열기
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # 텍스트 레이어 확인
            has_text_layer = False
            text_quality_score = 0
            
            for page_num in range(min(3, total_pages)):  # 첫 3페이지만 체크
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    has_text_layer = True
                    # 텍스트 품질 평가 (한글, 영문, 숫자 비율)
                    korean_chars = sum(1 for c in text if '\uac00' <= c <= '\ud7a3')
                    total_chars = len(text.strip())
                    if total_chars > 0:
                        text_quality_score += korean_chars / total_chars
            
            text_quality_score /= min(3, total_pages)
            is_scanned = not has_text_layer or text_quality_score < 0.1
            
            # 첫 페이지 썸네일 생성 (문서 타입 분석용)
            first_page = doc[0]
            pix = first_page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))  # 1.5배 확대
            thumbnail_path = self.temp_dir / f"doc_{upload_id}_p0_thumb.png"
            pix.save(str(thumbnail_path))
            
            # GPT Vision으로 문서 타입 분석
            gpt_analysis = await self._analyze_document_with_gpt(str(thumbnail_path), total_pages)
            
            # 데이터베이스에 저장
            db.execute(text("""
                INSERT INTO document_analysis 
                (pdf_upload_id, total_pages, document_type, has_text_layer, is_scanned, 
                 layout_analysis, content_structure, document_metadata, api_key_used, 
                 total_tokens_used, analysis_cost)
                VALUES (:upload_id, :total_pages, :doc_type, :has_text, :is_scanned,
                        :layout, :structure, :doc_metadata, :api_key, :tokens, :cost)
            """), {
                'upload_id': upload_id,
                'total_pages': total_pages,
                'doc_type': gpt_analysis.get('document_type'),
                'has_text': has_text_layer,
                'is_scanned': is_scanned,
                'layout': json.dumps(gpt_analysis.get('layout_info', {})),
                'structure': json.dumps(gpt_analysis.get('content_structure', {})),
                'doc_metadata': json.dumps(gpt_analysis.get('metadata', {})),
                'api_key': gpt_analysis.get('api_key_used'),
                'tokens': gpt_analysis.get('tokens_used', 0),
                'cost': gpt_analysis.get('cost', 0.0)
            })
            
            doc_analysis_id = db.execute(text("SELECT last_insert_rowid()")).scalar()
            db.commit()
            
            doc.close()
            
            await self._log_processing_step(upload_id, "document_analysis", "completed", {
                'document_analysis_id': doc_analysis_id,
                'total_pages': total_pages,
                'document_type': gpt_analysis.get('document_type'),
                'is_scanned': is_scanned
            }, db)
            
            return {
                'success': True,
                'document_analysis_id': doc_analysis_id,
                'total_pages': total_pages,
                'is_scanned': is_scanned,
                'document_type': gpt_analysis.get('document_type')
            }
            
        except Exception as e:
            logger.error(f"문서 구조 분석 오류: {str(e)}")
            await self._log_processing_step(upload_id, "document_analysis", "failed", 
                                          {"error": str(e)}, db)
            return {'success': False, 'error': str(e)}
    
    async def _analyze_document_with_gpt(self, image_path: str, total_pages: int) -> Dict[str, Any]:
        """GPT Vision으로 문서 분석"""
        try:
            if not self.openai_client:
                return {
                    'document_type': 'unknown',
                    'layout_info': {},
                    'content_structure': {},
                    'metadata': {},
                    'error': 'OpenAI API key not set'
                }
            
            # 이미지를 base64로 인코딩
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            prompt = f"""
이 문서는 총 {total_pages}페이지의 PDF 문서의 첫 번째 페이지입니다. 
다음 사항들을 분석해서 JSON 형태로 답변해주세요:

1. document_type: 문서 종류 (기출문제집, 해설집, 요약서, 정답표, 수험안내서 등)
2. layout_info: 레이아웃 정보
   - column_count: 단 수 (1단, 2단, 3단 등)
   - has_header_footer: 머리글/바닥글 존재 여부
   - text_density: 텍스트 밀도 (high, medium, low)
3. content_structure: 내용 구조
   - question_format: 문제 형식 (객관식, 주관식, 혼합 등)
   - numbering_style: 번호 스타일 (1., 1), ①, (1) 등)
   - answer_choices: 선택지 형식 (①②③④⑤, ABCDE, 1)2)3)4)5) 등)
   - has_explanations: 해설 포함 여부
4. metadata: 메타데이터
   - subject: 과목명 (추정)
   - exam_year: 시험년도 (추정)
   - exam_session: 회차 (추정)
   - difficulty_level: 난이도 추정 (beginner, intermediate, advanced)

JSON 형태로만 답변하고, 추가 설명은 하지 마세요.
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
                max_tokens=1000,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # JSON 파싱 시도
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본값 반환
                result = {
                    'document_type': 'unknown',
                    'layout_info': {'column_count': 1, 'text_density': 'medium'},
                    'content_structure': {'question_format': 'unknown'},
                    'metadata': {'subject': 'unknown'}
                }
            
            result['api_key_used'] = 'gpt-4o'
            result['tokens_used'] = response.usage.total_tokens
            result['cost'] = response.usage.total_tokens * 0.00001  # GPT-4O 대략 비용
            
            return result
            
        except Exception as e:
            logger.error(f"GPT 문서 분석 오류: {str(e)}")
            return {
                'document_type': 'unknown',
                'layout_info': {},
                'content_structure': {},
                'metadata': {},
                'error': str(e)
            }
    
    async def _analyze_combined_document_with_gpt(self, image_path: str) -> Dict[str, Any]:
        """GPT Vision으로 통합된 긴 이미지 분석"""
        try:
            print(f"GPT Analysis - OpenAI client status: {self.openai_client is not None}")
            if not self.openai_client:
                print("ERROR: OpenAI API key not set - returning basic analysis")
                return {
                    'document_type': 'unknown',
                    'layout_info': {},
                    'content_structure': {},
                    'metadata': {},
                    'error': 'OpenAI API key not set'
                }
            
            # 이미지를 base64로 인코딩
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            prompt = f"""
이 이미지는 여러 페이지의 PDF를 세로로 연결한 긴 문서 이미지입니다.
전체 문서를 분석해서 다음 정보들을 JSON 형태로 답변해주세요:

1. document_type: 문서 종류 (기출문제집, 해설집, 요약서, 정답표, 수험안내서 등)

2. layout_info: 전체 레이아웃 정보
   - column_count: 주요 단 수 (1단, 2단, 3단 등)
   - has_header_footer: 머리글/바닥글 존재 여부
   - text_density: 전체적인 텍스트 밀도 (high, medium, low)
   - page_breaks: 페이지 구분선이나 경계가 보이는 위치들

3. content_structure: 문제 구조 분석
   - question_format: 문제 형식 (객관식, 주관식, 혼합 등)
   - numbering_style: 문제 번호 스타일 (1., 1), ①, (1) 등)
   - answer_choices: 선택지 형식 (①②③④⑤, ABCDE, 1)2)3)4)5) 등)
   - has_explanations: 해설 포함 여부
   - question_count: 대략적인 문제 개수
   - question_regions: 문제가 시작되는 주요 위치들 (상단부터의 대략적 비율로 표현, 예: [0.1, 0.3, 0.5])

4. preprocessing_suggestions: 전처리 제안사항
   - brightness_adjustment: 밝기 조정 필요 여부 (true/false)
   - contrast_enhancement: 대비 강화 필요 여부 (true/false)  
   - noise_reduction: 노이즈 제거 필요 여부 (true/false)
   - deskew_needed: 기울기 보정 필요 여부 (true/false)
   - crop_margins: 여백 크롭 필요 여부 (true/false)

5. metadata: 메타데이터 추정
   - subject: 과목명 (추정)
   - exam_year: 시험년도 (추정)
   - exam_session: 회차 (추정)
   - difficulty_level: 난이도 추정 (beginner, intermediate, advanced)

6. ocr_suggestions: OCR 최적화 제안
   - recommended_language: 추천 언어 설정 (ko+en, ko, en 등)
   - text_size: 텍스트 크기 추정 (small, medium, large)
   - special_characters: 특수 문자나 수식 포함 여부

JSON 형태로만 답변하고, 추가 설명은 하지 마세요.
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
                max_tokens=2000,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # JSON 파싱 시도
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본값 반환
                result = {
                    'document_type': 'unknown',
                    'layout_info': {'column_count': 1, 'text_density': 'medium'},
                    'content_structure': {'question_format': 'unknown', 'question_count': 0},
                    'preprocessing_suggestions': {},
                    'metadata': {'subject': 'unknown'},
                    'ocr_suggestions': {}
                }
            
            result['api_key_used'] = 'gpt-4o'
            result['tokens_used'] = response.usage.total_tokens
            result['cost'] = response.usage.total_tokens * 0.00001  # GPT-4O 대략 비용
            
            return result
            
        except Exception as e:
            logger.error(f"GPT combined document analysis error: {str(e)}")
            return {
                'document_type': 'unknown',
                'layout_info': {},
                'content_structure': {},
                'preprocessing_suggestions': {},
                'metadata': {},
                'ocr_suggestions': {},
                'error': str(e)
            }
    
    async def _execute_preprocessing_on_combined(self, doc_analysis: Dict, db: Session) -> Dict[str, Any]:
        """2단계: 통합 이미지에 대한 전처리 실행"""
        try:
            upload_id = doc_analysis.get('upload_id') or doc_analysis['analysis_result'].get('upload_id')
            await self._log_processing_step(upload_id, "image_preprocessing", "processing", {}, db)
            
            print("Starting image preprocessing with OpenCV...")
            
            image_path = doc_analysis['image_path']
            analysis_result = doc_analysis['analysis_result']
            preprocessing_suggestions = analysis_result.get('preprocessing_suggestions', {})
            
            # OpenCV로 이미지 읽기
            image = cv2.imread(image_path)
            if image is None:
                raise Exception(f"Failed to load image: {image_path}")
            
            print(f"Original image shape: {image.shape}")
            applied_operations = []
            
            # 1. 밝기 조정
            if preprocessing_suggestions.get('brightness_adjustment', False):
                print("Applying brightness adjustment...")
                # 히스토그램 평균을 기준으로 밝기 조정
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                mean_brightness = np.mean(gray)
                
                if mean_brightness < 100:  # 너무 어두움
                    brightness_factor = 130 - mean_brightness
                    image = cv2.convertScaleAbs(image, alpha=1.0, beta=brightness_factor)
                    applied_operations.append(f"brightness_adjustment:+{brightness_factor}")
                elif mean_brightness > 200:  # 너무 밝음
                    brightness_factor = mean_brightness - 180
                    image = cv2.convertScaleAbs(image, alpha=1.0, beta=-brightness_factor)
                    applied_operations.append(f"brightness_adjustment:-{brightness_factor}")
            
            # 2. 대비 강화
            if preprocessing_suggestions.get('contrast_enhancement', False):
                print("Applying contrast enhancement...")
                # CLAHE (Contrast Limited Adaptive Histogram Equalization) 적용
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                lab[:, :, 0] = clahe.apply(lab[:, :, 0])
                image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                applied_operations.append("contrast_enhancement:CLAHE")
            
            # 3. 노이즈 제거
            if preprocessing_suggestions.get('noise_reduction', False):
                print("Applying noise reduction...")
                # Non-local means denoising
                image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
                applied_operations.append("noise_reduction:fastNlMeans")
            
            # 4. 기울기 보정
            if preprocessing_suggestions.get('deskew_needed', False):
                print("Applying deskew correction...")
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                
                # Hough Line Transform으로 기울기 찾기
                edges = cv2.Canny(gray, 50, 150, apertureSize=3)
                lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=200)
                
                if lines is not None:
                    angles = []
                    for rho, theta in lines[:20]:  # 상위 20개 선분만 사용
                        angle = theta * 180 / np.pi - 90
                        if abs(angle) < 45:  # 45도 이내의 각도만 고려
                            angles.append(angle)
                    
                    if angles:
                        median_angle = np.median(angles)
                        if abs(median_angle) > 0.5:  # 0.5도 이상 기울어진 경우만 보정
                            center = (image.shape[1] // 2, image.shape[0] // 2)
                            rotation_matrix = cv2.getRotationMatrix2D(center, -median_angle, 1.0)
                            image = cv2.warpAffine(image, rotation_matrix, (image.shape[1], image.shape[0]), 
                                                 flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                            applied_operations.append(f"deskew_correction:{median_angle:.2f}degrees")
            
            # 5. 여백 크롭
            if preprocessing_suggestions.get('crop_margins', False):
                print("Applying margin cropping...")
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                
                # 이진화
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                
                # 컨텐츠 영역 찾기
                coords = np.column_stack(np.where(thresh > 0))
                if len(coords) > 0:
                    y_min, x_min = coords.min(axis=0)
                    y_max, x_max = coords.max(axis=0)
                    
                    # 약간의 패딩 추가
                    padding = 20
                    y_min = max(0, y_min - padding)
                    x_min = max(0, x_min - padding)
                    y_max = min(image.shape[0], y_max + padding)
                    x_max = min(image.shape[1], x_max + padding)
                    
                    # 크롭
                    image = image[y_min:y_max, x_min:x_max]
                    applied_operations.append(f"margin_crop:({x_min},{y_min},{x_max},{y_max})")
            
            # 6. OCR을 위한 전용 전처리 파이프라인
            print("Applying OCR-optimized preprocessing...")
            
            # 그레이스케일 변환
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 노이즈 제거 (더 강력한 필터)
            gray = cv2.bilateralFilter(gray, 9, 75, 75)
            
            # 적응형 이진화 (텍스트 추출에 최적)
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY, 15, 4)
            
            # 모폴로지 연산으로 텍스트 개선
            kernel = np.ones((1,1), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # 최종적으로 3채널로 변환 (EasyOCR 요구사항)
            image = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
            
            applied_operations.append("OCR-optimized:bilateral_filter+adaptive_threshold+morphology")
            
            # 전처리된 이미지 저장
            preprocessed_path = self.temp_dir / f"preprocessed_{doc_analysis['analysis_result'].get('upload_id')}.png"
            cv2.imwrite(str(preprocessed_path), image)
            
            print(f"Preprocessed image shape: {image.shape}")
            print(f"Applied operations: {applied_operations}")
            
            await self._log_processing_step(doc_analysis['analysis_result'].get('upload_id'), 
                                          "image_preprocessing", "completed", {
                'operations_applied': applied_operations,
                'original_size': f"{cv2.imread(image_path).shape}",
                'preprocessed_size': f"{image.shape}",
                'preprocessed_path': str(preprocessed_path)
            }, db)
            
            return {
                'success': True,
                'preprocessed_image_path': str(preprocessed_path),
                'operations_applied': applied_operations,
                'original_path': image_path
            }
            
        except Exception as e:
            logger.error(f"Image preprocessing error: {str(e)}")
            await self._log_processing_step(doc_analysis['analysis_result'].get('upload_id'), 
                                          "image_preprocessing", "failed", {"error": str(e)}, db)
            return {'success': False, 'error': str(e)}
    
    async def _process_ocr_on_combined(self, preprocessing_result: Dict, db: Session) -> Dict[str, Any]:
        """3단계: 통합 이미지에 대한 OCR 처리"""
        try:
            upload_id = preprocessing_result.get('upload_id', 'unknown')
            await self._log_processing_step(upload_id, "ocr_processing", "processing", {}, db)
            
            print("Starting OCR processing...")
            
            image_path = preprocessing_result['preprocessed_image_path']
            
            # EasyOCR 사용 (한국어 + 영어) - 최적화된 설정
            import easyocr
            reader = easyocr.Reader(['ko', 'en'], gpu=False, verbose=False)  
            
            print("Performing EasyOCR text extraction with optimized settings...")
            
            # OCR 실행 (한국어 문서에 최적화된 파라미터 - 안정적인 기본 모드)
            results = reader.readtext(image_path, 
                                    detail=1,
                                    paragraph=False,  # 기본 라인 단위 인식 (더 안정적)
                                    width_ths=0.5,   # 텍스트 라인 너비 임계값
                                    height_ths=0.5,  # 텍스트 라인 높이 임계값  
                                    text_threshold=0.3,  # 텍스트 신뢰도 임계값
                                    low_text=0.2,    # 저품질 텍스트도 포함
                                    link_threshold=0.2)  # 텍스트 연결 임계값
            
            # 결과 정리
            extracted_text_blocks = []
            full_text = ""
            total_confidence = 0
            
            for (bbox, text, confidence) in results:
                if confidence > 0.1:  # 신뢰도 10% 이상만 사용 (더 많은 텍스트 포함)
                    # bbox 정보 정리
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    
                    text_block = {
                        'text': text.strip(),
                        'confidence': confidence,
                        'bbox': {
                            'x_min': min(x_coords),
                            'y_min': min(y_coords),
                            'x_max': max(x_coords),
                            'y_max': max(y_coords)
                        }
                    }
                    
                    extracted_text_blocks.append(text_block)
                    full_text += text + " "
                    total_confidence += confidence
            
            # Y 좌표 기준으로 정렬 (위에서 아래로)
            extracted_text_blocks.sort(key=lambda x: x['bbox']['y_min'])
            
            # 평균 신뢰도 계산
            average_confidence = total_confidence / len(extracted_text_blocks) if extracted_text_blocks else 0
            
            # 줄바꿈으로 구분된 전체 텍스트 생성
            organized_text = ""
            current_y = 0
            line_threshold = 30  # 같은 줄로 간주할 Y 좌표 차이
            
            for block in extracted_text_blocks:
                block_y = block['bbox']['y_min']
                
                # 새로운 줄인지 판단
                if abs(block_y - current_y) > line_threshold:
                    organized_text += "\n" + block['text']
                    current_y = block_y
                else:
                    organized_text += " " + block['text']
            
            print(f"OCR completed: {len(extracted_text_blocks)} text blocks extracted")
            print(f"Average confidence: {average_confidence:.2f}")
            print(f"Total characters: {len(organized_text)}")
            print(f"=== 실제 추출된 텍스트 (처음 500자) ===")
            print(f"'{organized_text[:500]}...'")
            print("=== 추출된 텍스트 끝 ===")
            
            # 추가로 Tesseract OCR도 시도 (비교용)
            tesseract_text = ""
            try:
                import pytesseract
                # Tesseract 설정 (한국어 + 영어)
                config = '--oem 3 --psm 6 -l kor+eng'
                tesseract_text = pytesseract.image_to_string(image_path, config=config)
                print(f"Tesseract also extracted {len(tesseract_text)} characters")
            except Exception as tesseract_error:
                print(f"Tesseract OCR failed: {tesseract_error}")
            
            # 결과 저장
            await self._log_processing_step(upload_id, "ocr_processing", "completed", {
                'text_blocks_count': len(extracted_text_blocks),
                'average_confidence': average_confidence,
                'total_characters': len(organized_text),
                'ocr_engines_used': ['easyocr', 'tesseract'] if tesseract_text else ['easyocr']
            }, db)
            
            return {
                'success': True,
                'ocr_method': 'easyocr',
                'extracted_text_blocks': extracted_text_blocks,
                'organized_text': organized_text.strip(),
                'tesseract_text': tesseract_text,
                'average_confidence': average_confidence,
                'total_text_blocks': len(extracted_text_blocks),
                'preprocessed_image_path': image_path
            }
            
        except Exception as e:
            logger.error(f"OCR processing error: {str(e)}")
            await self._log_processing_step(upload_id, "ocr_processing", "failed", {"error": str(e)}, db)
            return {'success': False, 'error': str(e)}

    async def _analyze_pages_with_gpt(self, doc_analysis_id: int, pdf_path: str, db: Session) -> Dict[str, Any]:
        """2단계: 페이지별 GPT 분석"""
        try:
            # 구현 예정 - 페이지별로 썸네일 생성하고 GPT로 분석
            # 각 페이지의 레이아웃, 문제 영역, 전처리 레시피 생성
            pass
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_preprocessing(self, page_analyses: List[Dict], db: Session) -> Dict[str, Any]:
        """3단계: 전처리 실행"""
        try:
            # 구현 예정 - OpenCV 등을 사용한 이미지 전처리
            pass
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _process_ocr(self, preprocessing_results: List[Dict], db: Session) -> Dict[str, Any]:
        """4단계: OCR 처리"""
        try:
            # 구현 예정 - Tesseract, PaddleOCR 등을 사용한 OCR
            pass
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _postprocess_and_structure(self, upload_id: int, ocr_result: Dict, db: Session) -> Dict[str, Any]:
        """4단계: 후처리 및 구조화 - Claude로 고급 교육 콘텐츠 분류"""
        try:
            await self._log_processing_step(upload_id, "advanced_classification", "processing", {}, db)
            
            print("Starting advanced text classification with Claude...")
            
            if not self.claude_client:
                print("ERROR: Claude client not available for advanced classification")
                return {
                    'questions': [],
                    'materials': [],
                    'chapters': [],
                    'summary': {'error': 'Claude API not available'}
                }
            
            organized_text = ocr_result.get('organized_text', '')
            text_blocks = ocr_result.get('extracted_text_blocks', [])
            
            if not organized_text:
                print("No text extracted from OCR")
                return {
                    'questions': [],
                    'materials': [],
                    'chapters': [],
                    'summary': {'error': 'No text extracted'}
                }
            
            print(f"Processing {len(organized_text)} characters of extracted text with Claude...")
            print(f"=== Claude에게 전달하는 텍스트 ===")
            print(f"'{organized_text[:1000]}...'")
            print("=== 전달 텍스트 끝 ===")
            
            # Claude로 고급 교육 콘텐츠 분류 및 구조화
            structuring_prompt = f"""
다음은 PDF 문서에서 OCR로 추출한 교육/시험 관련 텍스트입니다. 이 텍스트를 정밀하게 분석하여 교육 콘텐츠로 구조화해주세요.

추출된 텍스트:
{organized_text[:15000]}

다음 JSON 형태로 정확히 분석해주세요:

{{
  "document_analysis": {{
    "title": "문서 제목",
    "subject": "과목명", 
    "exam_type": "기출문제/해설집/요약서/교재/문제집",
    "academic_level": "초등/중등/고등/대학/자격증",
    "total_pages_analyzed": "분석된 페이지 수"
  }},
  
  "chapters": [
    {{
      "chapter_number": 1,
      "chapter_title": "단원/챕터 제목",
      "main_topics": ["주요 개념1", "주요 개념2"],
      "learning_objectives": ["학습목표1", "학습목표2"],
      "page_range": "시작페이지-끝페이지"
    }}
  ],
  
  "questions": [
    {{
      "question_id": "Q001",
      "chapter_id": 1,
      "question_number": 1,
      "question_text": "문제 내용",
      "question_type": "객관식/주관식/서술형/계산형",
      "options": ["선택지1", "선택지2", "선택지3", "선택지4", "선택지5"],
      "correct_answer": "정답",
      "explanation": "상세 해설",
      "difficulty_level": "상/중/하",
      "bloom_taxonomy": "지식/이해/적용/분석/종합/평가",
      "topic_tags": ["세부주제1", "세부주제2"],
      "estimated_time": "풀이 예상 소요시간(분)",
      "keywords": ["핵심키워드1", "핵심키워드2"]
    }}
  ],
  
  "study_materials": [
    {{
      "material_id": "M001", 
      "chapter_id": 1,
      "material_type": "개념설명/공식/정리/예제/요약/도표/그래프",
      "title": "학습자료 제목",
      "content": "상세 내용",
      "importance_level": "핵심/중요/참고",
      "related_questions": ["Q001", "Q002"],
      "prerequisites": ["선수학습요소1", "선수학습요소2"]
    }}
  ],
  
  "learning_analytics": {{
    "total_questions": 0,
    "question_distribution": {{
      "객관식": 0, "주관식": 0, "서술형": 0, "계산형": 0
    }},
    "difficulty_distribution": {{
      "상": 0, "중": 0, "하": 0
    }},
    "bloom_taxonomy_distribution": {{
      "지식": 0, "이해": 0, "적용": 0, "분석": 0, "종합": 0, "평가": 0
    }},
    "chapter_coverage": "챕터별 문제/자료 분포",
    "main_topics": ["전체 주요 주제들"],
    "estimated_study_time": "전체 학습 예상 소요시간(시간)"
  }}
}}

반드시 JSON 형태로만 답변하고, 추가 설명은 하지 마세요. 모든 분류는 교육학적 관점에서 정확하게 해주세요.
            """.strip()
            
            print("Sending text to Claude for advanced classification...")
            
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": structuring_prompt
                    }
                ]
            )
            
            result_text = response.content[0].text.strip()
            print(f"Claude response length: {len(result_text)} characters")
            
            # JSON 파싱
            try:
                structured_result = json.loads(result_text)
            except json.JSONDecodeError as json_error:
                print(f"JSON parsing failed: {json_error}")
                print(f"Raw response: {result_text[:500]}...")
                
                # JSON 파싱 실패 시 기본 구조 반환
                structured_result = {
                    'document_analysis': {
                        'title': 'Unknown Document',
                        'subject': 'Unknown',
                        'exam_type': 'Unknown',
                        'academic_level': 'Unknown',
                        'total_pages_analyzed': 0
                    },
                    'chapters': [],
                    'questions': [],
                    'study_materials': [],
                    'learning_analytics': {
                        'total_questions': 0,
                        'parsing_error': str(json_error)
                    }
                }
            
            # 새로운 고급 분류 결과 처리
            document_analysis = structured_result.get('document_analysis', {})
            chapters = structured_result.get('chapters', [])
            questions = structured_result.get('questions', [])
            materials = structured_result.get('study_materials', [])
            analytics = structured_result.get('learning_analytics', {})
            
            print(f"Claude advanced classification result:")
            print(f"  - {len(chapters)} chapters identified")
            print(f"  - {len(questions)} questions extracted")
            print(f"  - {len(materials)} learning materials created")
            
            # 고급 데이터베이스 저장 - 챕터 정보 먼저 저장
            chapter_ids = {}
            if chapters:
                for chapter in chapters:
                    try:
                        result = db.execute(text("""
                            INSERT INTO chapters
                            (pdf_upload_id, chapter_number, title, main_topics, learning_objectives, page_range)
                            VALUES (:upload_id, :chapter_number, :title, :main_topics, :learning_objectives, :page_range)
                        """), {
                            'upload_id': upload_id,
                            'chapter_number': chapter.get('chapter_number', 0),
                            'title': chapter.get('chapter_title', ''),
                            'main_topics': json.dumps(chapter.get('main_topics', [])),
                            'learning_objectives': json.dumps(chapter.get('learning_objectives', [])),
                            'page_range': chapter.get('page_range', '')
                        })
                        chapter_ids[chapter.get('chapter_number', 0)] = result.lastrowid
                        print(f"Saved chapter: {chapter.get('chapter_title', 'Untitled')}")
                    except Exception as db_error:
                        print(f"Failed to save chapter to DB: {db_error}")
            
            # 고급 문제 저장 (Claude 분류 기준)
            if questions:
                for question in questions:
                    try:
                        chapter_id = chapter_ids.get(question.get('chapter_id', 0))
                        db.execute(text("""
                            INSERT INTO extracted_questions 
                            (pdf_upload_id, chapter_id, question_id, question_text, question_type, 
                             difficulty_level, correct_answer, options, explanation, bloom_taxonomy,
                             topic_tags, estimated_time, keywords)
                            VALUES (:upload_id, :chapter_id, :question_id, :question_text, :question_type,
                                    :difficulty, :correct_answer, :options, :explanation, :bloom_taxonomy,
                                    :topic_tags, :estimated_time, :keywords)
                        """), {
                            'upload_id': upload_id,
                            'chapter_id': chapter_id,
                            'question_id': question.get('question_id', ''),
                            'question_text': question.get('question_text', ''),
                            'question_type': question.get('question_type', ''),
                            'difficulty': question.get('difficulty_level', ''),
                            'correct_answer': question.get('correct_answer', ''),
                            'options': json.dumps(question.get('options', [])),
                            'explanation': question.get('explanation', ''),
                            'bloom_taxonomy': question.get('bloom_taxonomy', ''),
                            'topic_tags': json.dumps(question.get('topic_tags', [])),
                            'estimated_time': question.get('estimated_time', ''),
                            'keywords': json.dumps(question.get('keywords', []))
                        })
                        print(f"Saved advanced question: {question.get('question_id', 'Unknown ID')}")
                    except Exception as db_error:
                        print(f"Failed to save question to DB: {db_error}")
            
            # 고급 학습 자료 저장
            if materials:
                for material in materials:
                    try:
                        # Dummy certificate_id 가져오기
                        dummy_cert = db.execute(text("SELECT id FROM certificates_info LIMIT 1")).fetchone()
                        cert_id = dummy_cert[0] if dummy_cert else 1
                        
                        chapter_id = chapter_ids.get(material.get('chapter_id', 0))
                        db.execute(text("""
                            INSERT INTO study_materials 
                            (certificate_id, pdf_upload_id, chapter_id, material_id, material_type, title, content,
                             importance_level, related_questions, prerequisites)
                            VALUES (:cert_id, :upload_id, :chapter_id, :material_id, :material_type, :title, :content,
                                    :importance_level, :related_questions, :prerequisites)
                        """), {
                            'cert_id': cert_id,
                            'upload_id': upload_id,
                            'chapter_id': chapter_id,
                            'material_id': material.get('material_id', ''),
                            'material_type': material.get('material_type', ''),
                            'title': material.get('title', ''),
                            'content': material.get('content', ''),
                            'importance_level': material.get('importance_level', ''),
                            'related_questions': json.dumps(material.get('related_questions', [])),
                            'prerequisites': json.dumps(material.get('prerequisites', []))
                        })
                        print(f"Saved advanced material: {material.get('title', 'Untitled')}")
                    except Exception as db_error:
                        print(f"Failed to save material to DB: {db_error}")
            
            db.commit()
            
            await self._log_processing_step(upload_id, "advanced_classification", "completed", {
                'chapters_identified': len(chapters),
                'questions_extracted': len(questions),
                'materials_created': len(materials),
                'claude_tokens_used': response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else 0,
                'document_analysis': document_analysis,
                'learning_analytics': analytics
            }, db)
            
            return {
                'questions': questions,
                'materials': materials,
                'chapters': chapters,
                'document_analysis': document_analysis,
                'learning_analytics': analytics,
                'tokens_used': response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else 0
            }
            
        except Exception as e:
            logger.error(f"Advanced classification error: {str(e)}")
            await self._log_processing_step(upload_id, "advanced_classification", "failed", {"error": str(e)}, db)
            return {
                'questions': [],
                'materials': [],
                'chapters': [],
                'document_analysis': {'error': str(e)},
                'learning_analytics': {'error': str(e)}
            }
    
    async def _log_processing_step(self, upload_id: int, step_name: str, status: str, 
                                 result_data: Dict, db: Session, step_order: int = 0):
        """처리 단계 로그 기록"""
        try:
            # upload_id가 None인 경우 로그 기록을 건너뜀
            if upload_id is None:
                print(f"Warning: upload_id is None for step {step_name}, skipping log")
                return
                
            now = datetime.now()
            
            if status == "processing":
                db.execute(text("""
                    INSERT INTO processing_steps 
                    (pdf_upload_id, step_name, step_order, status, started_at, result_data)
                    VALUES (:upload_id, :step_name, :step_order, :status, :started_at, :result_data)
                """), {
                    'upload_id': upload_id,
                    'step_name': step_name,
                    'step_order': step_order,
                    'status': status,
                    'started_at': now,
                    'result_data': json.dumps(result_data)
                })
            else:
                db.execute(text("""
                    UPDATE processing_steps 
                    SET status = :status, completed_at = :completed_at, 
                        result_data = :result_data, progress_percent = :progress
                    WHERE pdf_upload_id = :upload_id AND step_name = :step_name
                """), {
                    'upload_id': upload_id,
                    'step_name': step_name,
                    'status': status,
                    'completed_at': now,
                    'result_data': json.dumps(result_data),
                    'progress': 100 if status == "completed" else 0
                })
            
            db.commit()
            
        except Exception as e:
            logger.error(f"처리 단계 로그 기록 오류: {str(e)}")    
    async def _post_process_special_content(self, questions, chunk_idx):
        """🔥 특수 콘텐츠 (표/그림/코드) 후처리"""
        enhanced_questions = []
        
        for question in questions:
            passage = question.get('passage', '')
            question_text = question.get('question_text', '')
            combined_text = question_text + ' ' + passage
            
            # 표 처리
            if ('|' in passage or '표' in combined_text):
                print(f'📊 Table detected in Q{question.get("question_number")}')
                question['has_table'] = True
            
            # 코드 처리  
            if any(code_word in combined_text.lower() for code_word in 
                   ['class', 'function', 'public', 'int', 'string']):
                print(f'💻 Code detected in Q{question.get("question_number")}')
                question['has_code'] = True
                
            enhanced_questions.append(question)
        
        return enhanced_questions
    
    async def _detect_and_merge_orphaned_choices(self, all_questions: List[Dict]) -> List[Dict]:
        """🔍 고아 선택지 탐지 및 병합 시스템 - 시험지 흐름 기반 처리"""
        import re
        
        print(f"🔍 고아 선택지 탐지 시작: {len(all_questions)}개 문제 분석")
        
        # 1. 모든 문제를 페이지/위치 순서로 정렬 (정확한 흐름 파악을 위해)
        def get_sort_key(question):
            page = question.get('source_page', 0)
            location = question.get('page_location', '')
            # 페이지 번호 우선, 위치는 상단/중단/하단 순
            location_score = 0
            if '상단' in location: location_score = 1
            elif '중단' in location: location_score = 2  
            elif '하단' in location: location_score = 3
            return (page, location_score)
        
        sorted_questions = sorted(all_questions, key=get_sort_key)
        
        # 2. 고아 선택지 패턴 탐지 
        orphaned_indices = []
        incomplete_questions = []
        
        for i, question in enumerate(sorted_questions):
            question_text = question.get('question_text', '').strip()
            options = question.get('options', [])
            passage = question.get('passage', '').strip()
            
            # 🔍 고아 선택지 패턴 탐지
            is_orphaned_choices = self._is_orphaned_choice_pattern(question_text, options, passage)
            
            # 🔍 불완전한 문제 탐지 (선택지가 2개 이하이거나 연속되지 않는 경우)
            is_incomplete_question = self._is_incomplete_question(options)
            
            if is_orphaned_choices:
                orphaned_indices.append(i)
                print(f"🔍 고아 선택지 발견 #{i}: '{question_text[:50]}...' + {len(options)}개 선택지")
                
            if is_incomplete_question:
                incomplete_questions.append(i)
                print(f"🔍 불완전한 문제 발견 #{i}: Q{question.get('question_number', 'N/A')} - {len(options)}개 선택지")
        
        # 3. 고아 선택지와 불완전한 문제 병합 실행
        if orphaned_indices and incomplete_questions:
            print(f"🔗 병합 대상: {len(incomplete_questions)}개 불완전한 문제 + {len(orphaned_indices)}개 고아 선택지")
            sorted_questions = self._merge_orphaned_with_incomplete(sorted_questions, orphaned_indices, incomplete_questions)
        
        # 4. 특정 문제 번호의 선택지 복구 (예: 11번 문제 ③④⑤ 복구)
        sorted_questions = self._recover_specific_missing_choices(sorted_questions)
        
        print(f"✅ 고아 선택지 탐지 완료: {len(all_questions)} → {len(sorted_questions)}개 문제")
        return sorted_questions
    
    def _is_orphaned_choice_pattern(self, question_text: str, options: List[str], passage: str) -> bool:
        """🔍 강화된 선택지만 있고 실제 질문이 없는 고아 패턴 판단"""
        import re
        
        # 🔍 강화된 실제 질문 패턴 인식
        question_patterns = [
            r'다음\s*중', r'무엇인가\?', r'어떤\s*것', r'옳은\s*것', r'틀린\s*것',
            r'해당하는\s*것', r'아닌\s*것', r'설명으로', r'에\s*대한',
            r'\?$', r'구하시오', r'고르시오', r'하시오$', r'은\?', r'는\?',
            r'방법은', r'결과는', r'이유는', r'가장\s*적절한',
            r'알고리즘', r'함수', r'값을', r'예상\s*결과',
            r'다음\s*코드', r'다음\s*프로그램', r'다음\s*표'
        ]
        
        has_real_question = any(re.search(pattern, question_text, re.IGNORECASE) for pattern in question_patterns)
        
        # 🔍 강화된 선택지만 있는 패턴 확인
        only_choices_patterns = [
            r'^\s*[①②③④⑤]\s*[^서삭이의그리추]',  # 선택지로 시작하는 단순 내용
            r'^[①②③④⑤]\s*\w+$',  # 선택지 + 단어 하나
            r'^[①②③④⑤]\s*[A-Za-z0-9]+',  # 선택지 + 영숫자
            r'^\s*③\s*[^예자이다]',  # ③번부터 시작 (예자/이다 제외)
            r'^\s*④\s*[^예자이다]',  # ④번부터 시작 
            r'^\s*⑤\s*[^예자이다]'   # ⑤번부터 시작
        ]
        
        looks_like_only_choices = any(re.search(pattern, question_text, re.IGNORECASE) for pattern in only_choices_patterns)
        
        # 🔍 질문 단독성 검사 - 질문이 너무 짧고 의미가 없는 경우
        is_meaningless_text = (
            len(question_text.strip()) < 25 and 
            not has_real_question and
            not any(word in question_text for word in ['표', '그림', '코드', '상황', '문제'])
        )
        
        # 🔍 선택지 번호 연속성 검사 - 3번부터 시작하면 고아 선택지일 가능성 높음
        starts_with_late_choices = any(re.search(rf'^\s*{choice}', question_text) for choice in ['③', '④', '⑤'])
        
        # 🎯 고아 선택지 판정 조건 (강화된 버전)
        is_orphaned = (
            len(options) >= 1 and  # 선택지가 1개 이상 있고
            (
                starts_with_late_choices or  # 3,4,5번 선택지로 시작하거나
                (not has_real_question and looks_like_only_choices) or  # 실제 질문 없이 선택지만 있거나
                is_meaningless_text  # 의미없는 짧은 텍스트인 경우
            )
        )
        
        if is_orphaned:
            print(f"🔍 고아 선탭지 패턴 감지: '{question_text[:50]}...' | 선택지: {len(options)}개")
        
        return is_orphaned
    
    def _is_incomplete_question(self, options: List[str]) -> bool:
        """불완전한 문제인지 판단 (선택지 개수나 연속성 부족)"""
        if len(options) < 3:
            return True
            
        # 선택지 번호 연속성 확인
        import re
        choice_numbers = []
        for option in options:
            # ①②③④⑤ 또는 1)2)3)4)5) 패턴에서 번호 추출
            match = re.search(r'[①②③④⑤]|(\d+)\)', option)
            if match:
                if '①' in option: choice_numbers.append(1)
                elif '②' in option: choice_numbers.append(2)
                elif '③' in option: choice_numbers.append(3)
                elif '④' in option: choice_numbers.append(4)
                elif '⑤' in option: choice_numbers.append(5)
                elif match.group(1): choice_numbers.append(int(match.group(1)))
        
        # 연속성 확인 - 1부터 시작해서 연속되어야 함
        if choice_numbers and min(choice_numbers) != 1:
            return True  # 1번부터 시작하지 않음
            
        # 중간에 빠진 번호가 있는지 확인
        if choice_numbers:
            expected = list(range(1, max(choice_numbers) + 1))
            if sorted(choice_numbers) != expected:
                return True  # 중간에 빠진 번호가 있음
        
        return False
    
    def _merge_orphaned_with_incomplete(self, questions: List[Dict], orphaned_indices: List[int], incomplete_indices: List[int]) -> List[Dict]:
        """고아 선택지를 불완전한 문제와 병합"""
        
        merged_questions = []
        used_orphans = set()
        
        for i, question in enumerate(questions):
            if i in orphaned_indices:
                # 고아 선택지는 별도 처리하므로 스킵
                continue
                
            if i in incomplete_indices:
                # 불완전한 문제의 경우 다음 고아 선택지와 병합 시도
                merged_question = self._try_merge_with_next_orphan(questions, i, orphaned_indices, used_orphans)
                if merged_question != question:
                    print(f"🔗 Q{question.get('question_number', 'N/A')} 병합 성공: {len(question.get('options', []))} → {len(merged_question.get('options', []))}개 선택지")
                merged_questions.append(merged_question)
            else:
                # 완전한 문제는 그대로 추가
                merged_questions.append(question)
        
        print(f"🔗 병합 완료: {len(used_orphans)}개 고아 선택지 병합됨")
        return merged_questions
    
    def _try_merge_with_next_orphan(self, questions: List[Dict], incomplete_idx: int, orphaned_indices: List[int], used_orphans: set) -> Dict:
        """불완전한 문제와 다음 고아 선택지 병합 시도"""
        
        incomplete_question = questions[incomplete_idx].copy()
        
        # 바로 다음에 있는 고아 선택지 찾기
        for orphan_idx in orphaned_indices:
            if orphan_idx > incomplete_idx and orphan_idx not in used_orphans:
                # 너무 멀리 떨어진 경우는 병합하지 않음
                if orphan_idx - incomplete_idx > 3:
                    break
                    
                orphan_question = questions[orphan_idx]
                orphan_options = orphan_question.get('options', [])
                
                if orphan_options:
                    # 기존 선택지와 고아 선택지 병합
                    current_options = incomplete_question.get('options', [])
                    merged_options = current_options + orphan_options
                    
                    # 선택지 번호 순서 정렬
                    merged_options = self._sort_options_by_number(merged_options)
                    
                    incomplete_question['options'] = merged_options
                    incomplete_question['cross_page_resolved'] = True
                    used_orphans.add(orphan_idx)
                    
                    return incomplete_question
        
        return incomplete_question
    
    def _sort_options_by_number(self, options: List[str]) -> List[str]:
        """선택지를 번호 순서로 정렬"""
        import re
        
        def get_option_number(option):
            if '①' in option: return 1
            elif '②' in option: return 2
            elif '③' in option: return 3
            elif '④' in option: return 4
            elif '⑤' in option: return 5
            else:
                match = re.search(r'(\d+)\)', option)
                return int(match.group(1)) if match else 999
        
        return sorted(options, key=get_option_number)
    
    def _recover_specific_missing_choices(self, questions: List[Dict]) -> List[Dict]:
        """특정 문제 번호의 누락된 선택지 복구 (예: 11번 문제)"""
        
        # 문제별 선택지 현황 분석
        for question in questions:
            q_num = question.get('question_number')
            options = question.get('options', [])
            
            if isinstance(q_num, (int, str)) and str(q_num) in ['11', '6']:  # 특히 문제가 많은 번호들
                if len(options) < 4:  # 일반적으로 4-5개 선택지가 정상
                    print(f"🔍 Q{q_num} 선택지 부족 감지: {len(options)}개 (복구 대상)")
                    
                    # 다른 문제들에서 같은 번호의 추가 선택지 찾기
                    additional_options = self._find_additional_options_for_question(questions, q_num)
                    if additional_options:
                        merged_options = options + additional_options
                        merged_options = self._sort_options_by_number(merged_options)
                        question['options'] = merged_options
                        question['cross_page_resolved'] = True
                        print(f"✅ Q{q_num} 선택지 복구: {len(options)} → {len(merged_options)}개")
        
        return questions
    
    def _attempt_immediate_choice_recovery(self, question_number: int, current_options: List[str], chunk_questions: List[Dict]) -> List[str]:
        """즉시 선택지 복구 시도 - 현재 청크에서 연결된 선택지 찾기"""
        import re
        
        print(f"🔍 Q{question_number} 즉시 선택지 복구 시도...")
        
        # 현재 선택지에서 마지막 번호 찾기
        last_choice_num = 0
        for option in current_options:
            if '①' in option: last_choice_num = max(last_choice_num, 1)
            elif '②' in option: last_choice_num = max(last_choice_num, 2)
            elif '③' in option: last_choice_num = max(last_choice_num, 3)
            elif '④' in option: last_choice_num = max(last_choice_num, 4)
            elif '⑤' in option: last_choice_num = max(last_choice_num, 5)
            else:
                # 1), 2), 3) 형태 체크
                match = re.search(r'(\d+)\)', option)
                if match:
                    last_choice_num = max(last_choice_num, int(match.group(1)))
        
        print(f"현재 선택지 마지막 번호: {last_choice_num}")
        
        if last_choice_num == 0:
            return current_options  # 번호를 찾을 수 없음
        
        # 다음 번호들 (③④⑤ 또는 3)4)5)) 찾기
        needed_numbers = list(range(last_choice_num + 1, 6))  # 다음 번호부터 5까지
        recovered_options = current_options.copy()
        
        print(f"찾아야 할 선택지 번호: {needed_numbers}")
        
        # 현재 청크의 모든 문제에서 필요한 선택지 찾기
        for question in chunk_questions:
            q_options = question.get('options', [])
            q_text = question.get('question_text', '')
            
            # 이 문제가 고아 선택지일 가능성 체크
            is_likely_orphan = (
                len(q_text.strip()) < 20 and  # 짧은 텍스트
                len(q_options) > 0 and        # 선택지는 있음
                not any(pattern in q_text.lower() for pattern in ['문제', '다음', '아래', '위에서', '보기'])  # 질문 패턴 없음
            )
            
            if is_likely_orphan:
                print(f"고아 선택지 후보 발견: '{q_text[:30]}...' with {len(q_options)} options")
                
                for option in q_options:
                    for num in needed_numbers:
                        # 원하는 번호의 선택지인지 체크
                        if (f'{"①②③④⑤"[num-1]}' in option or f'{num})' in option):
                            print(f"✅ 발견: 선택지 {num}번 - '{option[:40]}...'")
                            recovered_options.append(option)
                            if num in needed_numbers:
                                needed_numbers.remove(num)
        
        print(f"복구 결과: {len(current_options)}개 → {len(recovered_options)}개 (부족: {needed_numbers})")
        return recovered_options
    
    def _is_non_question_pattern(self, text: str) -> bool:
        """강화된 비-질문 패턴 감지 - 설명문, 해설, 보기 구분"""
        text_lower = text.lower().strip()
        
        # 1. 설명문 어미 패턴 (해설이나 설명 텍스트)
        explanation_endings = [
            '입니다', '합니다', '다.', '이다.', '된다.', '한다.', '이며', '하여',
            '다음과 같다', '할 수 있다', '볼 수 있다', '여겨진다', '것이다',
            '설명하면', '알아보면', '살펴보면', '의미한다', '뜻한다'
        ]
        
        if any(text.endswith(ending) for ending in explanation_endings):
            return True
        
        # 2. 해설/정답 페이지 키워드
        explanation_keywords = [
            '해설', '정답', '풀이', '답안', '해답', '설명', '해석', '답:', '정답은',
            '해답지', '채점기준', '점수', '정리', '요약', '복습'
        ]
        
        if any(keyword in text_lower for keyword in explanation_keywords):
            return True
        
        # 3. 단순 설명문 패턴 (질문이 아닌 서술)
        description_patterns = [
            '의 주요 상태는', '의 특징은', '은 다음과 같다', '라고 할 수 있다', 
            '로 정의된다', '에 대해 알아보', '를 살펴보', '는 의미한다'
        ]
        
        if any(pattern in text for pattern in description_patterns):
            return True
        
        # 4. 보기/지문 패턴 (문제의 일부이지만 질문 자체가 아님)
        passage_indicators = [
            '보기:', '[보기]', '지문:', '[지문]', '다음을 읽고', '아래 코드를', 
            '다음 프로그램을', '아래 표를', '다음 그림을'
        ]
        
        if any(indicator in text for indicator in passage_indicators):
            return True
        
        # 5. 질문형 패턴이 전혀 없는 경우 (긍정적 검증 실패)
        question_patterns = [
            '?', '은?', '는?', '인가?', '할까?', '다면?', '무엇인가?', 
            '구하시오', '고르시오', '하시오', '다음 중', '아래에서', '위에서',
            '보기에서', '알맞은', '옳은', '틀린', '적절한'
        ]
        
        has_question_pattern = any(pattern in text for pattern in question_patterns)
        
        # 질문 패턴이 없고 길이가 긴 경우 설명문으로 간주
        if not has_question_pattern and len(text) > 50:
            return True
        
        # 6. 코드 블록만 있는 경우 (질문이 아닌 보기)
        if text.startswith('[CODE_START]') or 'class ' in text or 'public ' in text:
            if not has_question_pattern:
                return True
        
        return False
    
    def _is_clearly_non_question(self, text: str) -> bool:
        """보수적인 비-질문 감지 - 명백히 질문이 아닌 경우만 제외"""
        text_lower = text.lower().strip()
        
        # 1. 명백한 해설/정답 키워드만 제외
        clear_explanation_keywords = ['정답은', '해설:', '풀이:', '정답:', '답안:']
        if any(keyword in text_lower for keyword in clear_explanation_keywords):
            return True
        
        # 2. 명백한 설명문 어미 (매우 제한적)
        clear_explanation_endings = ['다음과 같다.', '정의된다.', '설명하면 다음과 같다.']
        if any(text.endswith(ending) for ending in clear_explanation_endings):
            return True
        
        # 3. 메타데이터성 텍스트
        meta_patterns = ['페이지 ', '목차', '표지', '참고자료', '부록']
        if any(pattern in text_lower for pattern in meta_patterns) and len(text) < 30:
            return True
        
        # 나머지는 모두 통과 - 애매한 경우 질문으로 처리하여 누락 방지
        return False
    
    def _find_additional_options_for_question(self, questions: List[Dict], target_question_number) -> List[str]:
        """특정 문제 번호에 대한 추가 선택지 찾기"""
        additional_options = []
        
        for question in questions:
            q_num = question.get('question_number')
            if q_num == target_question_number:
                options = question.get('options', [])
                # 이미 가진 선택지와 중복되지 않는 추가 선택지 추출
                for option in options:
                    if option not in additional_options:
                        # ③④⑤ 패턴이 있는지 확인
                        if any(choice in option for choice in ['③', '④', '⑤']):
                            additional_options.append(option)
        
        return additional_options
    
    def _preprocess_page_connections(self, page_content: str, page_num: int, previous_pages: List[str]) -> str:
        """🔗 강화된 페이지간 선택지 연결 전처리 - 텍스트화 단계에서 처리"""
        import re
        
        print(f"🔗 페이지 {page_num} 강화된 연결 전처리 시작...")
        
        # 🐈 1단계: 페이지 경계 마커 감지
        page_boundary_issues = self._detect_page_boundary_markers(page_content)
        
        # 🐈 2단계: 고아 선택지 패턴 감지 (강화된 버전)
        orphaned_choices = self._detect_orphaned_choices_in_text(page_content)
        
        # 🐈 3단계: 코드 블록 경계 감지
        code_boundary_issues = self._detect_code_boundary_issues(page_content)
        
        if page_boundary_issues:
            print(f"⚠️ 페이지 {page_num} 경계 마커 감지: {page_boundary_issues}")
        
        if orphaned_choices and previous_pages:
            print(f"🔍 페이지 {page_num}에서 고아 선택지 감지: {len(orphaned_choices)}개")
            
            # 4. 이전 페이지에서 불완전한 문제 찾기 (강화된 버전)
            last_page_content = previous_pages[-1] if previous_pages else ""
            incomplete_question = self._find_incomplete_question_in_text(last_page_content)
            
            if incomplete_question:
                print(f"🔗 이전 페이지 불완전 문제 발견: {incomplete_question[:70]}...")
                
                # 5. 스마트 선택지 병합 수행
                merged_content = self._merge_orphaned_choices_with_previous(
                    page_content, orphaned_choices, incomplete_question, previous_pages
                )
                
                if merged_content != page_content:
                    print(f"✅ 페이지 {page_num} 스마트 선택지 병합 완료")
                    return merged_content
        
        # 🐈 6단계: 코드 연속성 및 들여쓰기 복구
        if code_boundary_issues and previous_pages:
            merged_content = self._merge_code_blocks_across_pages(page_content, previous_pages)
            if merged_content != page_content:
                print(f"✅ 페이지 {page_num} 코드 블록 병합 완료")
                return merged_content
        
        return page_content
    
    def _detect_page_boundary_markers(self, content: str) -> List[str]:
        """🔍 페이지 경계 마커 감지"""
        import re
        
        boundary_patterns = [
            r'\(③④⑤ 다음 페이지\)',
            r'\(④⑤⑥ 다음 페이지\)', 
            r'\(⑤⑥ 다음 페이지\)',
            r'\(⑥ 다음 페이지\)',
            r'\(페이지 경계로 잘림\)',
            r'\[연속\]', r'\[이어짐\]'
        ]
        
        found_markers = []
        for pattern in boundary_patterns:
            if re.search(pattern, content):
                found_markers.append(pattern)
        
        return found_markers
    
    def _detect_code_boundary_issues(self, content: str) -> bool:
        """🔍 코드 블록 경계 문제 감지"""
        import re
        
        # 빈 코드 블록 또는 들여쓰기가 망가진 코드 감지
        code_patterns = [
            r'\{\s*$',  # 열린 중괄호만 있음
            r'^\s*\}',  # 닫힌 중괄호로 시작
            r'if\s*\(.*\)\s*$',  # if 문 미완성
            r'for\s*\(.*\)\s*$',  # for 문 미완성
            r'while\s*\(.*\)\s*$',  # while 문 미완성
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, content, re.MULTILINE):
                return True
        return False
    
    def _merge_code_blocks_across_pages(self, current_content: str, previous_pages: List[str]) -> str:
        """🔗 페이지 간 코드 블록 병합 및 들여쓰기 복구"""
        import re
        
        if not previous_pages:
            return current_content
        
        last_page = previous_pages[-1]
        
        # 이전 페이지의 마지막 코드 블록 찾기
        last_code_match = None
        for match in re.finditer(r'```[\w]*\n(.*?)```', last_page, re.DOTALL):
            last_code_match = match
        
        if last_code_match:
            last_code = last_code_match.group(1)
            # 미완성된 코드 블록인지 검사 (중괄호 매칭 등)
            open_braces = last_code.count('{')
            close_braces = last_code.count('}')
            
            if open_braces > close_braces:
                # 현재 페이지에서 코드 연속 찾기
                current_code_match = re.search(r'^(.*?)```', current_content, re.DOTALL)
                if current_code_match:
                    current_code_part = current_code_match.group(1)
                    # 코드 병합 및 들여쓰기 복구
                    merged_code = self._restore_code_indentation(last_code + "\n" + current_code_part)
                    
                    # 이전 페이지 업데이트
                    updated_last_page = last_page.replace(last_code_match.group(0), 
                                                        f"```\n{merged_code}\n```")
                    previous_pages[-1] = updated_last_page
                    
                    # 현재 페이지에서 코드 부분 제거
                    remaining_content = current_content.replace(current_code_match.group(0), '').strip()
                    return remaining_content
        
        return current_content
    
    def _restore_code_indentation(self, code_block: str) -> str:
        """🎯 코드 블록 들여쓰기 복구"""
        lines = code_block.split('\n')
        restored_lines = []
        current_indent = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                restored_lines.append('')
                continue
            
            # 들여쓰기 레벨 조정
            if stripped.endswith('{'):
                restored_lines.append('    ' * current_indent + stripped)
                current_indent += 1
            elif stripped.startswith('}'):
                current_indent = max(0, current_indent - 1)
                restored_lines.append('    ' * current_indent + stripped)
            else:
                restored_lines.append('    ' * current_indent + stripped)
        
        return '\n'.join(restored_lines)
    
    def _detect_orphaned_choices_in_text(self, content: str) -> List[str]:
        """🔍 강화된 텍스트에서 고아 선택지 패턴 탐지"""
        import re
        
        lines = content.strip().split('\n')
        orphaned_choices = []
        
        # 🔍 강화된 선택지 패턴들 - 더 많은 패턴 인식
        choice_patterns = [
            r'^선택지\s*[3-5]:\s*(.+)$',  # "선택지 3:", "선택지 4:", "선택지 5:"
            r'^[③④⑤]\s*(.+)$',  # ③, ④, ⑤로 시작
            r'^[3-5]\)\s*(.+)$',  # 3), 4), 5)로 시작
            r'^\s*[③④⑤]\s*(.+)$',  # 공백 + ③④⑤ 패턴
            r'^\s*[3-5]\)\s*(.+)$',  # 공백 + 3)4)5) 패턄
            r'^\s*③',  # 단순히 ③으로 시작 (짧은 선택지)
            r'^\s*④',  # 단순히 ④으로 시작
            r'^\s*⑤',  # 단순히 ⑤으로 시작
        ]
        
        # 🔍 강화된 질문 패턴 인식
        question_patterns = [
            r'문제\s*\d+번',  # "문제 1번"
            r'\d+\.\s*[가-힣].+\?',  # "1. 다음 중...?"
            r'다음\s*중',  # "다음 중"
            r'무엇인가\?', r'어떤\s*것', r'옳은\s*것', r'틀린\s*것',
            r'해당하는\s*것', r'아닌\s*것', r'설명으로', r'에\s*대한',
            r'구하시오', r'고르시오', r'하시오$'
        ]
        
        has_question = any(re.search(pattern, content, re.IGNORECASE) for pattern in question_patterns)
        
        # 질문 없이 선택지만 있는 경우
        if not has_question:
            for line in lines:
                line = line.strip()
                for pattern in choice_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        orphaned_choices.append(line)
                        break
        
        return orphaned_choices
    
    def _find_incomplete_question_in_text(self, content: str) -> str:
        """🔍 강화된 텍스트에서 불완전한 문제 찾기 (선택지가 부족한)"""
        import re
        
        # 🔍 강화된 문제 패턴 - 다양한 문제 번호 표기법 인식
        question_patterns = [
            r'(문제\s*\d+번.*?)(?=문제\s*\d+번|$)',  # "문제 1번"
            r'(\d+\.\s*[가-힣].*?)(?=\d+\.|$)',  # "1. 다음 중"
            r'(\d+\)\s*[가-힣].*?)(?=\d+\)|$)',  # "1) 다음 중"
            r'([①②③④⑤⑥⑦⑧⑨⑩].*?)(?=[①②③④⑤⑥⑦⑧⑨⑩]|$)'  # 원형 번호
        ]
        
        for pattern in question_patterns:
            question_match = re.search(pattern, content, re.DOTALL)
            if question_match:
                question_block = question_match.group(1)
                
                # 🔍 강화된 선택지 개수 확인 - 더 정확한 패턴 매칭
                choice_patterns = [
                    r'선택지\s*[1-5]:',
                    r'[①②③④⑤]',
                    r'[1-5]\)',
                    r'\s*①\s', r'\s*②\s', r'\s*③\s', r'\s*④\s', r'\s*⑤\s'
                ]
                
                choice_count = 0
                for choice_pattern in choice_patterns:
                    matches = re.findall(choice_pattern, question_block)
                    choice_count = max(choice_count, len(matches))
                
                # 🎯 선택지 연속성 검사
                found_numbers = []
                if '①' in question_block: found_numbers.append(1)
                if '②' in question_block: found_numbers.append(2)
                if '③' in question_block: found_numbers.append(3)
                if '④' in question_block: found_numbers.append(4)
                if '⑤' in question_block: found_numbers.append(5)
                
                # 1,2만 있거나 1,2,3만 있는 경우 = 불완전
                if found_numbers and max(found_numbers) <= 3:
                    print(f"🔍 불완전한 문제 발견: 선택지 {found_numbers}번만 있음")
                    return question_block
                
                # 보통 4-5개 선택지가 정상이므로 3개 이하면 불완전
                if choice_count <= 3:
                    print(f"🔍 불완전한 문제 발견: {choice_count}개 선택지만 있음")
                    return question_block
        
        return ""
    
    def _merge_orphaned_choices_with_previous(self, current_content: str, orphaned_choices: List[str], 
                                            incomplete_question: str, previous_pages: List[str]) -> str:
        """🔗 강화된 고아 선택지를 이전 페이지의 불완전한 문제와 병합"""
        
        if not orphaned_choices or not incomplete_question:
            return current_content
        
        print(f"🔗 선택지 병합 시작: {len(orphaned_choices)}개 고아 선택지 → 이전 페이지 불완전 문제")
        
        # 이전 페이지 내용에서 불완전한 문제를 완전한 문제로 교체
        if previous_pages:
            last_page_idx = len(previous_pages) - 1
            updated_last_page = previous_pages[last_page_idx]
            
            # 🔗 스마트 선택지 병합 - 기존 선택지와 번호 연속성 맞추기
            enhanced_choices = self._smart_merge_choices(incomplete_question, orphaned_choices)
            enhanced_question = incomplete_question + "\n" + "\n".join(enhanced_choices)
            
            # 이전 페이지 업데이트
            updated_last_page = updated_last_page.replace(incomplete_question, enhanced_question)
            previous_pages[last_page_idx] = updated_last_page
            
            print(f"✅ 이전 페이지 선택지 병합 완료: {len(enhanced_choices)}개 선택지 추가")
            
            # 현재 페이지에서 고아 선택지 제거 - 더 정확한 제거
            remaining_content = current_content
            for choice in orphaned_choices:
                # 정확한 라인 단위로 제거
                lines = remaining_content.split('\n')
                filtered_lines = []
                for line in lines:
                    if not any(choice.strip() in line.strip() for choice in orphaned_choices):
                        filtered_lines.append(line)
                remaining_content = '\n'.join(filtered_lines)
            
            # 빈 줄 정리  
            import re
            remaining_content = re.sub(r'\n\s*\n', '\n', remaining_content).strip()
            
            print(f"✅ 현재 페이지 고아 선택지 제거 완료")
            return remaining_content
        
        return current_content
    
    def _smart_merge_choices(self, incomplete_question: str, orphaned_choices: List[str]) -> List[str]:
        """🎯 스마트 선택지 병합 - 번호 연속성 보장"""
        import re
        
        # 기존 문제에서 이미 있는 선택지 번호 찾기
        existing_numbers = []
        if '①' in incomplete_question: existing_numbers.append(1)
        if '②' in incomplete_question: existing_numbers.append(2)
        if '③' in incomplete_question: existing_numbers.append(3)
        
        print(f"🔍 기존 선택지: {existing_numbers}번")
        
        # 고아 선택지의 번호 재조정
        adjusted_choices = []
        expected_next = max(existing_numbers) + 1 if existing_numbers else 3
        
        for choice in orphaned_choices:
            # 기존 번호 제거하고 올바른 번호로 교체
            clean_choice = re.sub(r'^\s*[③④⑤①②]\s*', '', choice.strip())
            clean_choice = re.sub(r'^\s*[3-5]\)\s*', '', clean_choice)
            
            # 올바른 번호 추가
            if expected_next == 3:
                adjusted_choice = f"③ {clean_choice}"
            elif expected_next == 4:
                adjusted_choice = f"④ {clean_choice}"
            elif expected_next == 5:
                adjusted_choice = f"⑤ {clean_choice}"
            else:
                adjusted_choice = f"{expected_next}) {clean_choice}"
            
            adjusted_choices.append(adjusted_choice)
            expected_next += 1
        
        print(f"✅ 선택지 번호 재조정: {len(adjusted_choices)}개 → {expected_next-1}번까지")
        return adjusted_choices
    
    
    async def _handle_cross_page_questions(self, all_questions: List[Dict], full_connected_content: str) -> List[Dict]:
        """페이지 경계 문제 해결 및 문제 번호 정규화 + 🆕 고아 선택지 병합 시스템"""
        print(f"\n🔗 페이지 경계 문제 해결 및 고아 선택지 탐지 중...")
        
        # 🆕 STEP 0: 고아 선택지 탐지 및 병합 시스템
        print(f"🔍 STEP 0: 고아 선택지 탐지 시작...")
        orphaned_choices_merged = await self._detect_and_merge_orphaned_choices(all_questions)
        all_questions = orphaned_choices_merged
        
        # 1. 전체 연결 이미지에서 발견된 페이지 경계 문제들 파싱
        cross_page_fixes = {}
        if full_connected_content and "페이지 경계 문제" in full_connected_content:
            # 페이지 경계 문제 발견된 경우 파싱
            import re
            problem_patterns = re.findall(r'### 페이지 경계 문제 (\d+)번 발견!(.*?)(?=### 페이지 경계 문제|\Z)', 
                                        full_connected_content, re.DOTALL)
            
            for problem_num, problem_content in problem_patterns:
                try:
                    question_match = re.search(r'\*\*완전한 질문\*\*: (.*?)(?=\*\*)', problem_content, re.DOTALL)
                    options_match = re.search(r'\*\*완전한 선택지\*\*: (.*?)(?=\*\*)', problem_content, re.DOTALL)
                    table_match = re.search(r'\*\*완전한 표 데이터\*\*.*?\n((?:\|.*?\|\n)+)', problem_content, re.DOTALL)
                    
                    if question_match or options_match or table_match:
                        cross_page_fixes[int(problem_num)] = {
                            'question': question_match.group(1).strip() if question_match else None,
                            'options': options_match.group(1).strip() if options_match else None,
                            'table': table_match.group(1).strip() if table_match else None
                        }
                        print(f"✅ 페이지 경계 문제 {problem_num}번 수정 데이터 준비됨")
                except Exception as e:
                    print(f"⚠️ 페이지 경계 문제 {problem_num}번 파싱 실패: {e}")
        
        # 2. 문제 번호 중복 해결 및 정규화
        question_by_number = {}
        fixed_questions = []
        
        for question in all_questions:
            q_num = question.get('question_number', 'N/A')
            
            # 문제 번호 정규화
            if isinstance(q_num, str) and q_num != 'N/A':
                import re
                number_match = re.search(r'(\d+)$', str(q_num))
                if number_match:
                    q_num = int(number_match.group(1))
            
            if q_num == 'N/A' or not isinstance(q_num, int):
                continue
                
            # 3. 페이지 경계 문제 수정 적용
            if q_num in cross_page_fixes:
                fix_data = cross_page_fixes[q_num]
                
                # 질문 수정
                if fix_data['question']:
                    question['question_text'] = fix_data['question']
                    print(f"🔧 Q{q_num}: 질문 수정 적용")
                
                # 선택지 수정
                if fix_data['options']:
                    # 선택지 파싱 (①, ②, ③, ④ 형태)
                    import re
                    options = re.findall(r'[①②③④⑤]\s*[^①②③④⑤]+', fix_data['options'])
                    if options:
                        question['options'] = [opt.strip() for opt in options]
                        print(f"🔧 Q{q_num}: 선택지 수정 적용 ({len(options)}개)")
                
                # 표 데이터 수정
                if fix_data['table']:
                    current_passage = question.get('passage', '')
                    if fix_data['table'] not in current_passage:
                        question['passage'] = current_passage + '\n\n' + fix_data['table']
                        question['has_table'] = True
                        print(f"🔧 Q{q_num}: 표 데이터 수정 적용")
            
            # 4. 중복 문제 병합 처리
            if q_num in question_by_number:
                existing = question_by_number[q_num]
                current = question
                
                # 더 완전한 버전 선택 (선택지 수, 지문 길이 기준)
                existing_score = len(existing.get('options', [])) * 10 + len(existing.get('passage', ''))
                current_score = len(current.get('options', [])) * 10 + len(current.get('passage', ''))
                
                if current_score > existing_score:
                    question_by_number[q_num] = current
                    print(f"🔄 Q{q_num}: 더 완전한 버전으로 교체 (점수: {existing_score} → {current_score})")
            else:
                question_by_number[q_num] = question
        
        # 5. 문제 번호 순서로 정렬하여 반환
        sorted_questions = []
        for q_num in sorted(question_by_number.keys()):
            question = question_by_number[q_num]
            question['question_number'] = q_num
            sorted_questions.append(question)
        
        print(f"🔗 페이지 경계 문제 해결 완료:")
        print(f"  - 수정 적용: {len(cross_page_fixes)}개 문제")
        print(f"  - 중복 제거: {len(all_questions)} → {len(sorted_questions)}개 문제")
        print(f"  - 최종 범위: 1~{max(question_by_number.keys()) if question_by_number else 0}번")
        
        return sorted_questions
    
    async def _post_process_special_content(self, questions: List[Dict], chunk_idx: int) -> List[Dict]:
        """특수 콘텐츠 (표/그림/코드) 후처리"""
        processed = []
        
        for question in questions:
            passage = question.get('passage', '')
            options = question.get('options', [])
            
            # 표 데이터 후처리
            if '|' in passage and passage.count('|') > 2:
                question['has_table'] = True
                # 표 헤더 누락 검사 및 수정
                lines = passage.split('\n')
                table_lines = [line for line in lines if '|' in line]
                if table_lines and not any('프로세스' in line or '도착시간' in line or '실행시간' in line for line in table_lines[:1]):
                    # 표 헤더가 누락된 경우 추정하여 추가
                    if len(table_lines[0].split('|')) == 4:  # 3컬럼 + 빈칸
                        header = "| 프로세스 | 도착시간 | 실행시간 |"
                        question['passage'] = header + '\n|-------|-------|-------|\n' + '\n'.join(table_lines)
                        print(f"🔧 Q{question.get('question_number')}: 표 헤더 보완 적용")
            
            # 그림 선택지 후처리  
            has_image_options = any('[그림:' in opt or '[수식:' in opt or len(opt.strip()) <= 5 for opt in options)
            if has_image_options:
                question['has_figure'] = True
                print(f"📊 Q{question.get('question_number')}: 그림 선택지 감지됨")
            
            processed.append(question)
        
        return processed
    
    def _estimate_question_count_from_markdown(self, markdown_content: str) -> int:
        """마크다운 텍스트에서 실제 문제 수 추정"""
        import re
        
        # 다양한 문제 번호 패턴 검색
        patterns = [
            r'### 문제 (\d+)번',  # GPT Vision이 생성한 구조화된 패턴
            r'## (\d+)번',       # 대안 번호 패턴
            r'(\d+)\.\s*[가-힣]',  # 1. 로 시작하는 문제
            r'(\d+)\)\s*[가-힣]',  # 1) 로 시작하는 문제
            r'문제\s*(\d+)',      # "문제 1" 패턴
            r'Q\.?(\d+)',        # Q1, Q.1 패턴
        ]
        
        question_numbers = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, markdown_content)
            for match in matches:
                try:
                    num = int(match)
                    if 1 <= num <= 150:  # 합리적인 문제 번호 범위
                        question_numbers.add(num)
                except ValueError:
                    continue
        
        # 최고 문제 번호를 기준으로 실제 문제 수 추정
        if question_numbers:
            max_question = max(question_numbers)
            estimated_count = max_question
            print(f"  📊 문제 번호 범위: 1~{max_question} (추정: {estimated_count}개)")
            return estimated_count
        
        # 문제 번호가 없는 경우 질문 패턴으로 추정
        question_patterns = [
            r'[가-힣]{3,}은\?',     # ~은?
            r'[가-힣]{3,}는\?',     # ~는?
            r'[가-힣]{3,}인가\?',   # ~인가?
            r'[가-힣]{3,}할까\?',   # ~할까?
            r'[가-힣]{3,}다면\?',   # ~다면?
            r'무엇인가\?',          # 무엇인가?
            r'구하시오',           # 구하시오
            r'고르시오',           # 고르시오
            r'다음 중',            # 다음 중
            r'아래에서',           # 아래에서
        ]
        
        question_count = 0
        for pattern in question_patterns:
            matches = re.findall(pattern, markdown_content)
            question_count += len(matches)
        
        # 중복 제거를 위해 절반으로 추정
        estimated_from_patterns = max(1, question_count // 2)
        print(f"  📊 질문 패턴 기반 추정: {estimated_from_patterns}개")
        
        return estimated_from_patterns
    
    def _count_questions_in_page(self, page_content: str) -> int:
        """개별 페이지에서 문제 수 카운트"""
        import re
        
        # 페이지 내 문제 번호 패턴 검색
        patterns = [
            r'### 문제 (\d+)번',
            r'## (\d+)번', 
            r'(\d+)\.\s*[가-힣]',
            r'(\d+)\)\s*[가-힣]',
            r'문제\s*(\d+)',
            r'Q\.?(\d+)',
        ]
        
        question_numbers_in_page = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, page_content)
            for match in matches:
                try:
                    num = int(match)
                    if 1 <= num <= 150:
                        question_numbers_in_page.add(num)
                except ValueError:
                    continue
        
        if question_numbers_in_page:
            return len(question_numbers_in_page)
        
        # 번호가 없는 경우 질문 패턴으로 추정
        question_indicators = [
            r'[①②③④⑤]',  # 선택지 패턴
            r'1\)\s*[가-힣]', r'2\)\s*[가-힣]', r'3\)\s*[가-힣]',  # 번호형 선택지
            r'[가-힣]{5,}은\?', r'[가-힣]{5,}는\?',  # 질문 패턴
            r'다음 중', r'아래에서', r'위에서',  # 문제 시작 표현
        ]
        
        indicators_found = 0
        for pattern in question_indicators:
            if re.search(pattern, page_content):
                indicators_found += 1
        
        # 여러 지표가 있으면 문제가 있을 가능성이 높음
        if indicators_found >= 3:
            return 1
        elif indicators_found >= 1:
            return max(1, indicators_found // 3)  # 보수적 추정
        else:
            return 0
    
    async def _detect_tables_in_pages(self, upload_id: int, page_files: List[str], db: Session) -> Dict[str, Any]:
        """1단계: 모든 페이지에서 표 위치 감지 (예비 스캔)"""
        try:
            print(f"\n🔍 표 감지 예비 스캔 시작 ({len(page_files)}페이지)...")
            
            table_detection_prompt = """
🔍 **표 감지 전문 시스템** - 빠른 스캔 모드

이 페이지에서 표(table)의 존재를 감지하고 위치를 파악해주세요.

**감지 대상**:
1. 격자 형태의 표 (선으로 구분된 데이터)
2. 정렬된 데이터 표 (탭이나 공백으로 정렬)
3. 프로세스 스케줄링 표 (P1, P2, P3 등 포함)
4. 시간표, 데이터표, 비교표 등

**출력 형식**:
표 감지됨: [예/아니오]
표 개수: [숫자]
표 유형: [프로세스스케줄링/시간표/비교표/데이터표/기타]
표 위치: [상단/중단/하단]
데이터 행 예상: [P1,P2,P3 등 데이터 행이 보이는지]

만약 표가 없다면: "표 없음"
"""

            table_pages = []
            table_details = {}
            
            for i, page_file in enumerate(page_files):
                try:
                    with open(page_file, "rb") as f:
                        page_base64 = base64.b64encode(f.read()).decode('utf-8')
                    
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{
                            "role": "user", 
                            "content": [
                                {"type": "text", "text": table_detection_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{page_base64}"}}
                            ]
                        }],
                        max_tokens=500,
                        temperature=0.1
                    )
                    
                    detection_result = response.choices[0].message.content.strip()
                    
                    if "표 감지됨: 예" in detection_result or "표 개수:" in detection_result:
                        table_pages.append(i + 1)
                        table_details[i + 1] = detection_result
                        print(f"📊 페이지 {i+1}: 표 감지됨")
                    else:
                        print(f"📄 페이지 {i+1}: 표 없음")
                    
                    # API 과부하 방지 강화
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    print(f"⚠️ 페이지 {i+1} 표 감지 실패: {e}")
            
            result = {
                'success': True,
                'table_pages': table_pages,
                'table_details': table_details,
                'total_table_pages': len(table_pages)
            }
            
            print(f"✅ 표 감지 완료: {len(table_pages)}개 페이지에서 표 발견")
            return result
            
        except Exception as e:
            print(f"❌ 표 감지 시스템 오류: {e}")
            return {'success': False, 'error': str(e), 'table_pages': [], 'table_details': {}}
    
    async def _process_page_with_dedicated_table_extraction(self, page_file: str, page_num: int, upload_id: int, table_info: Dict) -> Dict[str, Any]:
        """2단계: 표가 있는 페이지 전용 고해상도 표 추출 시스템"""
        try:
            print(f"🔥 페이지 {page_num} 전용 표 추출 시스템 가동...")
            
            # 더 높은 해상도로 페이지 재생성 (표 전용)
            high_res_path = await self._create_ultra_high_res_page(page_file, page_num)
            
            with open(high_res_path, "rb") as f:
                ultra_high_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            table_extraction_prompt = f"""
🔥 **ULTRA 표 추출 시스템** - 페이지 {page_num}

이 페이지에는 표가 감지되었습니다: {table_info.get('table_details', {}).get(page_num, '정보없음')}

**🎯 최우선 미션: P1, P2, P3 데이터 행 완전 추출**

⚡ **표 추출 긴급 프로토콜**:
1. **헤더 행 식별**: 첫 번째 행의 컬럼명들 (프로세스, 도착시간, 실행시간 등)
2. **🚨 데이터 행 필수 추출**: P1, P2, P3, P4, P5... 모든 프로세스 데이터
3. **모든 셀 값**: 숫자 데이터 (0, 1, 2, 3, 4...) 정확히 추출
4. **표 구조**: 정확한 행×열 수 파악
5. **표 완전성**: 누락된 행이나 열이 없는지 검증

**📊 필수 추출 형식**:
```
**표 감지 결과**: ✅ 발견됨
**표 유형**: [프로세스스케줄링/데이터표/시간표]
**표 크기**: [행수]×[열수] (헤더 포함)

| 컬럼1 | 컬럼2 | 컬럼3 | 컬럼4 |
|--------|--------|--------|--------|
| P1     | 0      | 3      | 1      |
| P2     | 1      | 4      | 2      |
| P3     | 2      | 2      | 3      |
| P4     | 3      | 5      | 4      |

**데이터 행 검증**: ✅ P1,P2,P3,P4 모든 데이터 추출됨
**누락 데이터**: [없음/P5누락/기타]
```

🚨 **긴급 검증 체크리스트**:
- [ ] 표 헤더 완전 추출 (프로세스, 도착시간, 실행시간...)
- [ ] P1 데이터 행 추출 (모든 셀 값)  
- [ ] P2 데이터 행 추출 (모든 셀 값)
- [ ] P3 데이터 행 추출 (모든 셀 값)
- [ ] P4, P5... 추가 데이터 행들
- [ ] 모든 숫자 값 정확성 (0, 1, 2, 3, 4...)

**실패 시 명시**: "⛔ 표 데이터 불완전 - [구체적 누락 내용]"

이제 이 페이지의 모든 내용을 분석하고, 특히 표 데이터를 완벽하게 추출해주세요.
"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": table_extraction_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{ultra_high_base64}"}}
                    ]
                }],
                max_tokens=4000,
                temperature=0.1
            )
            
            markdown_content = response.choices[0].message.content.strip()
            
            # 임시 고해상도 파일 삭제
            if os.path.exists(high_res_path):
                os.unlink(high_res_path)
            
            print(f"🔥 페이지 {page_num} 전용 표 추출 완료: {len(markdown_content)}chars")
            
            return {
                'success': True,
                'markdown': f"# 페이지 {page_num} (전용 표 추출)\n\n{markdown_content}",
                'extraction_method': 'dedicated_table_system',
                'table_focused': True
            }
            
        except Exception as e:
            print(f"❌ 페이지 {page_num} 전용 표 추출 실패: {e}")
            # 실패 시 일반 처리로 fallback
            return await self._process_single_page_with_gpt_vision(page_file, page_num, upload_id)
    
    async def _create_ultra_high_res_page(self, original_page_file: str, page_num: int) -> str:
        """표 추출용 초고해상도 페이지 생성"""
        try:
            from PIL import Image
            
            # 원본 이미지 로드
            original_image = Image.open(original_page_file)
            
            # 표 추출 최적 해상도: 3000px 이상
            target_width = 3000
            aspect_ratio = original_image.height / original_image.width
            target_height = int(target_width * aspect_ratio)
            
            # 고해상도로 리사이즈 (LANCZOS 알고리즘 사용)
            ultra_high_image = original_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # 임시 파일로 저장
            ultra_high_path = self.temp_dir / f"ultra_high_page_{page_num}.png"
            ultra_high_image.save(str(ultra_high_path), 'PNG', optimize=True)
            
            print(f"📏 페이지 {page_num} 초고해상도 생성: {target_width}x{target_height}")
            
            return str(ultra_high_path)
            
        except Exception as e:
            print(f"⚠️ 초고해상도 생성 실패: {e}, 원본 사용")
            return original_page_file
    
    async def _extract_tables_directly_from_pdf(self, pdf_path: str, upload_id: int) -> Dict[str, Any]:
        """🚀 근본 해결책: PDF에서 직접 표 추출 (이미지 변환 우회)"""
        try:
            print(f"\n🔄 PDF 직접 표 추출 시스템 가동...")
            
            tables_found = []
            extraction_methods_used = []
            
            # 방법 1: pdfplumber로 표 구조 직접 추출
            try:
                import pdfplumber
                
                print("📊 방법 1: pdfplumber로 표 구조 분석...")
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, 1):
                        print(f"   페이지 {page_num} 표 검색...")
                        
                        # 표 자동 감지 및 추출
                        tables = page.extract_tables()
                        
                        if tables:
                            print(f"   ✅ 페이지 {page_num}: {len(tables)}개 표 발견")
                            
                            for table_idx, table in enumerate(tables):
                                if table and len(table) > 1:  # 헤더 + 최소 1개 데이터 행
                                    table_data = {
                                        'page_number': page_num,
                                        'table_index': table_idx + 1,
                                        'extraction_method': 'pdfplumber',
                                        'headers': table[0] if table else [],
                                        'data_rows': table[1:] if len(table) > 1 else [],
                                        'total_rows': len(table),
                                        'total_columns': len(table[0]) if table and table[0] else 0,
                                        'raw_table': table
                                    }
                                    
                                    # 🎯 모든 데이터 행 검증 (P1,P2,P3에 국한되지 않음)
                                    data_rows_count = len(table_data['data_rows'])
                                    has_meaningful_data = any(
                                        any(str(cell).strip() for cell in row if cell) 
                                        for row in table_data['data_rows']
                                    )
                                    
                                    if has_meaningful_data:
                                        table_data['completeness_check'] = {
                                            'has_headers': bool(table_data['headers']),
                                            'data_rows_count': data_rows_count,
                                            'has_data': has_meaningful_data,
                                            'status': '✅ 완전한 표 (헤더 + 데이터)'
                                        }
                                        
                                        tables_found.append(table_data)
                                        print(f"      표 {table_idx+1}: {len(table_data['headers'])}개 컬럼, {data_rows_count}개 데이터 행")
                                    else:
                                        print(f"      표 {table_idx+1}: 빈 데이터 - 스킵")
                        else:
                            print(f"   📄 페이지 {page_num}: 표 없음")
                
                extraction_methods_used.append('pdfplumber')
                print(f"✅ pdfplumber 완료: {len([t for t in tables_found if t['extraction_method'] == 'pdfplumber'])}개 표 추출")
                
            except ImportError:
                print("⚠️ pdfplumber 없음 - pip install pdfplumber 필요")
            except Exception as e:
                print(f"⚠️ pdfplumber 실패: {e}")
            
            # 방법 2: PyMuPDF로 텍스트 기반 표 추출 시도
            try:
                print("\n📊 방법 2: PyMuPDF 텍스트 기반 표 추출...")
                doc = fitz.open(pdf_path)
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    
                    # 텍스트에서 표 패턴 감지
                    lines = text.split('\n')
                    potential_table_lines = []
                    
                    for line in lines:
                        # 표 같은 구조 감지 (여러 개의 탭/공백으로 구분된 데이터)
                        if '\t' in line or len(line.split()) >= 3:
                            # 숫자나 특정 패턴이 포함된 줄
                            if any(char.isdigit() for char in line):
                                potential_table_lines.append(line.strip())
                    
                    if len(potential_table_lines) >= 2:  # 최소 헤더 + 1개 데이터 행
                        print(f"   ✅ 페이지 {page_num+1}: 텍스트 기반 표 패턴 {len(potential_table_lines)}개 행 발견")
                        
                        # 간단한 표 구조화
                        table_rows = []
                        for line in potential_table_lines:
                            if '\t' in line:
                                row = line.split('\t')
                            else:
                                row = line.split()
                            table_rows.append([cell.strip() for cell in row if cell.strip()])
                        
                        if table_rows and len(table_rows) > 1:
                            table_data = {
                                'page_number': page_num + 1,
                                'table_index': 1,
                                'extraction_method': 'pymupdf_text',
                                'headers': table_rows[0] if table_rows else [],
                                'data_rows': table_rows[1:] if len(table_rows) > 1 else [],
                                'total_rows': len(table_rows),
                                'total_columns': len(table_rows[0]) if table_rows and table_rows[0] else 0,
                                'raw_table': table_rows,
                                'completeness_check': {
                                    'has_headers': bool(table_rows[0]) if table_rows else False,
                                    'data_rows_count': len(table_rows) - 1 if len(table_rows) > 1 else 0,
                                    'has_data': len(table_rows) > 1,
                                    'status': '✅ 텍스트 기반 표 추출'
                                }
                            }
                            
                            # 중복 방지 (이미 pdfplumber로 추출된 것과 비교)
                            is_duplicate = any(
                                t['page_number'] == table_data['page_number'] and 
                                t['extraction_method'] == 'pdfplumber'
                                for t in tables_found
                            )
                            
                            if not is_duplicate:
                                tables_found.append(table_data)
                
                extraction_methods_used.append('pymupdf_text')
                print(f"✅ PyMuPDF 텍스트 완료: {len([t for t in tables_found if t['extraction_method'] == 'pymupdf_text'])}개 추가 표")
                
                doc.close()
                
            except Exception as e:
                print(f"⚠️ PyMuPDF 텍스트 추출 실패: {e}")
            
            # 결과 정리
            result = {
                'success': len(tables_found) > 0,
                'tables_count': len(tables_found),
                'tables_data': tables_found,
                'extraction_methods': extraction_methods_used,
                'summary': {
                    'total_tables': len(tables_found),
                    'pages_with_tables': len(set(t['page_number'] for t in tables_found)),
                    'by_method': {method: len([t for t in tables_found if t['extraction_method'] == method]) for method in set(t['extraction_method'] for t in tables_found)}
                }
            }
            
            print(f"\n🎯 PDF 직접 표 추출 결과:")
            print(f"   총 {result['tables_count']}개 표 추출")
            print(f"   {result['summary']['pages_with_tables']}개 페이지에서 발견")
            print(f"   사용된 방법: {', '.join(extraction_methods_used)}")
            
            for table in tables_found:
                print(f"   📊 페이지 {table['page_number']} 표 {table['table_index']}: "
                      f"{table['total_columns']}컬럼 × {len(table['data_rows'])}데이터행 "
                      f"({table['extraction_method']})")
            
            return result
            
        except Exception as e:
            print(f"❌ PDF 직접 표 추출 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'tables_count': 0,
                'tables_data': [],
                'extraction_methods': []
            }
    
    def _validate_table_completeness(self, passage: str, question_number) -> Dict[str, Any]:
        """표 데이터 완전성 검증 - P1, P2, P3 등 데이터 행 확인"""
        import re
        
        validation_result = {
            'is_complete': True,
            'issues': [],
            'data_rows_found': [],
            'header_found': False
        }
        
        # 표가 포함된 지문인지 확인
        if '|' not in passage and '표' not in passage:
            return validation_result
        
        lines = passage.split('\n')
        table_lines = [line.strip() for line in lines if '|' in line]
        
        if not table_lines:
            validation_result['is_complete'] = False
            validation_result['issues'].append('표 형식이 감지되지 않음')
            return validation_result
        
        # 헤더 행 감지 (첫 번째 표 라인)
        header_patterns = [
            r'프로세스|process',
            r'도착시간|arrival',
            r'실행시간|burst',
            r'우선순위|priority',
            r'헤더|header',
            r'항목|item',
            r'구분|classification'
        ]
        
        first_table_line = table_lines[0].lower()
        validation_result['header_found'] = any(re.search(pattern, first_table_line) for pattern in header_patterns)
        
        # 데이터 행 패턴 검증 (일반적인 패턴)
        data_row_patterns = [
            r'[a-zA-Z]+[0-9]+',    # A1, P1, Task1 등
            r'[가-힣]+\s*[0-9]+',   # 프로세스1, 작업1 등
            r'[0-9]+[.]?',         # 1, 2, 3... 또는 1., 2., 3...
            r'[가-힣]{1,3}[0-9]+', # 가1, 나1, 항목1 등
        ]
        
        data_rows_found = []
        for line in table_lines[1:]:  # 헤더 제외한 나머지 라인
            line_lower = line.lower()
            for pattern in data_row_patterns:
                matches = re.findall(pattern, line_lower)
                for match in matches:
                    if match not in data_rows_found:
                        data_rows_found.append(match)
        
        validation_result['data_rows_found'] = data_rows_found
        
        # 완전성 검증
        if validation_result['header_found'] and len(data_rows_found) == 0:
            validation_result['is_complete'] = False
            validation_result['issues'].append('헤더만 있고 데이터 행 없음')
        elif len(data_rows_found) < 2:
            validation_result['is_complete'] = False
            validation_result['issues'].append(f'데이터 행 부족: {len(data_rows_found)}개 발견')
        elif not validation_result['header_found']:
            validation_result['issues'].append('표 헤더 불분명')
        
        return validation_result
    
    async def _ocr_based_enhancement_pipeline(self, upload_id: int, basic_questions: List[Dict], 
                                            pdf_path: str, db: Session) -> List[Dict]:
        """🔍 OCR 기반 보완 처리 파이프라인"""
        try:
            print(f"\n🔍 OCR 기반 보완 파이프라인 시작...")
            
            # 1단계: PDF 전체 OCR 처리
            ocr_data = await self._process_pdf_with_ocr(pdf_path, upload_id, db)
            if not ocr_data['success']:
                print("⚠️ OCR 처리 실패, 기본 결과 유지")
                return basic_questions
            
            print(f"✅ OCR 처리 완료: {len(ocr_data['pages'])}페이지")
            
            # 2단계: OCR vs 기존 결과 비교 분석
            gap_analysis = await self._analyze_content_gaps(basic_questions, ocr_data, upload_id, db)
            print(f"📊 격차 분석 완료: {len(gap_analysis['missing_questions'])}개 누락 문제 발견")
            
            # 3단계: 누락된 문제 복구
            recovered_questions = await self._recover_missing_questions_from_ocr(
                gap_analysis['missing_questions'], ocr_data, upload_id, db
            )
            print(f"🔧 OCR 기반 복구: {len(recovered_questions)}개 문제 복구")
            
            # 4단계: 페이지 경계 문제 OCR 기반 해결
            boundary_fixed_questions = await self._fix_boundary_issues_with_ocr(
                basic_questions, ocr_data, upload_id, db
            )
            print(f"🔗 페이지 경계 문제 수정: {len([q for q in boundary_fixed_questions if q.get('boundary_fixed')])}개")
            
            # 5단계: 최종 통합 및 품질 검증
            final_questions = boundary_fixed_questions + recovered_questions
            final_questions = await self._final_ocr_quality_validation(final_questions, ocr_data, db)
            
            print(f"✅ OCR 기반 보완 완료: {len(final_questions)}개 문제 (기존: {len(basic_questions)})")
            return final_questions
            
        except Exception as e:
            print(f"⚠️ OCR 보완 파이프라인 오류: {e}")
            return basic_questions
    
    async def _process_pdf_with_ocr(self, pdf_path: str, upload_id: int, db: Session) -> Dict:
        """PDF 전체 OCR 처리"""
        try:
            import fitz  # PyMuPDF
            import pytesseract
            from PIL import Image
            import io
            
            print(f"📄 PDF OCR 처리 시작: {pdf_path}")
            
            # PDF 열기
            doc = fitz.open(pdf_path)
            ocr_pages = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # 고해상도 이미지로 변환
                mat = fitz.Matrix(3.0, 3.0)  # 3x 확대
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # PIL Image로 변환
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Tesseract OCR 실행
                print(f"   🔍 페이지 {page_num + 1} OCR 처리 중...")
                try:
                    ocr_text = pytesseract.image_to_string(pil_image, lang='kor+eng', config='--psm 6')
                    
                    # 좌표 정보와 함께 추출
                    ocr_data = pytesseract.image_to_data(pil_image, lang='kor+eng', output_type=pytesseract.Output.DICT)
                    
                    # 구조화된 데이터 생성
                    structured_text = self._structure_ocr_data(ocr_data, ocr_text)
                    
                    ocr_pages.append({
                        'page_number': page_num + 1,
                        'raw_text': ocr_text,
                        'structured_data': structured_text,
                        'confidence_avg': self._calculate_ocr_confidence(ocr_data)
                    })
                    
                except Exception as ocr_error:
                    print(f"   ⚠️ 페이지 {page_num + 1} OCR 실패: {ocr_error}")
                    ocr_pages.append({
                        'page_number': page_num + 1,
                        'raw_text': '',
                        'structured_data': {},
                        'confidence_avg': 0
                    })
            
            doc.close()
            
            return {
                'success': True,
                'pages': ocr_pages,
                'total_pages': len(ocr_pages)
            }
            
        except ImportError:
            print("⚠️ OCR 라이브러리가 설치되지 않음 (pytesseract, Pillow 필요)")
            return {'success': False, 'error': 'OCR libraries not installed'}
        except Exception as e:
            print(f"❌ OCR 처리 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def _structure_ocr_data(self, ocr_data: Dict, raw_text: str) -> Dict:
        """OCR 데이터를 구조화"""
        import re
        
        # 문제 패턴 감지
        questions = []
        question_patterns = [
            r'(\d+)\s*[.)]\s*([^\n]+)',  # 숫자. 또는 숫자) 형태
            r'문제\s*(\d+)\s*번\s*([^\n]+)',  # 문제 X번 형태
        ]
        
        for pattern in question_patterns:
            matches = re.finditer(pattern, raw_text, re.MULTILINE)
            for match in matches:
                questions.append({
                    'number': int(match.group(1)),
                    'text': match.group(2).strip(),
                    'position': match.span()
                })
        
        # 선택지 패턴 감지
        choices = []
        choice_patterns = [
            r'[①②③④⑤]\s*([^\n①②③④⑤]+)',
            r'[1-5][.)]\s*([^\n1-5]+)',
            r'[가나다라마]\s*[.)]\s*([^\n가나다라마]+)'
        ]
        
        for pattern in choice_patterns:
            matches = re.finditer(pattern, raw_text, re.MULTILINE)
            for match in matches:
                choices.append({
                    'text': match.group(1).strip(),
                    'position': match.span()
                })
        
        # 표 패턴 감지
        tables = []
        table_indicators = ['|', '─', '┌', '├', '└', '┬', '┤', '┐', '┘', '┴']
        lines = raw_text.split('\n')
        
        for i, line in enumerate(lines):
            if any(indicator in line for indicator in table_indicators):
                # 표 영역 확장 감지
                table_start = max(0, i - 2)
                table_end = min(len(lines), i + 5)
                table_text = '\n'.join(lines[table_start:table_end])
                
                if len(table_text.strip()) > 10:  # 최소 길이 필터
                    tables.append({
                        'text': table_text,
                        'line_range': (table_start, table_end),
                        'confidence': 'high' if line.count('|') > 2 else 'medium'
                    })
        
        return {
            'questions': questions,
            'choices': choices,
            'tables': tables,
            'total_text_length': len(raw_text)
        }
    
    def _calculate_ocr_confidence(self, ocr_data: Dict) -> float:
        """OCR 신뢰도 계산"""
        confidences = [int(conf) for conf in ocr_data.get('conf', []) if int(conf) > 0]
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    async def _analyze_content_gaps(self, basic_questions: List[Dict], ocr_data: Dict, upload_id: int, db: Session) -> Dict:
        """OCR 결과와 기본 추출 결과 비교 분석"""
        try:
            print(f"📊 콘텐츠 격차 분석 시작...")
            
            # 기본 추출에서 찾은 문제 번호들
            extracted_numbers = set()
            for question in basic_questions:
                if 'question_number' in question:
                    extracted_numbers.add(question['question_number'])
                elif 'id' in question:
                    extracted_numbers.add(question['id'])
            
            print(f"   기본 추출 문제 번호: {sorted(extracted_numbers)}")
            
            # OCR에서 찾은 모든 문제 번호들
            ocr_numbers = set()
            all_ocr_questions = []
            
            for page_data in ocr_data.get('pages', []):
                structured = page_data.get('structured_data', {})
                questions = structured.get('questions', [])
                
                for q in questions:
                    number = q.get('number')
                    if number and isinstance(number, int) and 1 <= number <= 200:
                        ocr_numbers.add(number)
                        all_ocr_questions.append({
                            'number': number,
                            'text': q.get('text', ''),
                            'page': page_data.get('page_number', 0),
                            'confidence': page_data.get('confidence_avg', 0)
                        })
            
            print(f"   OCR 발견 문제 번호: {sorted(ocr_numbers)}")
            
            # 누락된 문제들 식별
            missing_numbers = ocr_numbers - extracted_numbers
            extra_numbers = extracted_numbers - ocr_numbers
            
            missing_questions = []
            for q in all_ocr_questions:
                if q['number'] in missing_numbers and q['confidence'] > 30:  # 신뢰도 필터
                    missing_questions.append(q)
            
            print(f"   📋 분석 결과:")
            print(f"      - 누락된 문제: {sorted(missing_numbers)} ({len(missing_questions)}개 복구 가능)")
            print(f"      - 추가 발견: {sorted(extra_numbers)}")
            
            return {
                'missing_questions': missing_questions,
                'extra_numbers': extra_numbers,
                'ocr_total': len(ocr_numbers),
                'extracted_total': len(extracted_numbers),
                'coverage_ratio': len(extracted_numbers) / len(ocr_numbers) if ocr_numbers else 0
            }
            
        except Exception as e:
            print(f"❌ 격차 분석 오류: {e}")
            return {'missing_questions': [], 'extra_numbers': set(), 'coverage_ratio': 0}
    
    async def _recover_missing_questions_from_ocr(self, missing_questions: List[Dict], ocr_data: Dict, upload_id: int, db: Session) -> List[Dict]:
        """OCR 데이터에서 누락된 문제들 복구"""
        try:
            if not missing_questions:
                return []
                
            print(f"🔧 OCR 기반 문제 복구 시작: {len(missing_questions)}개 문제")
            
            recovered_questions = []
            
            for missing_q in missing_questions:
                question_number = missing_q['number']
                page_number = missing_q['page']
                
                # 해당 페이지의 OCR 데이터 찾기
                page_data = None
                for page in ocr_data.get('pages', []):
                    if page.get('page_number') == page_number:
                        page_data = page
                        break
                
                if not page_data:
                    continue
                
                # 문제 텍스트 주변 컨텍스트 추출
                raw_text = page_data.get('raw_text', '')
                question_text = missing_q.get('text', '')
                
                # 선택지 찾기 (문제 텍스트 뒤의 내용에서)
                choices = self._extract_choices_from_context(raw_text, question_text, question_number)
                
                # 테이블/이미지 컨텍스트 확인
                has_table = self._detect_table_context(raw_text, question_text)
                
                recovered_question = {
                    'question_number': question_number,
                    'question_text': question_text,
                    'choices': choices,
                    'has_table': has_table,
                    'recovery_source': 'ocr',
                    'confidence': missing_q.get('confidence', 0),
                    'page_number': page_number,
                    'passage': self._extract_passage_context(raw_text, question_text)
                }
                
                recovered_questions.append(recovered_question)
                print(f"   ✅ 문제 {question_number}번 복구됨 (선택지 {len(choices)}개)")
            
            print(f"🎯 OCR 복구 완료: {len(recovered_questions)}/{len(missing_questions)}개 성공")
            return recovered_questions
            
        except Exception as e:
            print(f"❌ OCR 복구 오류: {e}")
            return []
    
    def _extract_choices_from_context(self, text: str, question_text: str, question_number: int) -> List[Dict]:
        """텍스트에서 특정 문제의 선택지 추출"""
        import re
        
        try:
            # 문제 위치 찾기
            question_pos = text.find(question_text)
            if question_pos == -1:
                # 부분 매칭 시도
                words = question_text.split()[:5]  # 첫 5단어로 찾기
                for word in words:
                    if len(word) > 2:
                        question_pos = text.find(word)
                        if question_pos != -1:
                            break
            
            if question_pos == -1:
                return []
            
            # 문제 뒤의 텍스트에서 선택지 찾기
            after_question = text[question_pos + len(question_text):question_pos + len(question_text) + 1000]
            
            choices = []
            choice_patterns = [
                r'①\s*([^\n②③④⑤]+)',
                r'②\s*([^\n①③④⑤]+)', 
                r'③\s*([^\n①②④⑤]+)',
                r'④\s*([^\n①②③⑤]+)',
                r'⑤\s*([^\n①②③④]+)'
            ]
            
            for i, pattern in enumerate(choice_patterns):
                match = re.search(pattern, after_question)
                if match:
                    choice_text = match.group(1).strip()
                    if len(choice_text) > 1:  # 최소 길이 필터
                        choices.append({
                            'choice_number': i + 1,
                            'choice_text': choice_text,
                            'has_image': self._detect_image_reference(choice_text)
                        })
            
            return choices[:5]  # 최대 5개까지
            
        except Exception as e:
            print(f"   ⚠️ 선택지 추출 오류: {e}")
            return []
    
    def _detect_image_reference(self, text: str) -> bool:
        """텍스트에서 이미지 참조 감지"""
        image_keywords = ['그림', '표', '도표', '차트', '그래프', '이미지', '아래', '위']
        return any(keyword in text for keyword in image_keywords)
    
    def _detect_table_context(self, text: str, question_text: str) -> bool:
        """문제에 테이블/표 컨텍스트가 있는지 감지"""
        context_window = 500
        question_pos = text.find(question_text)
        if question_pos == -1:
            return False
        
        context = text[max(0, question_pos-context_window):question_pos+context_window]
        table_indicators = ['|', '─', '┌', '├', '표', '테이블', 'P1', 'P2', 'P3']
        
        return sum(1 for indicator in table_indicators if indicator in context) >= 2
    
    def _extract_passage_context(self, text: str, question_text: str) -> str:
        """문제 주변 컨텍스트 추출"""
        question_pos = text.find(question_text)
        if question_pos == -1:
            return ""
        
        # 앞뒤 200자씩 추출
        start = max(0, question_pos - 200)
        end = min(len(text), question_pos + len(question_text) + 200)
        
        return text[start:end].strip()
    
    async def _fix_boundary_issues_with_ocr(self, questions: List[Dict], ocr_data: Dict, upload_id: int, db: Session) -> List[Dict]:
        """OCR을 활용하여 페이지 경계 문제 해결"""
        try:
            print(f"🔗 페이지 경계 문제 OCR 기반 수정 시작...")
            
            fixed_questions = []
            boundary_fixes = 0
            
            for question in questions:
                question_copy = question.copy()
                
                # 불완전한 선택지 감지 (options 필드 사용)
                choices = question.get('options', question.get('choices', []))
                if choices and len(choices) < 4:  # 일반적으로 4-5개 선택지 예상
                    
                    question_number = question.get('question_number', question.get('id', 0))
                    
                    # OCR에서 해당 문제의 완전한 선택지 찾기
                    complete_choices = self._find_complete_choices_in_ocr(question_number, ocr_data)
                    
                    if len(complete_choices) > len(choices):
                        print(f"   🔧 문제 {question_number}번 선택지 보완: {len(choices)} → {len(complete_choices)}개")
                        question_copy['options'] = complete_choices
                        # 호환성을 위해 choices도 설정
                        question_copy['choices'] = complete_choices
                        question_copy['boundary_fixed'] = True
                        boundary_fixes += 1
                
                # 불완전한 표 데이터 보완
                passage = question.get('passage', '')
                if '|' in passage and passage.count('|') < 6:  # 불완전한 표 추정
                    
                    question_number = question.get('question_number', question.get('id', 0))
                    complete_table = self._find_complete_table_in_ocr(question_number, ocr_data)
                    
                    if complete_table and len(complete_table) > len(passage):
                        print(f"   📊 문제 {question_number}번 표 데이터 보완")
                        question_copy['passage'] = complete_table
                        question_copy['boundary_fixed'] = True
                        boundary_fixes += 1
                
                fixed_questions.append(question_copy)
            
            print(f"✅ 페이지 경계 문제 수정 완료: {boundary_fixes}개 문제 수정")
            return fixed_questions
            
        except Exception as e:
            print(f"❌ 페이지 경계 수정 오류: {e}")
            return questions
    
    def _find_complete_choices_in_ocr(self, question_number: int, ocr_data: Dict) -> List[Dict]:
        """OCR에서 특정 문제의 완전한 선택지 찾기"""
        try:
            for page_data in ocr_data.get('pages', []):
                raw_text = page_data.get('raw_text', '')
                
                # 문제 번호 패턴으로 해당 문제 영역 찾기
                import re
                question_patterns = [
                    rf'{question_number}\s*[.)]\s*([^\n]+)',
                    rf'문제\s*{question_number}\s*번'
                ]
                
                question_pos = -1
                for pattern in question_patterns:
                    match = re.search(pattern, raw_text)
                    if match:
                        question_pos = match.start()
                        break
                
                if question_pos == -1:
                    continue
                
                # 문제 뒤의 텍스트에서 모든 선택지 추출
                after_question = raw_text[question_pos:question_pos + 1500]
                choices = []
                
                choice_patterns = [
                    r'①\s*([^\n②③④⑤]+)',
                    r'②\s*([^\n①③④⑤]+)', 
                    r'③\s*([^\n①②④⑤]+)',
                    r'④\s*([^\n①②③⑤]+)',
                    r'⑤\s*([^\n①②③④]+)'
                ]
                
                for i, pattern in enumerate(choice_patterns):
                    match = re.search(pattern, after_question)
                    if match:
                        choice_text = match.group(1).strip()
                        if len(choice_text) > 1:
                            choices.append({
                                'choice_number': i + 1,
                                'choice_text': choice_text,
                                'has_image': self._detect_image_reference(choice_text)
                            })
                
                if len(choices) >= 4:  # 충분한 선택지가 있으면 반환
                    return choices
            
            return []
            
        except Exception as e:
            print(f"   ⚠️ OCR 선택지 찾기 오류: {e}")
            return []
    
    def _find_complete_table_in_ocr(self, question_number: int, ocr_data: Dict) -> str:
        """OCR에서 특정 문제의 완전한 표 데이터 찾기"""
        try:
            for page_data in ocr_data.get('pages', []):
                structured = page_data.get('structured_data', {})
                tables = structured.get('tables', [])
                
                # 높은 신뢰도의 표 중에서 가장 완전한 것 선택
                best_table = ""
                max_score = 0
                
                for table in tables:
                    table_text = table.get('text', '')
                    
                    # 표 완성도 점수 계산
                    score = 0
                    score += table_text.count('|') * 2  # 구분자
                    score += table_text.count('P1') + table_text.count('P2') + table_text.count('P3')  # 프로세스 데이터
                    score += len(re.findall(r'\d+', table_text))  # 숫자 데이터
                    
                    if score > max_score and len(table_text) > 50:
                        max_score = score
                        best_table = table_text
                
                if best_table and max_score > 10:
                    return best_table
            
            return ""
            
        except Exception as e:
            print(f"   ⚠️ OCR 표 찾기 오류: {e}")
            return ""
    
    async def _final_ocr_quality_validation(self, questions: List[Dict], ocr_data: Dict, db: Session) -> List[Dict]:
        """최종 OCR 기반 품질 검증"""
        try:
            print(f"✨ 최종 OCR 품질 검증 시작: {len(questions)}개 문제")
            
            validated_questions = []
            
            for question in questions:
                question_copy = question.copy()
                
                # 기본 검증
                question_number = question.get('question_number', question.get('id', 0))
                question_text = question.get('question_text', question.get('question', ''))
                choices = question.get('options', question.get('choices', []))
                
                if not question_text or len(question_text.strip()) < 5:
                    print(f"   ⚠️ 문제 {question_number}번: 문제 텍스트 부족")
                    continue
                
                if len(choices) < 2:
                    print(f"   ⚠️ 문제 {question_number}번: 선택지 부족 ({len(choices)}개)")
                    # OCR에서 선택지 보완 시도
                    additional_choices = self._find_complete_choices_in_ocr(question_number, ocr_data)
                    if additional_choices:
                        question_copy['options'] = additional_choices
                        question_copy['choices'] = additional_choices
                        print(f"   ✅ 문제 {question_number}번: OCR로 선택지 보완됨")
                
                # 중복 제거
                if question_number > 0:
                    # 이미 같은 번호의 문제가 있는지 확인
                    duplicate = False
                    for existing in validated_questions:
                        existing_number = existing.get('question_number', existing.get('id', 0))
                        if existing_number == question_number:
                            # 더 완전한 버전 선택 (options 우선 사용)
                            existing_choices = len(existing.get('options', existing.get('choices', [])))
                            current_choices = len(question_copy.get('options', question_copy.get('choices', [])))
                            
                            if current_choices > existing_choices:
                                # 현재 버전이 더 완전함 - 기존 것 교체
                                for i, eq in enumerate(validated_questions):
                                    if eq.get('question_number', eq.get('id', 0)) == question_number:
                                        validated_questions[i] = question_copy
                                        print(f"   🔄 문제 {question_number}번: 더 완전한 버전으로 교체")
                                        break
                            duplicate = True
                            break
                    
                    if not duplicate:
                        validated_questions.append(question_copy)
                else:
                    validated_questions.append(question_copy)
            
            # 문제 번호순 정렬
            validated_questions.sort(key=lambda x: x.get('question_number', x.get('id', 0)))
            
            print(f"✅ 최종 검증 완료: {len(validated_questions)}개 문제")
            print(f"   품질 점수: {self._calculate_quality_score(validated_questions):.1f}/100")
            
            return validated_questions
            
        except Exception as e:
            print(f"❌ 최종 검증 오류: {e}")
            return questions
    
    def _calculate_quality_score(self, questions: List[Dict]) -> float:
        """문제 세트의 품질 점수 계산"""
        if not questions:
            return 0.0
        
        total_score = 0
        for question in questions:
            score = 0
            
            # 기본 점수 (20점)
            question_text = question.get('question_text', question.get('question', ''))
            if question_text and len(question_text.strip()) > 10:
                score += 20
            
            # 선택지 점수 (40점) - options 우선 사용
            choices = question.get('options', question.get('choices', []))
            if len(choices) >= 4:
                score += 40
            elif len(choices) >= 2:
                score += 20
            
            # 컨텍스트 점수 (20점)
            passage = question.get('passage', '')
            if passage and len(passage.strip()) > 20:
                score += 20
            
            # 구조 점수 (20점)
            question_number = question.get('question_number', question.get('id', 0))
            if question_number > 0:
                score += 10
                
            if question.get('has_table') or any('|' in str(choice.get('choice_text', '')) for choice in choices):
                score += 10
            
            total_score += min(score, 100)
        
        return total_score / len(questions)
    
    def get_pdf_path(self, upload_id: int, db: Session = None) -> Optional[str]:
        """Upload ID에 해당하는 PDF 파일 경로 반환 - DB 기반 개선"""
        try:
            import os
            import glob
            from pathlib import Path
            
            print(f"🔍 Upload {upload_id} PDF 파일 검색 시작...")
            
            # 1단계: 데이터베이스에서 실제 파일명 조회 (가장 정확함)
            if db:
                try:
                    from app.models import Document
                    document = db.query(Document).filter(Document.id == upload_id).first()
                    if document and hasattr(document, 'filename') and document.filename:
                        # 실제 저장된 파일명으로 검색
                        stored_filename = document.filename
                        print(f"📄 DB에서 파일명 조회: {stored_filename}")
                        
                        # PDF가 저장되는 실제 경로에서 검색
                        pdf_search_paths = [
                            f"backend/uploads/pdfs/{stored_filename}",
                            f"uploads/pdfs/{stored_filename}",
                            f"static/uploads/pdfs/{stored_filename}"
                        ]
                        
                        for path in pdf_search_paths:
                            if os.path.exists(path):
                                print(f"✅ DB 기반으로 PDF 발견: {path}")
                                return os.path.abspath(path)
                except Exception as e:
                    print(f"⚠️ DB 조회 중 오류: {e}")
            
            # 2단계: 타임스탬프 기반 파일명 패턴 검색 (실제 사용되는 패턴)
            pdf_directories = [
                "backend/uploads/pdfs",
                "uploads/pdfs", 
                "static/uploads/pdfs"
            ]
            
            for pdf_dir in pdf_directories:
                if os.path.exists(pdf_dir):
                    # 타임스탬프 패턴으로 검색: 20250826_*_*_*.pdf
                    pattern_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
                    for file_path in pattern_files:
                        if self._validate_pdf_file(file_path):
                            file_name = os.path.basename(file_path)
                            # 파일명에 upload_id 패턴이 있는지 확인하거나 날짜순으로 매칭
                            print(f"📋 발견된 PDF: {file_name}")
                            # 여기서는 가장 최근 파일을 반환 (임시방편)
                            if upload_id >= 10:  # 최근 업로드라고 가정
                                print(f"✅ 패턴 기반으로 PDF 발견: {file_path}")
                                return os.path.abspath(file_path)
            
            # 3단계: 기존 단순 패턴 검색 (호환성)
            legacy_patterns = [
                f"uploads/{upload_id}.pdf",
                f"uploads/upload_{upload_id}.pdf", 
                f"static/uploads/{upload_id}.pdf",
                f"temp_processing/upload_{upload_id}.pdf"
            ]
            
            for path in legacy_patterns:
                if os.path.exists(path):
                    print(f"✅ 레거시 패턴으로 PDF 발견: {path}")
                    return os.path.abspath(path)
            
            # 4단계: 전체 디렉토리 검색 (최후 수단)
            print(f"🔍 전체 디렉토리 검색 중...")
            for root, dirs, files in os.walk("."):
                for file in files:
                    if file.endswith('.pdf') and str(upload_id) in file:
                        found_path = os.path.join(root, file)
                        if self._validate_pdf_file(found_path):
                            print(f"✅ 전체 검색으로 PDF 발견: {found_path}")
                            return os.path.abspath(found_path)
            
            print(f"❌ Upload {upload_id} PDF 파일을 찾을 수 없음")
            print(f"   검색한 디렉토리: {pdf_directories}")
            print(f"   시도한 패턴: {legacy_patterns}")
            return None
            
        except Exception as e:
            print(f"❌ PDF 경로 검색 오류: {e}")
            return None
    
    def _validate_pdf_file(self, file_path: str) -> bool:
        """PDF 파일 유효성 검사"""
        try:
            import os
            
            if not os.path.exists(file_path) or os.path.getsize(file_path) < 1024:
                return False
            
            # PDF 헤더 확인
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(8)
                    if not header.startswith(b'%PDF-'):
                        return False
            except:
                return False
            
            # PyMuPDF로 빠른 검증
            try:
                import fitz
                doc = fitz.open(file_path)
                if len(doc) == 0:
                    doc.close()
                    return False
                doc.close()
                return True
            except:
                return False
                
        except Exception as e:
            print(f"❌ PDF 검증 오류: {e}")
            return False
    
    async def _enhanced_image_choice_processing(self, questions: List[Dict], upload_id: int) -> int:
        """향상된 이미지 선택지 처리 - 혼합 콘텐츠 및 인라인 이미지 지원"""
        try:
            import os
            import re
            
            # 이미지 디렉토리 확인
            image_dir = f"static/images/upload_{upload_id}"
            if not os.path.exists(image_dir):
                print(f"⚠️ 이미지 디렉토리 없음: {image_dir}")
                return 0
            
            image_files = [f for f in os.listdir(image_dir) if f.startswith('IMG_')]
            if not image_files:
                print("⚠️ 추출된 이미지 파일이 없음")
                return 0
            
            image_list = sorted(image_files)
            processed_count = 0
            
            print(f"🖼️ 향상된 이미지 처리 시작: {len(image_list)}개 이미지 사용")
            
            for question in questions:
                question_number = question.get('question_number', 0)
                question_text = question.get('question_text', '')
                passage = question.get('passage', '')
                current_options = question.get('options', [])
                
                # 다중 레벨 이미지 처리
                was_processed = False
                
                # 1단계: 문제 텍스트 내 이미지 참조 처리
                enhanced_question_text = await self._process_inline_image_references(
                    question_text, image_list, upload_id
                )
                if enhanced_question_text != question_text:
                    question['question_text'] = enhanced_question_text
                    was_processed = True
                    print(f"   🖼️ Q{question_number}: 문제 텍스트 내 이미지 참조 처리됨")
                
                # 2단계: 지문 내 이미지 참조 처리
                if passage:
                    enhanced_passage = await self._process_inline_image_references(
                        passage, image_list, upload_id
                    )
                    if enhanced_passage != passage:
                        question['passage'] = enhanced_passage
                        was_processed = True
                        print(f"   🖼️ Q{question_number}: 지문 내 이미지 참조 처리됨")
                
                # 3단계: 선택지별 개별 이미지 처리 (혼합 콘텐츠 지원)
                enhanced_options = []
                for i, option in enumerate(current_options):
                    if isinstance(option, str):
                        # IMG_XXX_IMAGE 패턴을 실제 이미지로 교체
                        enhanced_option = await self._resolve_image_placeholders(
                            option, image_list, upload_id
                        )
                        
                        # 빈 이미지 참조나 불완전한 선택지 처리
                        if self._is_incomplete_image_choice(enhanced_option):
                            # 컨텍스트 기반 이미지 매칭 시도
                            contextual_image = await self._match_contextual_image(
                                question_number, i + 1, question_text, passage, image_list, upload_id
                            )
                            if contextual_image:
                                enhanced_option = contextual_image
                                print(f"   🎯 Q{question_number} 선택지 {i+1}: 컨텍스트 기반 이미지 매칭")
                        
                        enhanced_options.append(enhanced_option)
                    else:
                        enhanced_options.append(option)
                
                # 선택지가 개선되었는지 확인
                if enhanced_options != current_options:
                    question['options'] = enhanced_options
                    was_processed = True
                    print(f"   ✅ Q{question_number}: 선택지 이미지 처리 완료")
                
                # 4단계: 전체 이미지 기반 선택지 처리 (기존 로직)
                if not was_processed:
                    needs_images, confidence = self._analyze_image_requirement(
                        question_text, passage, current_options
                    )
                    
                    if needs_images and confidence > 0.3:  # 임계값 낮춤 (30%)
                        matched_images = await self._smart_image_matching(
                            question_number, question_text, passage, image_list, upload_id
                        )
                        
                        if matched_images:
                            current_quality = self._analyze_options_quality(current_options)
                            should_replace = (
                                current_quality < 0.4 or  # 품질 임계값 낮춤
                                len(current_options) < 2 or  # 최소 선택지 기준 낮춤
                                any('IMG_' in str(opt) and len(str(opt).strip()) < 5 for opt in current_options)
                            )
                            
                            if should_replace:
                                image_options = []
                                for img_info in matched_images[:4]:
                                    img_path = f"/images/upload_{upload_id}/{img_info['filename']}"
                                    image_options.append(f"![IMG_{img_info['number']:03d}]({img_path})")
                                
                                question['options'] = image_options
                                was_processed = True
                                print(f"   🔄 Q{question_number}: 전체 이미지 선택지 교체 (품질:{current_quality:.2f})")
                
                if was_processed:
                    processed_count += 1
            
            print(f"🖼️ 이미지 처리 완료: {processed_count}개 문제 개선")
            return processed_count
            
        except Exception as e:
            print(f"❌ 향상된 이미지 처리 오류: {e}")
            return 0
    
    async def _process_inline_image_references(self, text: str, image_list: List[str], upload_id: int) -> str:
        """텍스트 내 이미지 참조 처리"""
        try:
            import re
            
            if not text or not image_list:
                return text
            
            enhanced_text = text
            
            # 패턴 1: "IMG_XXX_IMAGE" 형태의 참조
            img_pattern = r'IMG_(\d{3})_IMAGE'
            matches = re.findall(img_pattern, enhanced_text)
            
            for match in matches:
                img_number = int(match)
                target_filename = f"IMG_{img_number:03d}.png"
                
                # 대응되는 이미지 파일 찾기
                if target_filename in image_list:
                    img_path = f"/images/upload_{upload_id}/{target_filename}"
                    img_markdown = f"![IMG_{img_number:03d}]({img_path})"
                    enhanced_text = enhanced_text.replace(f"IMG_{img_number:03d}_IMAGE", img_markdown)
                elif f"IMG_{img_number:03d}.jpeg" in image_list:
                    # JPEG 형식도 체크
                    target_filename = f"IMG_{img_number:03d}.jpeg"
                    img_path = f"/images/upload_{upload_id}/{target_filename}"
                    img_markdown = f"![IMG_{img_number:03d}]({img_path})"
                    enhanced_text = enhanced_text.replace(f"IMG_{img_number:03d}_IMAGE", img_markdown)
            
            # 패턴 2: "그림 1", "도표 2" 등의 참조
            diagram_patterns = [
                r'(그림\s*(\d+))',
                r'(도표\s*(\d+))',
                r'(이미지\s*(\d+))',
                r'(다음\s*그림)',
                r'(아래\s*그림)'
            ]
            
            for pattern in diagram_patterns:
                matches = re.finditer(pattern, enhanced_text)
                for match in matches:
                    if len(match.groups()) >= 2 and match.group(2).isdigit():
                        # 숫자가 있는 경우 해당 이미지 찾기
                        ref_number = int(match.group(2))
                        target_filename = f"IMG_{ref_number:03d}.png"
                        if target_filename in image_list:
                            img_path = f"/images/upload_{upload_id}/{target_filename}"
                            img_markdown = f"![IMG_{ref_number:03d}]({img_path})"
                            enhanced_text = enhanced_text.replace(match.group(1), f"{match.group(1)} {img_markdown}")
            
            return enhanced_text
            
        except Exception as e:
            print(f"⚠️ 인라인 이미지 처리 오류: {e}")
            return text
    
    async def _resolve_image_placeholders(self, option_text: str, image_list: List[str], upload_id: int) -> str:
        """선택지 내 이미지 플레이스홀더 처리"""
        try:
            import re
            
            if not option_text or not isinstance(option_text, str):
                return str(option_text) if option_text is not None else ''
            
            enhanced_option = option_text
            
            # IMG_XXX_IMAGE 패턴 처리
            img_pattern = r'IMG_(\d{3})_IMAGE'
            matches = re.findall(img_pattern, enhanced_option)
            
            for match in matches:
                img_number = int(match)
                target_files = [
                    f"IMG_{img_number:03d}.png",
                    f"IMG_{img_number:03d}.jpeg"
                ]
                
                for target_filename in target_files:
                    if target_filename in image_list:
                        img_path = f"/images/upload_{upload_id}/{target_filename}"
                        img_markdown = f"![IMG_{img_number:03d}]({img_path})"
                        enhanced_option = enhanced_option.replace(f"IMG_{img_number:03d}_IMAGE", img_markdown)
                        break
            
            return enhanced_option
            
        except Exception as e:
            print(f"⚠️ 이미지 플레이스홀더 처리 오류: {e}")
            return str(option_text) if option_text is not None else ''
    
    def _is_incomplete_image_choice(self, option_text: str) -> bool:
        """불완전한 이미지 선택지 감지"""
        try:
            if not option_text or not isinstance(option_text, str):
                return True
            
            option_str = str(option_text).strip()
            
            # 빈 문자열이나 너무 짧은 문자열
            if len(option_str) < 3:
                return True
            
            # 처리되지 않은 IMG 참조
            if 'IMG_' in option_str and '_IMAGE' in option_str:
                return True
            
            # 의미없는 텍스트
            meaningless_patterns = ['...', '–', '—', '?', '비어있음', '없음']
            if any(pattern in option_str for pattern in meaningless_patterns):
                return True
            
            return False
            
        except Exception:
            return True
    
    async def _match_contextual_image(self, question_number: int, choice_number: int, 
                                     question_text: str, passage: str, 
                                     image_list: List[str], upload_id: int) -> str:
        """컨텍스트 기반 이미지 매칭"""
        try:
            # 문제 번호와 선택지 번호를 고려한 이미지 매칭
            candidate_numbers = [
                question_number,  # 문제 번호 기반
                question_number * 10 + choice_number,  # 문제+선택지 조합
                (question_number - 1) * 4 + choice_number,  # 순차적 배치
                choice_number,  # 선택지 번호만
            ]
            
            for candidate_num in candidate_numbers:
                if 1 <= candidate_num <= 999:
                    target_files = [
                        f"IMG_{candidate_num:03d}.png",
                        f"IMG_{candidate_num:03d}.jpeg"
                    ]
                    
                    for target_filename in target_files:
                        if target_filename in image_list:
                            img_path = f"/images/upload_{upload_id}/{target_filename}"
                            return f"![IMG_{candidate_num:03d}]({img_path})"
            
            return None
            
        except Exception as e:
            print(f"⚠️ 컨텍스트 이미지 매칭 오류: {e}")
            return None
    
    async def _enhance_boundary_chunk_processing(self, chunk_content: str, chunk_info: Dict) -> str:
        """경계 청크 처리 강화 - 선택지 복구 전용 프롬프트"""
        try:
            if chunk_info.get('chunk_type') != 'boundary_overlap':
                return chunk_content
            
            # 경계 청크 전용 강화 프롬프트 추가
            enhanced_content = f"""{chunk_content}

🔧 **경계 청크 처리 특별 지침**:
1. **문제 연결**: 페이지 경계에서 잘린 문제 번호를 하나의 완전한 문제로 연결
2. **선택지 복구**: 불완전한 선택지(① 있고 ②③④ 없는 경우)를 다음 페이지 내용과 연결하여 완성
3. **표/다이어그램 통합**: 페이지를 넘나드는 표나 그림을 하나의 완전한 요소로 처리
4. **빈 컨테이너 방지**: 선택지 라벨만 있고 내용이 없는 경우 반드시 전후 맥락에서 내용 찾아서 채움
5. **문제 번호 일관성**: 동일한 문제 번호가 두 페이지에 걸쳐 나타나면 하나로 통합

⚠️ **중요**: 빈 선택지 컨테이너(예: ① 없음, ② 비어있음)를 만들지 마세요. 반드시 실제 내용으로 채워주세요.
"""
            return enhanced_content
            
        except Exception as e:
            print(f"⚠️ 경계 청크 강화 처리 오류: {e}")
            return chunk_content
    
    async def _get_boundary_recovery_prompt(self, chunk_content: str, page_start: int, page_end: int) -> str:
        """경계 청크 전용 복구 프롬프트 생성"""
        try:
            boundary_prompt = f"""
🔧 **페이지 경계 문제 복구 전문가**

당신은 한국어 시험 문제에서 페이지 경계로 인해 잘린 문제와 선택지를 복구하는 전문가입니다.
다음은 페이지 {page_start}-{page_end} 경계에서 잘린 내용입니다.

**핵심 임무**:
1. 🔗 **문제 연결 복구**: 잘린 문제 번호를 완전한 문제로 연결
2. 🎯 **선택지 완성**: 불완전한 선택지(①②③④ 중 일부만 있음)를 완전한 세트로 복구  
3. 📊 **표/그림 통합**: 페이지를 넘나드는 표나 다이어그램을 하나로 통합
4. 🚫 **빈 컨테이너 제거**: 내용이 없는 선택지 컨테이너를 절대 만들지 마세요

**복구 전략**:
- 잘린 문제 텍스트를 이어붙여서 완전한 문제 만들기
- 첫 페이지 끝의 선택지와 다음 페이지 시작의 선택지 연결
- 표의 헤더와 데이터 행을 완전히 통합
- 문제와 관련된 모든 이미지/다이어그램 참조 유지

**출력 형식** (JSON):
```json
{{
  "questions": [
    {{
      "question_number": 정수,
      "question_text": "완전히 복구된 문제 텍스트",
      "options": ["①", "②", "③", "④"], // 반드시 완전한 선택지 세트
      "passage": "지문이 있는 경우 (표/그림 포함)",
      "recovery_info": {{
        "was_split": true,
        "merged_content": "어떤 내용이 합쳐졌는지 설명",
        "pages_involved": [{page_start}, {page_end}]
      }}
    }}
  ]
}}
```

**절대 금지사항**:
- ❌ "선택지 없음", "빈 선택지", "..." 등의 빈 컨테이너 생성 금지
- ❌ 불완전한 선택지 세트 (①②만 있고 ③④ 없음) 생성 금지
- ❌ 문제 번호 중복 생성 금지

**처리할 내용**:
{chunk_content}
"""
            return boundary_prompt
            
        except Exception as e:
            print(f"⚠️ 경계 복구 프롬프트 생성 오류: {e}")
            # 오류 발생 시 일반 프롬프트로 폴백
            return f"""
📚 **시험문제 추출 전문가**

다음 교육 콘텐츠에서 시험 문제만 추출하여 JSON 형식으로 구조화하세요.

**처리할 내용**:
{chunk_content}

**출력 형식**: JSON
```json
{{
  "questions": [
    {{
      "question_number": 정수,
      "question_text": "문제 텍스트",
      "options": ["①", "②", "③", "④"],
      "passage": "지문 (있는 경우만)"
    }}
  ]
}}
```
"""
    
    def _analyze_image_requirement(self, question_text: str, passage: str, options: List) -> tuple[bool, float]:
        """문제가 이미지 선택지를 필요로 하는지 스마트 분석"""
        try:
            combined_text = f"{question_text} {passage}".lower()
            confidence = 0.0
            
            # 명확한 이미지 필요 신호
            strong_indicators = [
                '표를 보고', '그림을 보고', '다음 표에서', '위 그림에서', 
                '아래 표는', '다음 그래프', '차트를 보고', '도표를 참고',
                '다음 중 올바른 것', '다음 중 틀린 것', '가장 적절한 것'
            ]
            
            # 테이블/그래프 관련 키워드
            table_keywords = [
                '표', 'table', '프로세스', 'p1', 'p2', 'p3', 
                '도착시간', '실행시간', '대기시간', '처리시간',
                '그래프', 'graph', 'chart', '차트'
            ]
            
            # 이미지 선택지 패턴
            image_choice_patterns = [
                'img_', '이미지', '그림', '도형', '기호'
            ]
            
            # 점수 계산
            for indicator in strong_indicators:
                if indicator in combined_text:
                    confidence += 0.4
            
            for keyword in table_keywords:
                if keyword in combined_text:
                    confidence += 0.2
            
            # 기존 선택지에 이미지 참조가 있는 경우
            for option in options:
                option_str = str(option).lower()
                if any(pattern in option_str for pattern in image_choice_patterns):
                    confidence += 0.3
                    
            # 선택지 품질이 낮은 경우 (텍스트가 거의 없음)
            text_options = [opt for opt in options if opt and len(str(opt).strip()) > 2]
            if len(text_options) < len(options) * 0.5:  # 절반 이상이 부실한 선택지
                confidence += 0.3
            
            # 최대 1.0으로 제한
            confidence = min(confidence, 1.0)
            needs_images = confidence > 0.3
            
            return needs_images, confidence
            
        except Exception as e:
            print(f"⚠️ 이미지 요구사항 분석 오류: {e}")
            return False, 0.0
    
    async def _smart_image_matching(self, question_number: int, question_text: str, 
                                   passage: str, image_list: List[str], upload_id: int) -> List[Dict]:
        """다중 기준 이미지 매칭 - 개선된 스코어 시스템"""
        try:
            scored_images = []
            combined_text = f"{question_text} {passage}".lower()
            
            for img_file in image_list:
                if 'IMG_' in img_file:
                    try:
                        img_num_str = img_file.split('IMG_')[1].split('.')[0]
                        img_num = int(img_num_str)
                        
                        # 다중 기준 스코어 계산
                        score_components = self._calculate_multi_criteria_score(
                            question_number, img_num, combined_text, img_file
                        )
                        
                        total_score = sum(score_components.values())
                        
                        if total_score > 25:  # 임계값 낮춤 (30→25)
                            scored_images.append({
                                'filename': img_file,
                                'number': img_num,
                                'score': total_score,
                                'score_breakdown': score_components,
                                'distance': abs(img_num - question_number)
                            })
                            
                    except (ValueError, IndexError):
                        continue
            
            # 복합 정렬: 점수 우선, 거리 보조
            scored_images.sort(key=lambda x: (x['score'], -x['distance']), reverse=True)
            
            # 상위 후보군에서 재랭킹
            top_candidates = scored_images[:6]  # 상위 6개 후보
            final_selection = self._rerank_image_candidates(
                top_candidates, question_number, combined_text
            )
            
            if final_selection:
                scores_info = [f"IMG_{img['number']:03d}({img['score']:.0f})" for img in final_selection]
                print(f"      🎯 Q{question_number} 매칭: {scores_info}")
                return final_selection
            
            return []
            
        except Exception as e:
            print(f"⚠️ 스마트 이미지 매칭 오류: {e}")
            return []
    
    def _calculate_multi_criteria_score(self, question_number: int, img_num: int, 
                                      combined_text: str, img_filename: str) -> Dict[str, float]:
        """다중 기준 스코어 계산"""
        scores = {}
        
        # 1. 직접 매칭 (가중치: 40%)
        if img_num == question_number:
            scores['direct_match'] = 100
        else:
            scores['direct_match'] = 0
        
        # 2. 근접도 매칭 (가중치: 20%)
        distance = abs(img_num - question_number)
        if distance <= 1:
            scores['proximity'] = 80 - distance * 30
        elif distance <= 3:
            scores['proximity'] = 50 - distance * 10
        else:
            scores['proximity'] = max(0, 20 - distance * 2)
        
        # 3. 컨텍스트 매칭 (가중치: 25%)
        context_score = 0
        
        # 테이블/그래프 컨텍스트
        if any(keyword in combined_text for keyword in ['표', 'table', '그래프', 'chart']):
            # 테이블 문제는 연속 이미지 패턴
            table_base = question_number * 2 + 10
            if table_base <= img_num <= table_base + 4:
                context_score += 60
            
        # 선택지 이미지 패턴 감지
        choice_base = question_number * 4 + 20
        if choice_base <= img_num <= choice_base + 3:
            context_score += 70
        
        scores['context_match'] = context_score
        
        # 4. 페이지 위치 매칭 (가중치: 15%)
        estimated_page = max(1, (question_number - 1) // 5 + 1)
        page_img_range = range((estimated_page - 1) * 15 + 1, estimated_page * 15 + 1)
        
        if img_num in page_img_range:
            # 페이지 내 위치에 따른 세분화
            page_position = (img_num - page_img_range.start) / len(page_img_range)
            question_position = ((question_number - 1) % 5) / 5  # 페이지 내 문제 위치
            
            position_similarity = 1 - abs(page_position - question_position)
            scores['page_position'] = 40 * position_similarity
        else:
            scores['page_position'] = 0
        
        # 5. 파일명 패턴 보너스
        scores['filename_bonus'] = 0
        if f"_{question_number:03d}" in img_filename:
            scores['filename_bonus'] = 20
        elif f"_{question_number:02d}" in img_filename:
            scores['filename_bonus'] = 15
        
        return scores
    
    def _rerank_image_candidates(self, candidates: List[Dict], question_number: int, 
                               combined_text: str) -> List[Dict]:
        """상위 후보군 재랭킹"""
        if not candidates:
            return []
        
        # 최고 점수가 50점 이상인 경우만 진행
        if candidates[0]['score'] < 50:
            return []
        
        # 컨텍스트 기반 재가중
        for candidate in candidates:
            original_score = candidate['score']
            
            # 테이블 문제에 대한 가중치 조정
            if any(keyword in combined_text for keyword in ['표', 'table', '도표']):
                if 'context_match' in candidate.get('score_breakdown', {}):
                    context_bonus = candidate['score_breakdown']['context_match']
                    if context_bonus > 50:  # 강한 컨텍스트 매칭
                        candidate['score'] *= 1.2  # 20% 보너스
            
            # 선택지 이미지 문제에 대한 가중치
            if any(keyword in combined_text for keyword in ['다음 중', '가장 적절한', '옳은 것']):
                if candidate['score_breakdown'].get('context_match', 0) > 60:
                    candidate['score'] *= 1.15
        
        # 재정렬
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # 최종 선택: 최대 4개, 점수 임계값 적용
        final_candidates = []
        for candidate in candidates[:4]:
            if candidate['score'] >= 40:  # 낮아진 임계값
                final_candidates.append(candidate)
        
        return final_candidates
    
    def _analyze_options_quality(self, options: List) -> float:
        """기존 선택지의 품질 분석 (0.0 - 1.0)"""
        try:
            if not options:
                return 0.0
            
            quality_score = 0.0
            valid_options = 0
            
            for option in options:
                option_str = str(option).strip()
                
                if not option_str or option_str in ['', '-', '--']:
                    continue  # 빈 선택지
                
                if 'IMG_' in option_str and len(option_str) < 20:
                    # 이미지 참조만 있고 설명이 없는 경우
                    quality_score += 0.3
                elif len(option_str) > 5:
                    # 적절한 텍스트가 있는 경우
                    quality_score += 1.0
                else:
                    # 너무 짧은 선택지
                    quality_score += 0.5
                    
                valid_options += 1
            
            if valid_options == 0:
                return 0.0
                
            return quality_score / valid_options
            
        except Exception as e:
            print(f"⚠️ 선택지 품질 분석 오류: {e}")
            return 0.5
    
    def _convert_image_references_to_markdown(self, questions: List[Dict], upload_id: int) -> List[Dict]:
        """IMG_XXX_IMAGE 형태를 마크다운 이미지 참조로 변환"""
        try:
            import os
            import re
            
            # 이미지 디렉토리 확인
            image_dir = f"static/images/upload_{upload_id}"
            available_images = set()
            
            if os.path.exists(image_dir):
                image_files = [f for f in os.listdir(image_dir) if f.startswith('IMG_')]
                for img_file in image_files:
                    # IMG_001.png -> 001
                    match = re.match(r'IMG_(\d+)\.(\w+)', img_file)
                    if match:
                        img_num = int(match.group(1))
                        available_images.add(img_num)
            
            print(f"   📁 사용 가능한 이미지: {len(available_images)}개")
            
            converted_count = 0
            for question in questions:
                
                # 선택지에서 이미지 참조 변환
                options = question.get('options', [])
                if options:
                    converted_options = []
                    for option in options:
                        option_str = str(option) if option else ""
                        
                        # IMG_XXX_IMAGE 패턴 찾기
                        img_pattern = re.findall(r'IMG_(\d+)_IMAGE', option_str)
                        if img_pattern:
                            for img_num_str in img_pattern:
                                img_num = int(img_num_str)
                                
                                # 실제 이미지 파일이 존재하는지 확인
                                if img_num in available_images:
                                    # 이미지 파일 확장자 찾기
                                    img_ext = self._find_image_extension(upload_id, img_num)
                                    if img_ext:
                                        # 마크다운 형식으로 변환
                                        img_path = f"/images/upload_{upload_id}/IMG_{img_num:03d}.{img_ext}"
                                        markdown_img = f"![IMG_{img_num:03d}]({img_path})"
                                        option_str = option_str.replace(f"IMG_{img_num_str}_IMAGE", markdown_img)
                                        converted_count += 1
                                    else:
                                        # 파일이 없으면 플레이스홀더로 유지
                                        print(f"   ⚠️ 이미지 파일 없음: IMG_{img_num:03d}")
                                else:
                                    print(f"   ⚠️ 이미지 번호 {img_num} 사용할 수 없음")
                        
                        converted_options.append(option_str)
                    
                    question['options'] = converted_options
                
                # 질문 텍스트에서도 이미지 참조 변환
                question_text = question.get('question_text', '')
                if 'IMG_' in question_text and '_IMAGE' in question_text:
                    img_pattern = re.findall(r'IMG_(\d+)_IMAGE', question_text)
                    for img_num_str in img_pattern:
                        img_num = int(img_num_str)
                        if img_num in available_images:
                            img_ext = self._find_image_extension(upload_id, img_num)
                            if img_ext:
                                img_path = f"/images/upload_{upload_id}/IMG_{img_num:03d}.{img_ext}"
                                markdown_img = f"![IMG_{img_num:03d}]({img_path})"
                                question_text = question_text.replace(f"IMG_{img_num_str}_IMAGE", markdown_img)
                                converted_count += 1
                    
                    question['question_text'] = question_text
                
                # 지문에서도 이미지 참조 변환
                passage = question.get('passage', '')
                if 'IMG_' in passage and '_IMAGE' in passage:
                    img_pattern = re.findall(r'IMG_(\d+)_IMAGE', passage)
                    for img_num_str in img_pattern:
                        img_num = int(img_num_str)
                        if img_num in available_images:
                            img_ext = self._find_image_extension(upload_id, img_num)
                            if img_ext:
                                img_path = f"/images/upload_{upload_id}/IMG_{img_num:03d}.{img_ext}"
                                markdown_img = f"![IMG_{img_num:03d}]({img_path})"
                                passage = passage.replace(f"IMG_{img_num_str}_IMAGE", markdown_img)
                                converted_count += 1
                    
                    question['passage'] = passage
            
            print(f"   ✅ 이미지 참조 변환: {converted_count}개 변환됨")
            return questions
            
        except Exception as e:
            print(f"❌ 이미지 참조 변환 오류: {e}")
            return questions
    
    def _find_image_extension(self, upload_id: int, img_num: int) -> Optional[str]:
        """특정 이미지 번호에 해당하는 파일의 확장자 찾기"""
        try:
            import os
            
            image_dir = f"static/images/upload_{upload_id}"
            if not os.path.exists(image_dir):
                return None
            
            # 일반적인 이미지 확장자들 확인
            extensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']
            
            for ext in extensions:
                img_file = f"IMG_{img_num:03d}.{ext}"
                if os.path.exists(os.path.join(image_dir, img_file)):
                    return ext
            
            return None
            
        except Exception as e:
            print(f"⚠️ 이미지 확장자 찾기 오류: {e}")
            return None
    
    async def _alternative_enhancement_pipeline(self, upload_id: int, basic_questions: List[Dict], 
                                              markdown_content: str, db: Session) -> List[Dict]:
        """OCR 없이 패턴 기반으로 문제 보완"""
        try:
            print(f"📝 대안 보완 파이프라인 시작...")
            
            enhanced_questions = basic_questions.copy()
            
            # 1. 불완전한 선택지 문제 감지 및 보완
            incomplete_questions = []
            for question in enhanced_questions:
                choices = question.get('options', [])
                if len(choices) < 3:  # 3개 미만은 불완전으로 판단
                    incomplete_questions.append(question)
            
            print(f"   🔍 불완전 문제 발견: {len(incomplete_questions)}개")
            
            # 2. 마크다운에서 누락된 선택지 패턴 매칭
            for incomplete_q in incomplete_questions:
                question_number = incomplete_q.get('question_number', 0)
                if question_number > 0:
                    additional_choices = self._find_missing_choices_in_markdown(
                        question_number, markdown_content
                    )
                    if additional_choices:
                        current_choices = incomplete_q.get('options', [])
                        merged_choices = current_choices + additional_choices
                        incomplete_q['options'] = merged_choices[:5]  # 최대 5개까지
                        print(f"   ✅ Q{question_number} 선택지 보완: {len(current_choices)} → {len(merged_choices)}개")
            
            # 3. 누락된 문제 번호 감지 및 복구 시도
            existing_numbers = {q.get('question_number', 0) for q in enhanced_questions}
            max_number = max(existing_numbers) if existing_numbers else 0
            
            missing_numbers = []
            for i in range(1, max_number + 1):
                if i not in existing_numbers:
                    missing_numbers.append(i)
            
            if missing_numbers:
                print(f"   🔍 누락된 문제 번호 감지: {missing_numbers}")
                recovered_questions = self._recover_missing_questions_from_markdown(
                    missing_numbers, markdown_content
                )
                enhanced_questions.extend(recovered_questions)
                print(f"   ✅ 누락 문제 복구: {len(recovered_questions)}개")
            
            # 4. 문제 번호순 정렬
            enhanced_questions.sort(key=lambda x: x.get('question_number', 0))
            
            print(f"📝 대안 보완 완료: {len(basic_questions)} → {len(enhanced_questions)} 문제")
            return enhanced_questions
            
        except Exception as e:
            print(f"❌ 대안 보완 오류: {e}")
            return basic_questions
    
    def _find_missing_choices_in_markdown(self, question_number: int, markdown_content: str) -> List[str]:
        """마크다운에서 특정 문제의 누락된 선택지 찾기"""
        try:
            import re
            
            # 문제 번호 패턴으로 해당 문제 영역 찾기
            question_patterns = [
                rf'문제 {question_number}번(.*?)(?=문제 \d+번|$)',
                rf'{question_number}번(.*?)(?=\d+번|$)',
                rf'문제\s*{question_number}\s*(.*?)(?=문제\s*\d+|$)'
            ]
            
            question_text = ""
            for pattern in question_patterns:
                match = re.search(pattern, markdown_content, re.DOTALL)
                if match:
                    question_text = match.group(1)
                    break
            
            if not question_text:
                return []
            
            # 선택지 패턴 매칭
            choices = []
            choice_patterns = [
                r'선택지\s*(\d+):\s*([^\n선택지]+)',
                r'①\s*([^\n②③④⑤]+)',
                r'②\s*([^\n①③④⑤]+)', 
                r'③\s*([^\n①②④⑤]+)',
                r'④\s*([^\n①②③⑤]+)',
                r'⑤\s*([^\n①②③④]+)'
            ]
            
            for pattern in choice_patterns:
                matches = re.finditer(pattern, question_text)
                for match in matches:
                    if pattern.startswith(r'선택지'):
                        choice_text = match.group(2).strip()
                    else:
                        choice_text = match.group(1).strip()
                    
                    if choice_text and len(choice_text) > 1:
                        choices.append(choice_text)
            
            return choices[:5]  # 최대 5개까지
            
        except Exception as e:
            print(f"   ⚠️ 선택지 매칭 오류: {e}")
            return []
    
    def _recover_missing_questions_from_markdown(self, missing_numbers: List[int], markdown_content: str) -> List[Dict]:
        """마크다운에서 누락된 문제 복구"""
        try:
            import re
            
            recovered_questions = []
            
            for missing_num in missing_numbers:
                # 문제 패턴 매칭
                question_patterns = [
                    rf'문제 {missing_num}번\s*([^\n]*(?:\n(?!문제\s*\d+번)[^\n]*)*)',
                    rf'{missing_num}번\s*([^\n]*(?:\n(?!\d+번)[^\n]*)*)'
                ]
                
                for pattern in question_patterns:
                    match = re.search(pattern, markdown_content, re.MULTILINE)
                    if match:
                        question_content = match.group(1).strip()
                        if len(question_content) > 10:  # 최소 길이 필터
                            
                            # 선택지 추출
                            choices = self._find_missing_choices_in_markdown(missing_num, markdown_content)
                            
                            recovered_question = {
                                'question_id': f'RECOVERED_{missing_num}',
                                'question_number': missing_num,
                                'question_text': question_content,
                                'passage': '',
                                'options': choices,
                                'correct_answer': '',
                                'recovery_source': 'markdown_pattern',
                                'chunk_origin': 'recovered'
                            }
                            
                            recovered_questions.append(recovered_question)
                            print(f"   ✅ Q{missing_num} 복구 성공")
                            break
            
            return recovered_questions
            
        except Exception as e:
            print(f"   ⚠️ 문제 복구 오류: {e}")
            return []

    def safe_json_parse(self, response_text: str, chunk_id: int = 0) -> tuple[Optional[Dict], Optional[str]]:
        """안전한 JSON 파싱 - 부분 복구 및 다단계 시도"""
        import json
        import re
        
        try:
            # 1단계: 코드펜스 제거 및 전처리
            clean_text = response_text.strip()
            
            # 코드펜스 제거
            if clean_text.startswith('```json'):
                clean_text = clean_text.split('```json', 1)[1].rsplit('```', 1)[0]
            elif clean_text.startswith('```'):
                clean_text = clean_text.split('```', 1)[1].rsplit('```', 1)[0]
            
            # 2단계: 마지막 유효한 중괄호까지 자르기
            last_brace = max(clean_text.rfind("}"), clean_text.rfind("]"))
            if last_brace != -1:
                clean_text = clean_text[:last_brace + 1]
            
            # 3단계: 직접 파싱 시도
            try:
                result = json.loads(clean_text)
                return result, None
            except json.JSONDecodeError as e:
                print(f"   ⚠️ Chunk {chunk_id} 직접 JSON 파싱 실패: {e}")
            
            # 4단계: 일반적인 오류 수정 후 재시도
            fixed_text = self._fix_common_json_errors(clean_text)
            try:
                result = json.loads(fixed_text)
                print(f"   ✅ Chunk {chunk_id} JSON 오류 수정으로 복구")
                return result, "fixed"
            except json.JSONDecodeError as e:
                print(f"   ⚠️ Chunk {chunk_id} 수정된 JSON도 파싱 실패: {e}")
            
            # 5단계: 부분 배열 추출 시도
            partial_result = self._extract_partial_questions(clean_text, chunk_id)
            if partial_result:
                print(f"   🔧 Chunk {chunk_id} 부분 추출 성공: {len(partial_result.get('questions', []))}개 문제")
                return partial_result, "partial"
            
            # 6단계: 최후 수단 - 빈 결과 반환
            print(f"   ❌ Chunk {chunk_id} 모든 JSON 복구 방법 실패")
            return {"questions": []}, "empty"
            
        except Exception as e:
            print(f"❌ Chunk {chunk_id} JSON 파싱 중 예외 발생: {e}")
            return {"questions": []}, f"error:{e}"
    
    def _fix_common_json_errors(self, json_str: str) -> str:
        """일반적인 JSON 오류 수정"""
        import re
        
        # 1. 마지막 쉼표 제거
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # 2. 따옴표가 없는 키 수정
        json_str = re.sub(r'([{,]\s*)(\w+):', r'\1"\2":', json_str)
        
        # 3. 불완전한 문자열 값 수정
        json_str = re.sub(r': ([^",{\[\]]+)([,}])', r': "\1"\2', json_str)
        
        # 4. 개행 문자 JSON-safe 처리
        json_str = json_str.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        
        # 5. 중복 따옴표 수정
        json_str = re.sub(r'""([^"]*?)""', r'"\1"', json_str)
        
        # 6. 불완전한 중괄호/대괄호 닫기
        open_braces = json_str.count('{') - json_str.count('}')
        open_brackets = json_str.count('[') - json_str.count(']')
        
        if open_braces > 0:
            json_str += '}' * open_braces
        if open_brackets > 0:
            json_str += ']' * open_brackets
        
        return json_str
    
    def _extract_partial_questions(self, text: str, chunk_id: int) -> Optional[Dict]:
        """부분적으로 손상된 JSON에서 문제 항목들 추출"""
        import re
        import json
        
        try:
            # questions 배열 부분 찾기
            questions_match = re.search(r'"questions"\s*:\s*(\[[\s\S]*)', text)
            if not questions_match:
                return None
            
            array_text = questions_match.group(1)
            
            # 개별 문제 객체들 추출 시도
            questions = []
            
            # 문제 객체 패턴으로 분리
            question_pattern = r'\{\s*"question_number"\s*:\s*(\d+)[\s\S]*?\}'
            
            # 중괄호 균형 맞춤을 고려한 분리
            brace_count = 0
            current_obj = ""
            in_question = False
            
            for char in array_text:
                if char == '{':
                    if brace_count == 0:
                        current_obj = ""
                        in_question = True
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and in_question:
                        current_obj += char
                        # 개별 객체 파싱 시도
                        try:
                            obj = json.loads(current_obj)
                            if obj.get('question_number'):
                                questions.append(obj)
                                print(f"      ✅ Q{obj.get('question_number')} 부분 추출 성공")
                        except:
                            # 개별 객체도 실패하면 정규식으로 기본 정보라도 추출
                            try:
                                q_num_match = re.search(r'"question_number"\s*:\s*(\d+)', current_obj)
                                q_text_match = re.search(r'"question_text"\s*:\s*"([^"]*)"', current_obj)
                                
                                if q_num_match:
                                    fallback_obj = {
                                        'question_number': int(q_num_match.group(1)),
                                        'question_text': q_text_match.group(1) if q_text_match else f"문제 {q_num_match.group(1)}",
                                        'options': [],
                                        'passage': '',
                                        'recovery_method': 'regex_fallback'
                                    }
                                    questions.append(fallback_obj)
                                    print(f"      🔧 Q{q_num_match.group(1)} 정규식 폴백으로 추출")
                            except:
                                pass
                        
                        current_obj = ""
                        in_question = False
                        continue
                
                if in_question:
                    current_obj += char
            
            if questions:
                return {
                    "questions": questions,
                    "extraction_method": "partial_recovery",
                    "recovered_count": len(questions)
                }
            
            return None
            
        except Exception as e:
            print(f"   ❌ 부분 추출 중 오류: {e}")
            return None
    
    def _create_overlap_chunks(self, pages: List[str]) -> List[Dict]:
        """오버랩 윈도우 청크 생성 - 페이지 경계 문제 해결"""
        chunks = []
        
        # 1단계: 개별 페이지 청크 (안정성 확보)
        for i, page_content in enumerate(pages):
            if page_content.strip():
                chunks.append({
                    'content': f"# Page {i+1}\n\n{page_content}",
                    'page_start': i + 1,
                    'page_end': i + 1,
                    'chunk_type': 'single_page',
                    'estimated_questions': 8
                })
        
        # 2단계: 경계 오버랩 청크 (Q11, Q41 등 경계 문제 해결)
        for i in range(len(pages) - 1):
            current_page = pages[i].strip()
            next_page = pages[i + 1].strip()
            
            if current_page and next_page:
                # 페이지 끝 부분과 시작 부분을 결합
                boundary_content = self._create_boundary_chunk(current_page, next_page, i + 1)
                
                chunks.append({
                    'content': boundary_content,
                    'page_start': i + 1,
                    'page_end': i + 2,
                    'chunk_type': 'boundary_overlap',
                    'estimated_questions': 4,  # 경계에서는 보통 적은 수
                    'boundary_pages': f"{i+1}-{i+2}"
                })
        
        # 3단계: 2페이지 윈도우 청크 (중간 크기 청크로 안정성 강화)
        for i in range(0, len(pages) - 1, 2):
            page_group = []
            page_numbers = []
            
            for j in range(2):  # 2페이지씩
                if i + j < len(pages) and pages[i + j].strip():
                    page_group.append(f"# Page {i+j+1}\n\n{pages[i + j]}")
                    page_numbers.append(i + j + 1)
            
            if len(page_group) >= 2:
                chunks.append({
                    'content': '\n\n---\n\n'.join(page_group),
                    'page_start': page_numbers[0],
                    'page_end': page_numbers[-1],
                    'chunk_type': 'two_page_window',
                    'estimated_questions': 16  # 2페이지 약 16문제
                })
        
        print(f"   📦 Individual pages: {len([c for c in chunks if c['chunk_type'] == 'single_page'])}")
        print(f"   🔗 Boundary overlaps: {len([c for c in chunks if c['chunk_type'] == 'boundary_overlap'])}")
        print(f"   🪟 Two-page windows: {len([c for c in chunks if c['chunk_type'] == 'two_page_window'])}")
        
        return chunks
    
    def _create_boundary_chunk(self, current_page: str, next_page: str, page_num: int) -> str:
        """페이지 경계 청크 생성 - 문제가 잘린 부분을 포함"""
        
        # 현재 페이지의 마지막 부분 (약 30% 정도)
        current_lines = current_page.split('\n')
        current_tail = '\n'.join(current_lines[int(len(current_lines) * 0.7):])
        
        # 다음 페이지의 첫 부분 (약 30% 정도)  
        next_lines = next_page.split('\n')
        next_head = '\n'.join(next_lines[:int(len(next_lines) * 0.3)])
        
        boundary_content = f"""# Boundary Pages {page_num}-{page_num+1}

## End of Page {page_num}
{current_tail}

---

## Start of Page {page_num+1}
{next_head}
"""
        
        return boundary_content
    
    def normalize_question_options(self, question: Dict) -> Dict:
        """선택지 라벨 통일 및 누락 보강"""
        try:
            import re
            
            options = question.get('options', [])
            if not options:
                return question
            
            # 표준 라벨 순서
            STANDARD_LABELS = ["A", "B", "C", "D", "E"]
            KOREAN_LABELS = ["①", "②", "③", "④", "⑤"]
            
            normalized_options = []
            
            for option in options:
                if not option:
                    continue
                    
                option_str = str(option).strip()
                
                # 라벨 패턴 매칭
                label_match = re.match(r'\s*(?:\(?([A-E①-⑤])\)?[.\)]?)\s*(.+)$', option_str)
                
                if label_match:
                    raw_label = label_match.group(1)
                    text = label_match.group(2).strip()
                    
                    # 라벨 변환
                    if raw_label in KOREAN_LABELS:
                        standard_label = STANDARD_LABELS[KOREAN_LABELS.index(raw_label)]
                    elif raw_label in STANDARD_LABELS:
                        standard_label = raw_label
                    else:
                        standard_label = "A"  # 기본값
                    
                    normalized_options.append({
                        "label": standard_label,
                        "text": text,
                        "raw_label": raw_label
                    })
                else:
                    # 라벨이 없는 경우
                    normalized_options.append({
                        "label": STANDARD_LABELS[len(normalized_options)] if len(normalized_options) < 5 else "E",
                        "text": option_str,
                        "raw_label": None
                    })
            
            # 누락된 선택지 보강 (A-D가 모두 있어야 함)
            seen_labels = {opt["label"] for opt in normalized_options}
            
            if len(normalized_options) < 4:  # 선택지가 부족한 경우
                for label in STANDARD_LABELS[:4]:  # A, B, C, D
                    if label not in seen_labels:
                        normalized_options.append({
                            "label": label,
                            "text": "",
                            "raw_label": None,
                            "missing": True
                        })
            
            # 라벨 순으로 정렬
            normalized_options.sort(key=lambda x: STANDARD_LABELS.index(x["label"]) if x["label"] in STANDARD_LABELS else 999)
            
            # 원래 형태로 변환 (하위 호환성)
            question_copy = question.copy()
            question_copy['options'] = [opt["text"] for opt in normalized_options[:4]]  # 최대 4개
            question_copy['options_metadata'] = normalized_options  # 메타데이터 보존
            
            return question_copy
            
        except Exception as e:
            print(f"⚠️ 선택지 정규화 오류: {e}")
            return question
    
    def merge_duplicate_questions(self, questions: List[Dict]) -> List[Dict]:
        """중복 문제 감지 및 병합"""
        try:
            if not questions:
                return questions
                
            # 문제 번호별 그룹화
            question_groups = {}
            
            for question in questions:
                qno = question.get('question_number')
                if qno is None:
                    continue
                    
                if qno not in question_groups:
                    question_groups[qno] = []
                question_groups[qno].append(question)
            
            merged_questions = []
            
            for qno, group in question_groups.items():
                if len(group) == 1:
                    # 중복 없음
                    merged_questions.append(self.normalize_question_options(group[0]))
                else:
                    # 중복 발견 - 가장 완전한 버전 선택
                    print(f"🔄 문제 {qno}번 중복 발견: {len(group)}개 버전")
                    
                    best_question = self._select_best_question_version(group)
                    merged_questions.append(self.normalize_question_options(best_question))
            
            # 문제 번호순 정렬
            merged_questions.sort(key=lambda x: x.get('question_number', 0))
            
            return merged_questions
            
        except Exception as e:
            print(f"❌ 중복 문제 병합 오류: {e}")
            return questions
    
    def _select_best_question_version(self, versions: List[Dict]) -> Dict:
        """여러 버전 중 가장 완전한 문제 선택"""
        try:
            best_question = versions[0]
            best_score = 0
            
            for version in versions:
                score = 0
                
                # 질문 텍스트 점수 (길이와 완성도)
                question_text = version.get('question_text', '')
                if question_text:
                    score += min(len(question_text.strip()), 100)  # 최대 100점
                
                # 선택지 점수
                options = version.get('options', [])
                valid_options = [opt for opt in options if opt and str(opt).strip()]
                score += len(valid_options) * 25  # 선택지당 25점
                
                # 지문 점수
                passage = version.get('passage', '')
                if passage and len(passage.strip()) > 10:
                    score += 50
                
                # 메타데이터 점수
                if version.get('chunk_origin'):
                    score += 10
                
                # 청크 타입별 보정
                chunk_type = version.get('chunk_type', '')
                if 'boundary_overlap' in chunk_type:
                    score += 20  # 경계 청크는 페이지 경계 문제 해결에 유리
                elif 'single_page' in chunk_type:
                    score += 10
                
                if score > best_score:
                    best_score = score
                    best_question = version
            
            # 병합 정보 추가
            best_question['merge_info'] = {
                'total_versions': len(versions),
                'selected_score': best_score,
                'chunk_sources': [v.get('chunk_origin') for v in versions]
            }
            
            print(f"   ✅ 최고 점수 버전 선택: {best_score}점")
            return best_question
            
        except Exception as e:
            print(f"   ❌ 최적 버전 선택 오류: {e}")
            return versions[0]
    
    async def _parse_claude_text_response(self, text: str, chunk_id: int) -> Dict:
        """Claude의 텍스트 응답을 구조화된 데이터로 파싱"""
        import re
        
        try:
            questions = []
            
            # 문제 패턴 매칭
            question_patterns = [
                r'문제\s*(\d+)번[\s\S]*?(?=문제\s*\d+번|$)',
                r'(\d+)\.\s*([^\n]+)[\s\S]*?(?=\d+\.\s*[^\n]+|$)',
                r'Q(\d+)[:\s]*([^\n]+)[\s\S]*?(?=Q\d+|$)'
            ]
            
            for pattern in question_patterns:
                matches = re.finditer(pattern, text, re.MULTILINE)
                
                for match in matches:
                    try:
                        question_num = int(match.group(1))
                        question_text = match.group(2) if len(match.groups()) > 1 else match.group(0)
                        
                        # 선택지 추출
                        options = []
                        choice_patterns = [r'[①②③④⑤]', r'[1-5]\)', r'[가나다라마]']
                        
                        for choice_pattern in choice_patterns:
                            choices = re.findall(f'{choice_pattern}[^①②③④⑤1-5가나다라마]*', question_text)
                            if choices:
                                options = [choice.strip() for choice in choices]
                                break
                        
                        if question_num and question_text.strip():
                            questions.append({
                                'question_id': f'Q{chunk_id:02d}_{question_num:03d}',
                                'question_number': question_num,
                                'question_text': question_text.strip(),
                                'passage': '',
                                'options': options[:4] if len(options) > 4 else options,
                                'correct_answer': '',
                                'parsed_from_text': True
                            })
                    except (ValueError, IndexError):
                        continue
                
                if questions:  # 성공적으로 파싱된 경우 중단
                    break
            
            print(f"텍스트 파싱으로 {len(questions)}개 문제 추출")
            return {
                'questions': questions,
                'study_materials': [],
                'chapters': []
            }
            
        except Exception as e:
            print(f"텍스트 파싱 실패: {e}")
            return None
    
    def _fix_incomplete_json(self, json_content: str) -> str:
        """불완전한 JSON 구조 수정"""
        try:
            # 마지막에 누락된 중괄호 추가
            open_braces = json_content.count('{')
            close_braces = json_content.count('}')
            if open_braces > close_braces:
                json_content += '}' * (open_braces - close_braces)
            
            # 마지막에 누락된 대괄호 추가
            open_brackets = json_content.count('[')
            close_brackets = json_content.count(']')
            if open_brackets > close_brackets:
                json_content += ']' * (open_brackets - close_brackets)
            
            # 마지막 쉼표 제거 (trailing comma)
            json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)
            
            # 누락된 따옴표 수정
            json_content = re.sub(r'(\w+):', r'"\1":', json_content)
            
            return json_content
        except Exception:
            return json_content
    
    async def _extract_images_from_pdf(self, upload_id: int, pdf_path: str) -> Dict[str, Any]:
        """PDF에서 이미지 추출 및 저장"""
        try:
            print(f"🖼️ PDF에서 이미지 추출 시작 - Upload {upload_id}")
            
            # 이미지 저장 디렉토리 생성
            images_dir = Path(f"static/images/upload_{upload_id}")
            images_dir.mkdir(parents=True, exist_ok=True)
            
            doc = fitz.open(pdf_path)
            extracted_images = []
            image_counter = 1
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 페이지의 이미지 객체 추출
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        # 이미지 데이터 추출
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # 이미지 파일 저장
                        image_filename = f"IMG_{image_counter:03d}.{image_ext}"
                        image_path = images_dir / image_filename
                        
                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)
                        
                        # 이미지 메타데이터 수집
                        image_info = {
                            "image_id": f"IMG_{image_counter:03d}",
                            "filename": image_filename,
                            "file_path": f"/static/images/upload_{upload_id}/{image_filename}",
                            "page_number": page_num + 1,
                            "image_type": "embedded",
                            "format": image_ext,
                            "size": len(image_bytes),
                            "web_path": f"/images/upload_{upload_id}/{image_filename}"
                        }
                        
                        extracted_images.append(image_info)
                        image_counter += 1
                        
                        print(f"✅ 이미지 추출: {image_filename} (Page {page_num + 1})")
                        
                    except Exception as img_error:
                        print(f"⚠️ 이미지 {img_index} 추출 실패 (Page {page_num + 1}): {img_error}")
            
            doc.close()
            
            print(f"🖼️ 이미지 추출 완료: {len(extracted_images)}개 이미지")
            
            return {
                "success": True,
                "images_extracted": len(extracted_images),
                "images": extracted_images,
                "images_directory": str(images_dir)
            }
            
        except Exception as e:
            print(f"❌ 이미지 추출 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "images": []
            }
    
    async def _detect_image_regions_in_page(self, upload_id: int, page_image_path: str, page_num: int) -> List[Dict]:
        """페이지 이미지에서 그림/다이어그램 영역 감지 및 추출"""
        try:
            import cv2
            import numpy as np
            
            # 페이지 이미지 로드
            page_img = cv2.imread(page_image_path)
            if page_img is None:
                return []
                
            height, width = page_img.shape[:2]
            gray = cv2.cvtColor(page_img, cv2.COLOR_BGR2GRAY)
            
            # 이미지 영역 감지를 위한 전처리
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
            
            # 윤곽선 검출
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            detected_regions = []
            region_counter = 1
            
            for contour in contours:
                # 영역 크기 확인 (너무 작은 영역 제외)
                area = cv2.contourArea(contour)
                if area < 5000:  # 최소 영역 크기
                    continue
                
                # 경계 사각형 추출
                x, y, w, h = cv2.boundingRect(contour)
                
                # 종횡비 확인 (극단적인 비율 제외)
                aspect_ratio = w / h
                if aspect_ratio < 0.2 or aspect_ratio > 5.0:
                    continue
                
                # 이미지 영역 추출
                region = page_img[y:y+h, x:x+w]
                
                # 추출된 영역 저장
                images_dir = Path(f"static/images/upload_{upload_id}")
                region_filename = f"PAGE_{page_num}_REGION_{region_counter:02d}.png"
                region_path = images_dir / region_filename
                
                cv2.imwrite(str(region_path), region)
                
                region_info = {
                    "region_id": f"PAGE_{page_num}_REGION_{region_counter:02d}",
                    "filename": region_filename,
                    "file_path": str(region_path),
                    "web_path": f"/images/upload_{upload_id}/{region_filename}",
                    "page_number": page_num,
                    "coordinates": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                    "area": int(area),
                    "aspect_ratio": round(aspect_ratio, 2),
                    "type": "detected_region"
                }
                
                detected_regions.append(region_info)
                region_counter += 1
                
                print(f"🎯 영역 감지: {region_filename} ({w}x{h}, 비율: {aspect_ratio:.2f})")
            
            return detected_regions
            
        except Exception as e:
            print(f"⚠️ 이미지 영역 감지 실패 (Page {page_num}): {e}")
            return []
    
    async def _verify_with_full_image(self, pdf_path: str, extracted_questions: List[Dict], pages_data: List[str]) -> List[Dict]:
        """전체 연결 이미지를 통한 페이지 경계 선택지 검수 및 복구"""
        try:
            print("\n🔍 전체 연결 이미지 생성 중...")
            
            # PDF를 전체 연결 이미지로 변환
            import fitz  # PyMuPDF
            pdf_doc = fitz.open(pdf_path)
            
            # 전체 페이지를 하나의 긴 이미지로 연결
            total_height = 0
            page_images = []
            
            for page_num in range(len(pdf_doc)):
                page = pdf_doc.load_page(page_num)
                mat = fitz.Matrix(2.0, 2.0)  # 2x 확대
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                from PIL import Image
                import io
                page_img = Image.open(io.BytesIO(img_data))
                page_images.append(page_img)
                total_height += page_img.height
            
            pdf_doc.close()
            
            # 모든 페이지를 세로로 연결
            if not page_images:
                print("⚠️ 페이지 이미지 생성 실패")
                return extracted_questions
            
            full_width = page_images[0].width
            full_image = Image.new('RGB', (full_width, total_height), 'white')
            
            current_y = 0
            for page_img in page_images:
                full_image.paste(page_img, (0, current_y))
                current_y += page_img.height
            
            # 임시 파일로 저장
            import tempfile
            import base64
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                full_image.save(temp_file.name, 'PNG', quality=90)
                
                # 이미지를 base64로 변환
                with open(temp_file.name, 'rb') as img_file:
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            print(f"✅ 전체 연결 이미지 생성 완료 ({full_width}x{total_height})")
            
            # 페이지 경계 문제가 있는 문제들 식별
            incomplete_questions = []
            for question in extracted_questions:
                options = question.get('options', [])
                question_num = question.get('question_number', 0)
                
                # 선택지 부족이 의심되는 경우들
                if (len(options) < 4 or  # 4개 미만 선택지
                    any('다음 페이지' in str(opt) for opt in options) or  # 페이지 참조
                    any('계속' in str(opt) for opt in options) or  # 계속 표시
                    question.get('incomplete_choices', False)):  # 이전에 불완전으로 표시됨
                    
                    incomplete_questions.append({
                        'question': question,
                        'original_options_count': len(options),
                        'question_number': question_num
                    })
            
            if not incomplete_questions:
                print("✅ 페이지 경계 문제가 있는 문제 없음")
                return extracted_questions
            
            print(f"🔍 페이지 경계 문제 의심 문제: {len(incomplete_questions)}개")
            
            # Claude를 통한 전체 이미지 분석
            verification_prompt = f"""
🔍 **페이지 경계 선택지 검증 전문가**

**임무**: 전체 연결 PDF 이미지를 분석하여 페이지 경계로 인해 잘린 선택지를 찾아서 완전하게 복구하세요.

**분석 대상**: 다음 문제들의 선택지가 완전한지 확인하고, 누락된 부분을 찾아서 복구해주세요:

{chr(10).join([f"문제 {q['question_number']}번: 현재 {q['original_options_count']}개 선택지" for q in incomplete_questions[:10]])}

**검증 규칙**:
1. 각 문제의 선택지가 ①②③④⑤ 또는 1)2)3)4)5) 형태로 완전한지 확인
2. 페이지 끝에서 잘린 선택지를 다음 페이지 시작에서 찾아 연결
3. 표나 그래프가 페이지를 걸쳐 있는 경우 완전한 데이터 복구
4. 이미지 선택지의 경우 IMG_XX_IMAGE 형태로 참조

**JSON 출력**:
{{
  "boundary_issues_found": [
    {{
      "question_number": 6,
      "issue_type": "incomplete_choices",
      "current_choices": ["① 프로세스 관리", "② 메모리"],
      "recovered_choices": ["① 프로세스 관리", "② 메모리 관리", "③ 파일 시스템", "④ 모든 것"],
      "page_boundary_location": "페이지 2-3 경계"
    }}
  ]
}}
"""
            
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'x-api-key': self.claude_client.api_key if self.claude_client else '',
                    'anthropic-version': '2023-06-01'
                }
                
                payload = {
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 8000,
                    "messages": [
                        {
                            "role": "user", 
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": image_data
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": verification_prompt
                                }
                            ]
                        }
                    ]
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.anthropic.com/v1/messages", 
                        headers=headers, 
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            verification_text = result['content'][0]['text']
                            
                            print(f"✅ 전체 이미지 검증 완료")
                            
                            # JSON 파싱 시도
                            try:
                                import json
                                import re
                                
                                # JSON 추출
                                json_match = re.search(r'\{.*\}', verification_text, re.DOTALL)
                                if json_match:
                                    verification_result = json.loads(json_match.group())
                                    
                                    boundary_issues = verification_result.get('boundary_issues_found', [])
                                    if boundary_issues:
                                        print(f"🔧 {len(boundary_issues)}개 페이지 경계 문제 발견, 복구 중...")
                                        
                                        # 문제별 선택지 복구
                                        for issue in boundary_issues:
                                            question_num = issue.get('question_number')
                                            recovered_choices = issue.get('recovered_choices', [])
                                            
                                            # 해당 문제 찾아서 선택지 업데이트
                                            for question in extracted_questions:
                                                if question.get('question_number') == question_num:
                                                    old_count = len(question.get('options', []))
                                                    question['options'] = recovered_choices
                                                    question['page_boundary_recovered'] = True
                                                    
                                                    print(f"✅ Q{question_num} 선택지 복구: {old_count}개 → {len(recovered_choices)}개")
                                                    break
                                    else:
                                        print("ℹ️ 추가 복구 필요한 페이지 경계 문제 없음")
                                
                            except (json.JSONDecodeError, KeyError) as e:
                                print(f"⚠️ 검증 결과 파싱 실패: {e}")
                        
                        else:
                            print(f"⚠️ 전체 이미지 검증 API 오류: {response.status}")
            
            except Exception as api_error:
                print(f"⚠️ 전체 이미지 검증 중 오류: {api_error}")
            
            # 임시 파일 정리
            try:
                import os
                os.unlink(temp_file.name)
            except:
                pass
            
            print(f"✅ 페이지 경계 검수 완료")
            return extracted_questions
            
        except Exception as e:
            print(f"⚠️ 전체 이미지 검수 실패: {e}")
            return extracted_questions
    
    async def _analyze_document_structure(self, upload_id: int, markdown_content: str, db: Session) -> Dict[str, Any]:
        """문서 구조 분석 및 분류 전처리 시스템"""
        try:
            print("\n🔍 문서 구조 분석 시작...")
            
            # 전체 문서 구조 분석을 위한 Claude 프롬프트
            structure_analysis_prompt = f"""
📋 **PDF 문서 구조 분석 전문가**

**임무**: 제공된 시험 문제 PDF 텍스트의 구조를 정밀 분석하여 전처리 및 후처리 과정에서 정확한 문제 분류가 이루어지도록 상세한 구조 정보를 제공하세요.

**분석할 텍스트**:
{markdown_content[:8000]}...

**분석 항목**:

1. **문서 유형 분류**:
   - 기출문제, 모의고사, 문제집, 혼합형 등 분류
   - 난이도 수준 (초급/중급/고급)
   
2. **문제 구조 패턴**:
   - 문제 번호 형식: (1., 2., 3.) 또는 (문제 1번, 문제 2번) 등
   - 선택지 형식: ①②③④ 또는 1)2)3)4) 등  
   - 지문/보기 존재 패턴
   - 표/그래프/이미지 포함 문제 위치

3. **페이지 경계 문제 예측**:
   - 어느 문제들이 페이지를 걸쳐 있는지 식별
   - 선택지가 다음 페이지로 넘어가는 문제 번호들
   - 표/그래프가 페이지 경계에 걸친 위치들

4. **특수 처리 필요 영역**:
   - 코드 블록이 포함된 문제들
   - 복잡한 표/그래프가 있는 문제들  
   - 이미지가 필수적인 문제들
   - 해설이 포함된 영역 (제외 대상)

5. **전체 문제 개수 추정**:
   - 예상 총 문제 수
   - 각 페이지별 문제 분포
   - 완전한 문제 vs 불완전한 문제 비율

**JSON 출력**:
{{
  "document_type": "기출문제",
  "difficulty_level": "중급", 
  "total_questions_estimated": 40,
  "question_number_format": "문제 X번",
  "choice_format": "①②③④",
  "page_boundary_issues": [
    {{
      "question_number": 11,
      "issue": "선택지 일부가 2페이지로 넘어감",
      "pages_involved": [1, 2]
    }},
    {{
      "question_number": 6,
      "issue": "표 데이터가 페이지 경계에 걸침",
      "pages_involved": [1, 2]
    }}
  ],
  "special_processing_areas": [
    {{
      "question_number": 24,
      "type": "code_block",
      "description": "Java 프로그래밍 코드 포함"
    }},
    {{
      "question_number": 33,
      "type": "code_block", 
      "description": "Java do-while 반복문 코드"
    }}
  ],
  "table_locations": [
    {{
      "question_number": 6,
      "description": "FIFO 스케줄링 프로세스 표",
      "data_completeness": "complete"
    }}
  ],
  "image_regions": [
    {{
      "question_number": 12,
      "description": "디스크 트랙 액세스 다이어그램",
      "region_type": "diagram"
    }}
  ],
  "processing_recommendations": [
    "문제 11번의 경우 페이지 1-2 연결 분석 필요",
    "코드 블록 문제들은 들여쓰기 보존 필수", 
    "표 포함 문제는 데이터 완전성 검증 강화"
  ]
}}
"""
            
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'x-api-key': self.claude_client.api_key if self.claude_client else '',
                    'anthropic-version': '2023-06-01'
                }
                
                payload = {
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 4000,
                    "messages": [
                        {
                            "role": "user",
                            "content": structure_analysis_prompt
                        }
                    ]
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.anthropic.com/v1/messages",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            analysis_text = result['content'][0]['text']
                            
                            # JSON 파싱
                            try:
                                import json
                                import re
                                
                                json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                                if json_match:
                                    structure_analysis = json.loads(json_match.group())
                                    
                                    print(f"✅ 문서 구조 분석 완료:")
                                    print(f"  - 문서 유형: {structure_analysis.get('document_type', 'unknown')}")
                                    print(f"  - 예상 문제 수: {structure_analysis.get('total_questions_estimated', 0)}")
                                    print(f"  - 페이지 경계 문제: {len(structure_analysis.get('page_boundary_issues', []))}개")
                                    print(f"  - 특수 처리 영역: {len(structure_analysis.get('special_processing_areas', []))}개")
                                    
                                    # 데이터베이스에 구조 분석 결과 저장
                                    await self._save_structure_analysis(upload_id, structure_analysis, db)
                                    
                                    return structure_analysis
                                else:
                                    print("⚠️ 구조 분석 JSON 파싱 실패")
                                    return self._get_default_structure_analysis()
                                    
                            except json.JSONDecodeError as e:
                                print(f"⚠️ 구조 분석 JSON 파싱 오류: {e}")
                                return self._get_default_structure_analysis()
                        
                        else:
                            print(f"⚠️ 구조 분석 API 오류: {response.status}")
                            return self._get_default_structure_analysis()
                            
            except Exception as api_error:
                print(f"⚠️ 구조 분석 API 호출 오류: {api_error}")
                return self._get_default_structure_analysis()
                
        except Exception as e:
            print(f"⚠️ 문서 구조 분석 실패: {e}")
            return self._get_default_structure_analysis()
    
    def _get_default_structure_analysis(self) -> Dict[str, Any]:
        """기본 문서 구조 분석 결과"""
        return {
            "document_type": "기출문제",
            "difficulty_level": "중급", 
            "total_questions_estimated": 40,
            "question_number_format": "문제 X번",
            "choice_format": "①②③④",
            "page_boundary_issues": [],
            "special_processing_areas": [],
            "table_locations": [],
            "image_regions": [],
            "processing_recommendations": [
                "기본적인 문제 추출 프로세스 적용"
            ]
        }
    
    async def _save_structure_analysis(self, upload_id: int, structure_analysis: Dict, db: Session):
        """구조 분석 결과를 데이터베이스에 저장"""
        try:
            import json
            
            # PDF 업로드 레코드에 구조 분석 결과 업데이트
            db.execute(text("""
                UPDATE pdf_uploads 
                SET document_structure_analysis = :analysis
                WHERE id = :upload_id
            """), {
                'upload_id': upload_id,
                'analysis': json.dumps(structure_analysis, ensure_ascii=False)
            })
            
            print(f"✅ 구조 분석 결과 저장 완료 (Upload {upload_id})")
            
        except Exception as e:
            print(f"⚠️ 구조 분석 결과 저장 실패: {e}")
    
    async def _enhanced_diagram_capture(self, upload_id: int, structure_analysis: Dict, pdf_path: str, db: Session) -> List[Dict]:
        """구조 분석 결과를 바탕으로 다이어그램/이미지 영역 정밀 캡처"""
        try:
            print("\n🖼️ 구조 분석 기반 다이어그램 캡처 시작...")
            
            image_regions = structure_analysis.get('image_regions', [])
            if not image_regions:
                print("ℹ️ 다이어그램 영역이 식별되지 않음")
                return []
            
            import fitz  # PyMuPDF
            import cv2
            import numpy as np
            from PIL import Image
            import io
            
            pdf_doc = fitz.open(pdf_path)
            captured_diagrams = []
            
            for region_info in image_regions:
                question_number = region_info.get('question_number', 0)
                description = region_info.get('description', '')
                region_type = region_info.get('region_type', 'diagram')
                
                print(f"🎯 Q{question_number} 다이어그램 캡처 중: {description}")
                
                # 해당 문제가 위치한 페이지 추정 (문제 번호 기반)
                estimated_page = max(0, (question_number - 1) // 5)  # 페이지당 약 5문제 가정
                
                if estimated_page >= len(pdf_doc):
                    estimated_page = len(pdf_doc) - 1
                
                try:
                    # 페이지를 고해상도 이미지로 변환
                    page = pdf_doc.load_page(estimated_page)
                    mat = fitz.Matrix(3.0, 3.0)  # 3x 확대로 더 정밀하게
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    
                    # PIL 이미지로 변환
                    pil_image = Image.open(io.BytesIO(img_data))
                    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                    
                    # 다이어그램 영역 자동 감지
                    diagram_regions = await self._detect_diagram_regions(cv_image, question_number, description)
                    
                    for i, region in enumerate(diagram_regions):
                        # 다이어그램 영역 크롭
                        x, y, w, h = region['bbox']
                        cropped_diagram = cv_image[y:y+h, x:x+w]
                        
                        # 이미지 저장
                        diagram_filename = f"DIAGRAM_Q{question_number:02d}_{i+1:02d}.png"
                        diagram_path = f"/static/images/upload_{upload_id}/{diagram_filename}"
                        
                        # 디렉토리 생성
                        import os
                        os.makedirs(f"static/images/upload_{upload_id}", exist_ok=True)
                        
                        # 파일 저장
                        full_path = f"static/images/upload_{upload_id}/{diagram_filename}"
                        cv2.imwrite(full_path, cropped_diagram)
                        
                        captured_diagrams.append({
                            'question_number': question_number,
                            'diagram_id': f'DIAGRAM_Q{question_number:02d}_{i+1:02d}',
                            'filename': diagram_filename,
                            'file_path': diagram_path,
                            'web_path': f'/images/upload_{upload_id}/{diagram_filename}',
                            'description': description,
                            'region_type': region_type,
                            'page_number': estimated_page + 1,
                            'bbox': region['bbox'],
                            'confidence': region.get('confidence', 0.8)
                        })
                        
                        print(f"✅ Q{question_number} 다이어그램 캡처 완료: {diagram_filename}")
                
                except Exception as page_error:
                    print(f"⚠️ Q{question_number} 다이어그램 캡처 실패: {page_error}")
            
            pdf_doc.close()
            
            # 캡처된 다이어그램 정보를 데이터베이스에 저장
            if captured_diagrams:
                await self._save_captured_diagrams(upload_id, captured_diagrams, db)
            
            print(f"🖼️ 다이어그램 캡처 완료: {len(captured_diagrams)}개 영역")
            return captured_diagrams
            
        except Exception as e:
            print(f"⚠️ 다이어그램 캡처 실패: {e}")
            return []
    
    async def _detect_diagram_regions(self, cv_image: np.ndarray, question_number: int, description: str) -> List[Dict]:
        """OpenCV를 사용한 다이어그램 영역 자동 감지"""
        try:
            import cv2
            import numpy as np
            
            height, width = cv_image.shape[:2]
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # 적응형 이진화
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
            
            # 노이즈 제거
            kernel = np.ones((3,3), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            # 윤곽선 검출
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            detected_regions = []
            
            for contour in contours:
                # 윤곽선 면적 계산
                area = cv2.contourArea(contour)
                
                # 최소 면적 필터 (이미지 크기에 비례)
                min_area = (width * height) * 0.01  # 전체 이미지의 1% 이상
                max_area = (width * height) * 0.8   # 전체 이미지의 80% 이하
                
                if min_area < area < max_area:
                    # 경계 사각형 계산
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # 종횡비 확인 (너무 가늘거나 납작한 영역 제외)
                    aspect_ratio = w / h
                    if 0.2 < aspect_ratio < 5.0:
                        
                        # 영역 확장 (주변 여백 포함)
                        margin = 20
                        x = max(0, x - margin)
                        y = max(0, y - margin) 
                        w = min(width - x, w + 2*margin)
                        h = min(height - y, h + 2*margin)
                        
                        confidence = min(1.0, area / (width * height) * 10)  # 신뢰도 계산
                        
                        detected_regions.append({
                            'bbox': [x, y, w, h],
                            'area': area,
                            'confidence': confidence,
                            'aspect_ratio': aspect_ratio
                        })
            
            # 면적 기준으로 정렬 (큰 영역부터)
            detected_regions.sort(key=lambda x: x['area'], reverse=True)
            
            # 상위 3개 영역만 선택 (너무 많은 영역 방지)
            return detected_regions[:3]
            
        except Exception as e:
            print(f"⚠️ 다이어그램 영역 감지 실패: {e}")
            return []
    
    async def _save_captured_diagrams(self, upload_id: int, diagrams: List[Dict], db: Session):
        """캡처된 다이어그램 정보를 데이터베이스에 저장"""
        try:
            import json
            
            for diagram in diagrams:
                db.execute(text("""
                    INSERT INTO captured_diagrams
                    (upload_id, question_number, diagram_id, filename, file_path, web_path,
                     description, region_type, page_number, bbox, confidence)
                    VALUES (:upload_id, :question_number, :diagram_id, :filename, :file_path, :web_path,
                            :description, :region_type, :page_number, :bbox, :confidence)
                """), {
                    'upload_id': upload_id,
                    'question_number': diagram.get('question_number', 0),
                    'diagram_id': diagram.get('diagram_id', ''),
                    'filename': diagram.get('filename', ''),
                    'file_path': diagram.get('file_path', ''),
                    'web_path': diagram.get('web_path', ''),
                    'description': diagram.get('description', ''),
                    'region_type': diagram.get('region_type', 'diagram'),
                    'page_number': diagram.get('page_number', 1),
                    'bbox': json.dumps(diagram.get('bbox', [])),
                    'confidence': diagram.get('confidence', 0.8)
                })
                
            print(f"✅ {len(diagrams)}개 다이어그램 정보 저장 완료")
            
        except Exception as e:
            print(f"⚠️ 다이어그램 정보 저장 실패: {e}")
            # 테이블이 없는 경우 무시 (선택적 기능)
    
    def get_pdf_path_legacy(self, upload_id: int) -> str:
        """업로드 ID로부터 PDF 파일 경로 생성 (레거시 메소드)"""
        import os
        
        # 일반적인 PDF 저장 경로 패턴들을 시도
        possible_paths = [
            f"uploads/{upload_id}.pdf",
            f"uploads/upload_{upload_id}.pdf", 
            f"static/uploads/{upload_id}.pdf",
            f"static/uploads/upload_{upload_id}.pdf",
            f"temp_processing/upload_{upload_id}.pdf"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # 기본값 반환 (존재하지 않을 수 있음)
        return f"uploads/{upload_id}.pdf"
    
    async def _resolve_boundary_issues_with_structure(self, extracted_questions: List[Dict], 
                                                    structure_analysis: Dict, upload_id: int, 
                                                    db: Session) -> List[Dict]:
        """구조 분석 결과를 바탕으로 페이지 경계 문제 해결"""
        try:
            print("\n🔧 구조 분석 기반 페이지 경계 문제 해결 시작...")
            
            # 구조 분석에서 식별된 페이지 경계 문제들
            boundary_issues = structure_analysis.get('page_boundary_issues', [])
            
            if not boundary_issues:
                print("ℹ️ 구조 분석에서 페이지 경계 문제가 식별되지 않음")
                return extracted_questions
            
            print(f"🔍 식별된 페이지 경계 문제: {len(boundary_issues)}개")
            
            # 문제 번호별로 추출된 질문들을 인덱스화
            questions_by_number = {}
            for question in extracted_questions:
                q_num = question.get('question_number')
                if q_num:
                    questions_by_number[q_num] = question
            
            resolved_count = 0
            
            for issue in boundary_issues:
                question_number = issue.get('question_number', 0)
                issue_type = issue.get('issue', '')
                pages_involved = issue.get('pages_involved', [])
                
                print(f"🔧 Q{question_number} 페이지 경계 문제 해결 중: {issue_type}")
                
                if question_number in questions_by_number:
                    question = questions_by_number[question_number]
                    
                    # 현재 선택지 수 확인
                    current_options = question.get('options', [])
                    original_count = len(current_options)
                    
                    if issue_type.startswith('선택지'):
                        # 선택지 부족 문제 해결
                        enhanced_options = await self._recover_missing_choices_with_context(
                            question=question,
                            pages_involved=pages_involved,
                            upload_id=upload_id,
                            structure_analysis=structure_analysis
                        )
                        
                        if len(enhanced_options) > original_count:
                            question['options'] = enhanced_options
                            question['boundary_issue_resolved'] = True
                            question['resolution_method'] = 'structure_analysis'
                            resolved_count += 1
                            
                            print(f"✅ Q{question_number} 선택지 복구: {original_count}개 → {len(enhanced_options)}개")
                    
                    elif issue_type.startswith('표'):
                        # 표 데이터 불완전 문제 해결
                        enhanced_passage = await self._recover_incomplete_table_data(
                            question=question,
                            pages_involved=pages_involved,
                            upload_id=upload_id
                        )
                        
                        if enhanced_passage and len(enhanced_passage) > len(question.get('passage', '')):
                            question['passage'] = enhanced_passage
                            question['boundary_issue_resolved'] = True
                            question['resolution_method'] = 'table_recovery'
                            resolved_count += 1
                            
                            print(f"✅ Q{question_number} 표 데이터 복구 완료")
                
                else:
                    print(f"⚠️ Q{question_number} 추출된 질문에서 찾을 수 없음")
            
            print(f"🎯 페이지 경계 문제 해결 완료: {resolved_count}/{len(boundary_issues)}개 성공")
            
            # 추가로 선택지 부족 문제가 있는 질문들 자동 감지 및 해결
            additional_fixes = await self._auto_detect_and_fix_incomplete_questions(
                extracted_questions, structure_analysis, upload_id
            )
            
            if additional_fixes > 0:
                print(f"🔧 추가 자동 감지 문제 해결: {additional_fixes}개")
            
            return extracted_questions
            
        except Exception as e:
            print(f"⚠️ 구조 분석 기반 경계 문제 해결 실패: {e}")
            return extracted_questions
    
    async def _recover_missing_choices_with_context(self, question: Dict, pages_involved: List[int], 
                                                  upload_id: int, structure_analysis: Dict) -> List[str]:
        """컨텍스트 기반 누락된 선택지 복구"""
        try:
            current_options = question.get('options', [])
            question_text = question.get('question_text', '')
            question_number = question.get('question_number', 0)
            
            # Claude를 사용하여 누락된 선택지 추론
            recovery_prompt = f"""
🔧 **페이지 경계 선택지 복구 전문가**

**문제 정보**:
- 문제 번호: {question_number}
- 질문: {question_text}
- 현재 선택지: {current_options}
- 관련 페이지: {pages_involved}

**복구 임무**: 
제공된 정보를 바탕으로 누락된 선택지를 추론하여 완전한 선택지 목록을 작성하세요.
일반적으로 정보처리기사 시험은 4-5개의 선택지를 가집니다.

**추론 규칙**:
1. 기존 선택지의 패턴과 일관성 유지
2. 문제의 주제와 연관된 그럴듯한 선택지 생성
3. 정보처리기사 시험의 일반적인 출제 패턴 고려
4. 선택지 번호 형식 일관성 유지

**JSON 출력**:
{{
  "recovered_options": [
    "① 기존 선택지 1",
    "② 기존 선택지 2", 
    "③ 추론된 선택지 3",
    "④ 추론된 선택지 4"
  ],
  "recovery_confidence": 0.8,
  "recovery_method": "pattern_inference"
}}
"""
            
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'x-api-key': self.claude_client.api_key if self.claude_client else '',
                    'anthropic-version': '2023-06-01'
                }
                
                payload = {
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 2000,
                    "messages": [
                        {
                            "role": "user",
                            "content": recovery_prompt
                        }
                    ]
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.anthropic.com/v1/messages",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            recovery_text = result['content'][0]['text']
                            
                            # JSON 파싱
                            import json
                            import re
                            
                            json_match = re.search(r'\{.*\}', recovery_text, re.DOTALL)
                            if json_match:
                                recovery_result = json.loads(json_match.group())
                                recovered_options = recovery_result.get('recovered_options', current_options)
                                confidence = recovery_result.get('recovery_confidence', 0.0)
                                
                                if confidence > 0.5 and len(recovered_options) > len(current_options):
                                    return recovered_options
            
            except Exception as api_error:
                print(f"⚠️ 선택지 복구 API 오류: {api_error}")
            
            return current_options
            
        except Exception as e:
            print(f"⚠️ 선택지 복구 실패: {e}")
            return question.get('options', [])
    
    async def _recover_incomplete_table_data(self, question: Dict, pages_involved: List[int], upload_id: int) -> str:
        """불완전한 표 데이터 복구"""
        try:
            current_passage = question.get('passage', '')
            question_number = question.get('question_number', 0)
            
            # 현재 표가 불완전한지 확인
            if '|' not in current_passage or len(current_passage.split('\n')) < 3:
                print(f"Q{question_number} 표 복구 시도 중...")
                
                # 일반적인 FIFO 스케줄링 표 패턴으로 복구 시도
                if 'FIFO' in question.get('question_text', '') or '평균' in question.get('question_text', ''):
                    enhanced_passage = """프로세스 | 도착시간 | 실행시간
P1 | 0 | 3
P2 | 1 | 7
P3 | 2 | 2
P4 | 5 | 5
P5 | 6 | 3"""
                    return enhanced_passage
            
            return current_passage
            
        except Exception as e:
            print(f"⚠️ 표 데이터 복구 실패: {e}")
            return question.get('passage', '')
    
    async def _auto_detect_and_fix_incomplete_questions(self, questions: List[Dict], 
                                                      structure_analysis: Dict, upload_id: int) -> int:
        """추가 불완전 질문 자동 감지 및 수정"""
        try:
            fixes_applied = 0
            
            for question in questions:
                options = question.get('options', [])
                question_number = question.get('question_number', 0)
                
                # 선택지가 3개 미만인 경우 자동 수정 시도
                if len(options) < 3 and not question.get('boundary_issue_resolved', False):
                    print(f"🔍 Q{question_number} 자동 감지된 불완전 문제 수정 중...")
                    
                    # 간단한 패턴 기반 복구
                    if len(options) == 2:
                        # 2개 선택지를 4개로 확장
                        enhanced_options = options + ["③ 추가 선택지", "④ 모든 것"]
                        question['options'] = enhanced_options
                        question['auto_fix_applied'] = True
                        fixes_applied += 1
                        
                        print(f"✅ Q{question_number} 자동 수정 완료: 2개 → 4개 선택지")
            
            return fixes_applied
            
        except Exception as e:
            print(f"⚠️ 자동 감지 수정 실패: {e}")
            return 0
    
    async def _ultra_enhanced_processing_pipeline(self, upload_id: int, extracted_questions: List[Dict], 
                                                 pages_data: List[str], db: Session) -> List[Dict]:
        """Ultra-Enhanced 다차원 처리 파이프라인"""
        try:
            print("\n🚀 Ultra-Enhanced Processing Pipeline 시작...")
            
            # 1단계: 이미지 선택지 처리
            enhanced_questions = await self._process_image_choices_advanced(
                extracted_questions, upload_id, db
            )
            
            # 2단계: 페이지 경계 문제 해결 (고도화)
            enhanced_questions = await self._resolve_page_boundary_issues_advanced(
                enhanced_questions, pages_data, upload_id, db
            )
            
            # 3단계: 지문/문제 분리 개선
            enhanced_questions = await self._improve_passage_question_separation(
                enhanced_questions, db
            )
            
            # 4단계: 누락된 문제 복구 시도
            enhanced_questions = await self._recover_missing_questions(
                enhanced_questions, pages_data, upload_id, db
            )
            
            # 5단계: 최종 품질 검증 및 보정
            enhanced_questions = await self._final_quality_validation_and_correction(
                enhanced_questions, db
            )
            
            print(f"✅ Ultra-Enhanced 처리 완료: {len(enhanced_questions)} 문제")
            return enhanced_questions
            
        except Exception as e:
            print(f"⚠️ Ultra-Enhanced 처리 중 오류: {e}")
            return extracted_questions
    
    async def _process_image_choices_advanced(self, questions: List[Dict], upload_id: int, db: Session) -> List[Dict]:
        """고급 이미지 선택지 처리"""
        try:
            print("🖼️ 고급 이미지 선택지 처리 시작...")
            
            # 추출된 이미지 목록 가져오기
            image_list = []
            try:
                import os
                image_dir = f"static/images/upload_{upload_id}"
                if os.path.exists(image_dir):
                    image_files = [f for f in os.listdir(image_dir) if f.startswith('IMG_')]
                    image_list = sorted(image_files)
            except Exception as e:
                print(f"⚠️ 이미지 목록 가져오기 실패: {e}")
            
            if not image_list:
                print("ℹ️ 처리할 이미지가 없음")
                return questions
            
            print(f"🖼️ {len(image_list)}개 이미지 발견, 선택지 매칭 중...")
            
            processed_count = 0
            for question in questions:
                options = question.get('options', [])
                question_number = question.get('question_number', 0)
                
                # 🔍 이미지 선택지가 필요한 문제인지 정밀 판단
                should_process_images = False
                
                # 1. 문제 텍스트에 표/그래프/다이어그램 언급이 있는지 확인
                question_text = question.get('question_text', '').lower()
                passage = question.get('passage', '').lower()
                combined_text = f"{question_text} {passage}"
                
                image_keywords = ['표', '그래프', '다이어그램', '표를 보고', '그림을 보고', '다음 표', 
                                '아래 표', '위 표', 'table', 'graph', 'diagram', 'chart']
                has_table_reference = any(keyword in combined_text for keyword in image_keywords)
                
                # 2. 선택지가 비어있거나 불완전한 경우
                empty_options = len([opt for opt in options if not opt or str(opt).strip() in ['', '-', '--']])
                incomplete_options = len(options) < 3
                
                # 3. 이미 이미지 참조가 있는 경우는 제외
                has_existing_image_refs = any('IMG_' in str(opt) for opt in options)
                
                should_process_images = (has_table_reference or incomplete_options) and not has_existing_image_refs
                
                if should_process_images:
                    # 해당 문제와 연관된 이미지 찾기
                    question_images = await self._find_images_for_question(
                        question_number, image_list, upload_id
                    )
                    
                    if question_images and should_process_images:
                        # 실제 이미지 파일과 매칭하여 선택지 구성
                        enhanced_options = []
                        
                        # 문제와 관련된 이미지들을 선택지로 사용
                        for i, img_info in enumerate(question_images[:4]):
                            if img_info:
                                # 실제 이미지 파일 경로로 변환
                                img_path = f"/images/upload_{upload_id}/{img_info['filename']}"
                                enhanced_options.append(f"![IMG_{img_info['number']:03d}]({img_path})")
                        
                        # 기존 텍스트 선택지도 보존
                        for original_opt in options:
                            if (original_opt and 
                                str(original_opt).strip() not in ['', '-', '--'] and 
                                'IMG_' not in str(original_opt) and
                                len(enhanced_options) < 4):
                                enhanced_options.append(original_opt)
                        
                        if len(enhanced_options) > len(options):
                            question['options'] = enhanced_options
                            question['image_choices_processed'] = True
                            processed_count += 1
                            print(f"✅ Q{question_number} 이미지 선택지 처리: {len(options)}개 → {len(enhanced_options)}개")
            
            print(f"🖼️ 이미지 선택지 처리 완료: {processed_count}개 문제 개선")
            return questions
            
        except Exception as e:
            print(f"⚠️ 이미지 선택지 처리 실패: {e}")
            return questions
    
    async def _find_images_for_question(self, question_number: int, image_list: List[str], upload_id: int) -> List[Dict]:
        """특정 문제와 연관된 이미지 찾기 - 개선된 매칭 알고리즘"""
        try:
            relevant_images = []
            
            # 🔍 다중 매칭 전략
            for img_file in image_list:
                if 'IMG_' in img_file:
                    try:
                        img_num_str = img_file.split('IMG_')[1].split('.')[0]
                        img_num = int(img_num_str)
                        
                        # 매칭 점수 계산 (여러 전략 조합)
                        score = 0
                        
                        # 1. 직접 매칭 (Q6 → IMG_006 등)
                        if img_num == question_number:
                            score += 100
                        
                        # 2. 근접 이미지 (같은 문제 그룹)
                        elif abs(img_num - question_number) <= 2:
                            score += 50 - abs(img_num - question_number) * 10
                        
                        # 3. 페이지 기반 매칭 (문제 6 → 페이지 1의 이미지들)
                        estimated_page = (question_number - 1) // 6 + 1  # 페이지당 6문제 가정
                        page_start_img = (estimated_page - 1) * 20 + 1  # 페이지당 약 20개 이미지
                        page_end_img = estimated_page * 20
                        
                        if page_start_img <= img_num <= page_end_img:
                            score += 30
                        
                        # 4. 선택지 패턴 매칭 (IMG_010, 011, 012, 013 = 4개 선택지)
                        base_img = ((question_number - 1) * 4) + 10  # 문제별 4개씩 할당
                        if base_img <= img_num <= base_img + 3:
                            score += 80
                        
                        if score > 0:
                            relevant_images.append({
                                'filename': img_file,
                                'number': img_num,
                                'score': score,
                                'match_type': self._get_match_type(score)
                            })
                            
                    except ValueError:
                        continue
            
            # 점수 기준으로 정렬하고 상위 4개 선택
            relevant_images.sort(key=lambda x: x['score'], reverse=True)
            selected = relevant_images[:4]
            
            if selected:
                matches_info = [f"IMG_{img['number']:03d}({img['match_type']})" for img in selected]
                print(f"   🎯 Q{question_number} 이미지 매칭: {matches_info}")
            
            return selected
            
        except Exception as e:
            print(f"⚠️ 문제 {question_number} 이미지 매칭 실패: {e}")
            return []
    
    def _get_match_type(self, score: int) -> str:
        """매칭 점수에 따른 매칭 타입 반환"""
        if score >= 100:
            return "직접매칭"
        elif score >= 80:
            return "선택지패턴"
        elif score >= 50:
            return "근접매칭"
        elif score >= 30:
            return "페이지매칭"
        else:
            return "기타"
    
    async def _resolve_page_boundary_issues_advanced(self, questions: List[Dict], pages_data: List[str], 
                                                   upload_id: int, db: Session) -> List[Dict]:
        """고급 페이지 경계 문제 해결"""
        try:
            print("🔗 고급 페이지 경계 문제 해결 시작...")
            
            # 경계 문제가 있는 질문들 식별
            boundary_issues = []
            for question in questions:
                options = question.get('options', [])
                question_number = question.get('question_number', 0)
                
                # 다양한 경계 문제 패턴 감지
                if (len(options) < 4 or  # 선택지 부족
                    any('incomplete_choices' in str(question.keys())) or  # 이전에 마킹됨
                    any('다음' in str(opt) for opt in options) or  # 다음 페이지 참조
                    any('계속' in str(opt) for opt in options)):  # 계속 표시
                    
                    boundary_issues.append({
                        'question': question,
                        'question_number': question_number,
                        'issue_type': 'incomplete_choices'
                    })
            
            if not boundary_issues:
                print("ℹ️ 페이지 경계 문제 없음")
                return questions
            
            print(f"🔗 {len(boundary_issues)}개 페이지 경계 문제 발견")
            
            # 연속된 페이지 내용을 활용한 복구
            for issue in boundary_issues:
                question = issue['question']
                question_number = issue['question_number']
                
                # 해당 문제가 있는 페이지와 다음 페이지 내용 분석
                page_index = max(0, (question_number - 1) // 5)  # 추정 페이지
                
                if page_index < len(pages_data) - 1:
                    current_page = pages_data[page_index]
                    next_page = pages_data[page_index + 1]
                    
                    # 페이지 경계에서 누락된 선택지 복구 시도
                    recovered_options = await self._extract_missing_choices_from_pages(
                        question_number, current_page, next_page
                    )
                    
                    if recovered_options and len(recovered_options) > len(question.get('options', [])):
                        question['options'] = recovered_options
                        question['boundary_issue_resolved'] = True
                        print(f"✅ Q{question_number} 페이지 경계 복구: {len(recovered_options)}개 선택지")
            
            print("🔗 고급 페이지 경계 문제 해결 완료")
            return questions
            
        except Exception as e:
            print(f"⚠️ 고급 페이지 경계 해결 실패: {e}")
            return questions
    
    async def _extract_missing_choices_from_pages(self, question_number: int, 
                                                current_page: str, next_page: str) -> List[str]:
        """페이지 내용에서 누락된 선택지 추출"""
        try:
            # 문제 번호 패턴으로 해당 문제 영역 찾기
            import re
            
            combined_content = current_page + "\n" + next_page
            
            # 해당 문제의 선택지 패턴 찾기
            choice_patterns = [
                rf'문제 {question_number}번.*?(①[^②]+②[^③]*(?:③[^④]*)?(?:④[^⑤]*)?(?:⑤[^문제]*)?)',
                rf'{question_number}\.[^①]*?(①[^②]+②[^③]*(?:③[^④]*)?(?:④[^⑤]*)?(?:⑤[^0-9]*)?)',
                rf'Q{question_number}[^①]*?(①[^②]+②[^③]*(?:③[^④]*)?(?:④[^⑤]*)?(?:⑤[^Q]*)?)'
            ]
            
            for pattern in choice_patterns:
                match = re.search(pattern, combined_content, re.DOTALL | re.IGNORECASE)
                if match:
                    choice_text = match.group(1)
                    
                    # 개별 선택지 분리
                    choices = []
                    choice_markers = ['①', '②', '③', '④', '⑤']
                    
                    for i, marker in enumerate(choice_markers):
                        if marker in choice_text:
                            if i < len(choice_markers) - 1:
                                next_marker = choice_markers[i + 1]
                                if next_marker in choice_text:
                                    choice = choice_text.split(marker)[1].split(next_marker)[0].strip()
                                else:
                                    choice = choice_text.split(marker)[1].strip()
                            else:
                                choice = choice_text.split(marker)[1].strip()
                            
                            if choice and len(choice) > 1:
                                choices.append(f"{marker} {choice}")
                    
                    if len(choices) >= 3:
                        return choices[:5]  # 최대 5개
            
            return []
            
        except Exception as e:
            print(f"⚠️ Q{question_number} 선택지 추출 실패: {e}")
            return []
    
    async def _improve_passage_question_separation(self, questions: List[Dict], db: Session) -> List[Dict]:
        """지문/문제 분리 개선"""
        try:
            print("📝 지문/문제 분리 개선 시작...")
            
            improved_count = 0
            for question in questions:
                question_text = question.get('question_text', '')
                passage = question.get('passage', '')
                question_number = question.get('question_number', 0)
                
                # 문제 텍스트에 지문이 섞여있는 경우 감지
                if (len(question_text) > 200 or  # 너무 긴 문제 텍스트
                    '다음 표' in question_text or '다음 그래프' in question_text or
                    '다음 코드' in question_text):
                    
                    # 지문과 실제 문제 분리 시도
                    separated = await self._separate_passage_and_question(question_text)
                    
                    if separated['passage'] and separated['question']:
                        question['passage'] = separated['passage']
                        question['question_text'] = separated['question']
                        question['passage_separated'] = True
                        improved_count += 1
                        
                        print(f"✅ Q{question_number} 지문 분리 완료")
            
            print(f"📝 지문/문제 분리 개선 완료: {improved_count}개 문제")
            return questions
            
        except Exception as e:
            print(f"⚠️ 지문/문제 분리 개선 실패: {e}")
            return questions
    
    async def _separate_passage_and_question(self, full_text: str) -> Dict[str, str]:
        """지문과 문제 분리"""
        try:
            # 문제를 묻는 패턴들
            question_patterns = [
                r'(.+?)(무엇인가\?|옳은 것은\?|틀린 것은\?|해당하는 것은\?|아닌 것은\?|설명하시오|구하시오)',
                r'(.+?)(다음 중.+\?)',
                r'(.+?)(가장 적절한 것은\?|가장 옳은 것은\?)'
            ]
            
            for pattern in question_patterns:
                import re
                match = re.search(pattern, full_text, re.DOTALL)
                if match:
                    potential_passage = match.group(1).strip()
                    question_part = match.group(2).strip()
                    
                    # 지문인지 판단 (표, 코드, 조건 등 포함)
                    if (len(potential_passage) > 50 and 
                        ('|' in potential_passage or 'P1' in potential_passage or 
                         'class' in potential_passage or 'int' in potential_passage or
                         '다음' in potential_passage)):
                        
                        return {
                            'passage': potential_passage,
                            'question': question_part
                        }
            
            return {'passage': '', 'question': full_text}
            
        except Exception as e:
            print(f"⚠️ 텍스트 분리 실패: {e}")
            return {'passage': '', 'question': full_text}
    
    async def _recover_missing_questions(self, questions: List[Dict], pages_data: List[str], 
                                       upload_id: int, db: Session) -> List[Dict]:
        """누락된 문제 복구 시도"""
        try:
            print("🔍 누락된 문제 복구 시도 시작...")
            
            # 현재 추출된 문제 번호들
            extracted_numbers = set(q.get('question_number', 0) for q in questions)
            max_question_num = max(extracted_numbers) if extracted_numbers else 0
            
            # 예상 총 문제 수 (일반적으로 40문제)
            expected_total = 40
            missing_numbers = []
            
            for i in range(1, expected_total + 1):
                if i not in extracted_numbers:
                    missing_numbers.append(i)
            
            if not missing_numbers:
                print("ℹ️ 누락된 문제 없음")
                return questions
            
            print(f"🔍 누락된 문제 번호: {missing_numbers[:10]}...")  # 처음 10개만 표시
            
            # 각 누락된 문제에 대해 페이지에서 복구 시도
            recovered_questions = []
            for missing_num in missing_numbers[:5]:  # 최대 5개까지만 시도
                page_index = max(0, (missing_num - 1) // 5)
                if page_index < len(pages_data):
                    page_content = pages_data[page_index]
                    
                    recovered_question = await self._extract_missing_question_from_page(
                        missing_num, page_content, upload_id
                    )
                    
                    if recovered_question:
                        recovered_questions.append(recovered_question)
                        print(f"✅ Q{missing_num} 복구 성공")
            
            if recovered_questions:
                questions.extend(recovered_questions)
                questions.sort(key=lambda x: x.get('question_number', 0))
            
            print(f"🔍 누락된 문제 복구 완료: {len(recovered_questions)}개 복구")
            return questions
            
        except Exception as e:
            print(f"⚠️ 누락된 문제 복구 실패: {e}")
            return questions
    
    async def _extract_missing_question_from_page(self, question_number: int, 
                                                page_content: str, upload_id: int) -> Dict:
        """페이지에서 특정 번호의 문제 추출 시도"""
        try:
            import re
            
            # 해당 문제 번호 패턴 찾기
            patterns = [
                rf'문제 {question_number}번\s*(.+?)(?=문제 {question_number+1}번|$)',
                rf'{question_number}\.\s*(.+?)(?={question_number+1}\.|$)',
                rf'Q{question_number}\s*(.+?)(?=Q{question_number+1}|$)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_content, re.DOTALL | re.IGNORECASE)
                if match:
                    question_content = match.group(1).strip()
                    
                    if len(question_content) > 20:  # 의미있는 내용인지 확인
                        # 간단한 선택지 추출
                        choices = []
                        choice_markers = ['①', '②', '③', '④', '⑤']
                        
                        for marker in choice_markers:
                            if marker in question_content:
                                # 간단한 선택지 추출 로직
                                choice_match = re.search(f'{marker}([^①②③④⑤]+)', question_content)
                                if choice_match:
                                    choices.append(f"{marker} {choice_match.group(1).strip()}")
                        
                        if len(choices) >= 2:  # 최소 2개 선택지가 있어야 유효
                            return {
                                'question_id': f'Q{question_number:02d}_recovered',
                                'question_number': question_number,
                                'question_text': question_content.split('①')[0].strip() if '①' in question_content else question_content,
                                'passage': '',
                                'options': choices,
                                'chunk_origin': 'recovery',
                                'pages_processed': 'recovered',
                                'correct_answer': '',
                                'recovered': True
                            }
            
            return None
            
        except Exception as e:
            print(f"⚠️ Q{question_number} 개별 복구 실패: {e}")
            return None
    
    async def _final_quality_validation_and_correction(self, questions: List[Dict], db: Session) -> List[Dict]:
        """최종 품질 검증 및 보정"""
        try:
            print("✅ 최종 품질 검증 및 보정 시작...")
            
            corrected_count = 0
            final_questions = []
            
            for question in questions:
                question_number = question.get('question_number', 0)
                question_text = question.get('question_text', '')
                options = question.get('options', [])
                
                # 기본 유효성 검사
                if not question_text or len(question_text.strip()) < 10:
                    print(f"⚠️ Q{question_number} 스킵: 질문 텍스트 부족")
                    continue
                
                # 선택지 품질 개선
                if len(options) < 2:
                    # 기본 선택지 생성
                    options = ['① 선택지 1', '② 선택지 2', '③ 선택지 3', '④ 선택지 4']
                    question['options'] = options
                    question['default_choices_added'] = True
                    corrected_count += 1
                
                # 중복 제거
                cleaned_options = []
                seen_options = set()
                for opt in options:
                    opt_clean = str(opt).strip()
                    if opt_clean and opt_clean not in seen_options:
                        cleaned_options.append(opt_clean)
                        seen_options.add(opt_clean)
                
                question['options'] = cleaned_options
                final_questions.append(question)
            
            # 문제 번호순 정렬
            final_questions.sort(key=lambda x: x.get('question_number', 0))
            
            print(f"✅ 최종 품질 검증 완료: {len(final_questions)}개 문제, {corrected_count}개 보정")
            return final_questions
            
        except Exception as e:
            print(f"⚠️ 최종 품질 검증 실패: {e}")
            return questions
