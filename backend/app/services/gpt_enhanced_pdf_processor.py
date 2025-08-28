"""
GPT Enhanced PDF Processor - GPT 제안사항을 완전 구현한 버전
페이지 분할 버그, 크로스페이지 처리, 컬럼 기반 처리, OCR 기반 선택지 추출 등 포함
"""

import asyncio
import json
import re
import base64
import io
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF
import openai
import anthropic
from sqlalchemy.orm import Session
import logging
from .enhanced_prompts import EnhancedPrompts

logger = logging.getLogger(__name__)

class GPTEnhancedPDFProcessor:
    """GPT 제안사항을 완전 구현한 향상된 PDF 처리 시스템"""
    
    def __init__(self):
        self.openai_client = None
        self.claude_client = None
        self.temp_dir = Path("temp_enhanced_processing")
        self.temp_dir.mkdir(exist_ok=True)
        
        # OCR 기반 선택지 패턴
        self.choice_patterns = [
            r'①\s*([^②③④⑤]*?)(?=②|$)',
            r'②\s*([^①③④⑤]*?)(?=③|$)', 
            r'③\s*([^①②④⑤]*?)(?=④|$)',
            r'④\s*([^①②③⑤]*?)(?=⑤|$)',
            r'⑤\s*([^①②③④]*?)(?=\n|$)'
        ]
        
    def set_openai_key(self, api_key: str):
        """OpenAI API 키 설정"""
        self.openai_client = openai.AsyncOpenAI(api_key=api_key)
        
    def set_claude_key(self, api_key: str):
        """Claude API 키 설정"""
        self.claude_client = anthropic.AsyncAnthropic(api_key=api_key)

    async def process_pdf_enhanced_pipeline(self, upload_id: int, pdf_path: str, db: Session) -> Dict[str, Any]:
        """GPT 제안사항 완전 구현 파이프라인"""
        try:
            print(f"[시작] GPT Enhanced Processing Pipeline - Upload {upload_id}")
            
            # 1단계: 초고해상도 PDF 변환 (DPI 600)
            high_res_result = await self._convert_pdf_ultra_high_res(upload_id, pdf_path, db)
            if not high_res_result['success']:
                return high_res_result
                
            # 2단계: 컬럼 감지 및 2열 처리
            column_result = await self._detect_and_process_columns(upload_id, high_res_result, db)
            if not column_result['success']:
                return column_result
                
            # 3단계: 크로스페이지 연결 감지 및 스티칭
            stitching_result = await self._detect_and_stitch_cross_page(upload_id, column_result, db)
            if not stitching_result['success']:
                return stitching_result
                
            # 4단계: OCR 기반 선택지 추출
            ocr_result = await self._extract_choices_with_ocr(upload_id, stitching_result, db)
            if not ocr_result['success']:
                return ocr_result
                
            # 5단계: 에셋 파이프라인 (표, 그림, 코드)
            asset_result = await self._process_assets_pipeline(upload_id, ocr_result, db)
            
            return {
                'success': True,
                'upload_id': upload_id,
                'processing_summary': asset_result,
                'questions_extracted': len(asset_result.get('questions', [])),
                'assets_processed': len(asset_result.get('assets', [])),
                'cross_page_stitches': asset_result.get('cross_page_count', 0)
            }
            
        except Exception as e:
            logger.error(f"GPT Enhanced PDF 처리 오류: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _convert_pdf_ultra_high_res(self, upload_id: int, pdf_path: str, db: Session) -> Dict[str, Any]:
        """1단계: 초고해상도 PDF 변환 (DPI 600, 안전한 여백 크로핑)"""
        try:
            print(f"Converting PDF to ultra-high resolution images (DPI 600)...")
            
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # 초고해상도 설정 (DPI 600 = scale_factor 8.33)
            scale_factor = 8.33
            mat = fitz.Matrix(scale_factor, scale_factor)
            
            page_images = []
            
            for page_num in range(total_pages):
                page = doc[page_num]
                
                # 초고해상도 렌더링
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # 안전한 여백 크로핑 (상하좌우 2% 여백 유지)
                width, height = img.size
                crop_margin_x = int(width * 0.02)
                crop_margin_y = int(height * 0.02)
                
                # 크로핑 영역 계산 (실제 내용 영역 감지)
                np_img = np.array(img.convert('L'))
                
                # 상하 여백 감지
                row_sums = np.sum(np_img < 250, axis=1)  # 텍스트가 있는 행
                content_rows = np.where(row_sums > width * 0.01)[0]  # 최소 1% 폭에 텍스트
                
                if len(content_rows) > 0:
                    top_bound = max(0, content_rows[0] - crop_margin_y)
                    bottom_bound = min(height, content_rows[-1] + crop_margin_y)
                else:
                    top_bound, bottom_bound = crop_margin_y, height - crop_margin_y
                
                # 좌우 여백 감지
                col_sums = np.sum(np_img < 250, axis=0)
                content_cols = np.where(col_sums > height * 0.01)[0]
                
                if len(content_cols) > 0:
                    left_bound = max(0, content_cols[0] - crop_margin_x)
                    right_bound = min(width, content_cols[-1] + crop_margin_x)
                else:
                    left_bound, right_bound = crop_margin_x, width - crop_margin_x
                
                # 안전 크로핑 적용
                cropped_img = img.crop((left_bound, top_bound, right_bound, bottom_bound))
                
                # 이미지 저장
                page_path = self.temp_dir / f"page_{upload_id}_{page_num:03d}_ultra.png"
                cropped_img.save(page_path, "PNG", quality=100, optimize=False)
                
                page_images.append({
                    'page_number': page_num + 1,
                    'image_path': str(page_path),
                    'original_size': (width, height),
                    'cropped_size': cropped_img.size,
                    'crop_bounds': (left_bound, top_bound, right_bound, bottom_bound)
                })
                
                print(f"Page {page_num+1}/{total_pages} processed (Ultra-high DPI)")
            
            doc.close()
            
            return {
                'success': True,
                'page_images': page_images,
                'total_pages': total_pages,
                'dpi': 600,
                'processing_note': 'Ultra-high resolution with safe margin cropping'
            }
            
        except Exception as e:
            logger.error(f"초고해상도 변환 오류: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _detect_and_process_columns(self, upload_id: int, high_res_result: Dict, db: Session) -> Dict[str, Any]:
        """2단계: 컬럼 감지 및 2열 처리"""
        try:
            print(f"Detecting columns and processing 2-column layouts...")
            
            page_images = high_res_result['page_images']
            column_processed_pages = []
            
            for page_info in page_images:
                img_path = page_info['image_path']
                img = Image.open(img_path)
                
                # OpenCV로 컬럼 감지
                np_img = np.array(img.convert('L'))
                
                # 세로 투영을 통한 컬럼 경계 감지
                height, width = np_img.shape
                vertical_projection = np.sum(np_img < 240, axis=0)  # 텍스트 영역
                
                # 컬럼 분할점 찾기 (가운데 영역에서 빈 공간 찾기)
                center_start = int(width * 0.4)
                center_end = int(width * 0.6)
                center_projection = vertical_projection[center_start:center_end]
                
                # 최소값 위치 찾기 (컬럼 사이 빈 공간)
                if len(center_projection) > 0:
                    min_idx = np.argmin(center_projection)
                    split_point = center_start + min_idx
                    
                    # 컬럼 분할 임계값 체크
                    if center_projection[min_idx] < np.mean(vertical_projection) * 0.1:
                        # 2컬럼으로 감지됨
                        left_column = img.crop((0, 0, split_point, height))
                        right_column = img.crop((split_point, 0, width, height))
                        
                        # 각 컬럼을 개별 이미지로 저장
                        left_path = self.temp_dir / f"page_{upload_id}_{page_info['page_number']:03d}_left.png"
                        right_path = self.temp_dir / f"page_{upload_id}_{page_info['page_number']:03d}_right.png"
                        
                        left_column.save(left_path, "PNG")
                        right_column.save(right_path, "PNG")
                        
                        column_processed_pages.append({
                            'page_number': page_info['page_number'],
                            'layout': '2-column',
                            'left_column': str(left_path),
                            'right_column': str(right_path),
                            'split_point': split_point
                        })
                        
                        print(f"Page {page_info['page_number']}: 2-column layout detected")
                    else:
                        # 단일 컬럼
                        column_processed_pages.append({
                            'page_number': page_info['page_number'],
                            'layout': '1-column',
                            'full_image': img_path
                        })
                        print(f"Page {page_info['page_number']}: single column layout")
                else:
                    column_processed_pages.append({
                        'page_number': page_info['page_number'],
                        'layout': '1-column',
                        'full_image': img_path
                    })
            
            return {
                'success': True,
                'column_pages': column_processed_pages,
                'two_column_count': len([p for p in column_processed_pages if p['layout'] == '2-column']),
                'single_column_count': len([p for p in column_processed_pages if p['layout'] == '1-column'])
            }
            
        except Exception as e:
            logger.error(f"컬럼 감지 오류: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _detect_and_stitch_cross_page(self, upload_id: int, column_result: Dict, db: Session) -> Dict[str, Any]:
        """3단계: 크로스페이지 연결 감지 및 자동 스티칭"""
        try:
            print(f"Detecting and stitching cross-page questions...")
            
            column_pages = column_result['column_pages']
            stitched_results = []
            cross_page_pairs = []
            
            # GPT Vision으로 각 페이지/컬럼을 텍스트로 변환
            page_texts = []
            for page_info in column_pages:
                if page_info['layout'] == '2-column':
                    # 좌측 컬럼 처리
                    left_text = await self._convert_image_to_text(page_info['left_column'])
                    page_texts.append({
                        'page_number': page_info['page_number'],
                        'column': 'left',
                        'text': left_text,
                        'image_path': page_info['left_column']
                    })
                    
                    # 우측 컬럼 처리
                    right_text = await self._convert_image_to_text(page_info['right_column'])
                    page_texts.append({
                        'page_number': page_info['page_number'],
                        'column': 'right', 
                        'text': right_text,
                        'image_path': page_info['right_column']
                    })
                else:
                    # 단일 컬럼 처리
                    full_text = await self._convert_image_to_text(page_info['full_image'])
                    page_texts.append({
                        'page_number': page_info['page_number'],
                        'column': 'full',
                        'text': full_text,
                        'image_path': page_info['full_image']
                    })
            
            # 크로스페이지 패턴 감지 및 스티칭
            for i, current_page in enumerate(page_texts):
                if i < len(page_texts) - 1:  # 마지막 페이지가 아닌 경우
                    next_page = page_texts[i + 1]
                    
                    # 현재 페이지 끝에서 미완료 문제 감지
                    current_text = current_page['text']
                    next_text = next_page['text']
                    
                    # 미완료 문제 패턴 감지
                    incomplete_pattern = await self._detect_incomplete_question(current_text)
                    if incomplete_pattern:
                        # 다음 페이지에서 연결 부분 찾기
                        continuation = await self._find_question_continuation(next_text, incomplete_pattern)
                        if continuation:
                            # 스티칭 수행
                            stitched_question = await self._stitch_cross_page_question(
                                current_text, next_text, incomplete_pattern, continuation
                            )
                            
                            cross_page_pairs.append({
                                'start_page': current_page['page_number'],
                                'end_page': next_page['page_number'],
                                'question_number': incomplete_pattern.get('question_number'),
                                'stitched_content': stitched_question
                            })
                            
                            print(f"Cross-page question detected: Q{incomplete_pattern.get('question_number')} "
                                  f"(Page {current_page['page_number']} → {next_page['page_number']})")
                
                # 스티칭되지 않은 페이지는 원본 텍스트 유지
                stitched_results.append(current_page)
            
            return {
                'success': True,
                'page_texts': page_texts,
                'stitched_results': stitched_results,
                'cross_page_pairs': cross_page_pairs,
                'cross_page_count': len(cross_page_pairs)
            }
            
        except Exception as e:
            logger.error(f"크로스페이지 스티칭 오류: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _convert_image_to_text(self, image_path: str) -> str:
        """GPT Vision으로 이미지를 텍스트로 변환"""
        try:
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "이 이미지에 포함된 모든 텍스트를 정확히 추출해주세요. 문제 번호, 문제 텍스트, 선택지, 표, 그림 설명 등을 모두 포함하여 마크다운 형식으로 출력해주세요."
                            },
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
                max_tokens=4000,
                temperature=0
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"이미지 텍스트 변환 오류: {str(e)}")
            return ""

    async def _detect_incomplete_question(self, text: str) -> Optional[Dict]:
        """텍스트에서 미완료 문제 패턴 감지"""
        try:
            # Claude로 미완료 문제 감지 (향상된 프롬프트 사용)
            prompt = EnhancedPrompts.get_cross_page_detection_prompt()
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": f"""{prompt}

분석할 텍스트 (마지막 1000자):
{text[-1000:]}"""
                    }
                ]
            )
            
            try:
                result = json.loads(response.content[0].text)
                if result.get('incomplete_detected'):
                    return result
            except:
                pass
                
            return None
            
        except Exception as e:
            logger.error(f"미완료 문제 감지 오류: {str(e)}")
            return None

    async def _find_question_continuation(self, text: str, incomplete_pattern: Dict) -> Optional[Dict]:
        """다음 페이지에서 문제 연결 부분 찾기"""
        try:
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": f"""이전 페이지에서 미완료로 끝난 문제의 연결 부분을 찾아주세요:

미완료 문제 정보:
- 문제 번호: {incomplete_pattern.get('question_number')}
- 미완료 타입: {incomplete_pattern.get('incomplete_type')}
- 마지막 내용: {incomplete_pattern.get('last_content')}

현재 페이지 텍스트 (처음 1000자):
{text[:1000]}

JSON 형식으로 응답:
{{"continuation_found": true/false, "continuation_text": "연결되는 텍스트", "continuation_type": "choices/text/table"}}"""
                    }
                ]
            )
            
            try:
                result = json.loads(response.content[0].text)
                if result.get('continuation_found'):
                    return result
            except:
                pass
                
            return None
            
        except Exception as e:
            logger.error(f"문제 연결 부분 찾기 오류: {str(e)}")
            return None

    async def _stitch_cross_page_question(self, current_text: str, next_text: str, 
                                        incomplete_pattern: Dict, continuation: Dict) -> str:
        """크로스페이지 문제 스티칭"""
        try:
            prompt = EnhancedPrompts.get_cross_page_stitching_prompt()
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": f"""{prompt}

첫 번째 페이지 (미완료 부분):
{incomplete_pattern.get('last_content')}

두 번째 페이지 (연결 부분):
{continuation.get('continuation_text')}"""
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"문제 스티칭 오류: {str(e)}")
            return ""

    async def _extract_choices_with_ocr(self, upload_id: int, stitching_result: Dict, db: Session) -> Dict[str, Any]:
        """4단계: OCR 기반 선택지 추출 (LLM 생성 대신)"""
        try:
            print(f"Extracting choices using OCR-based regex patterns...")
            
            page_texts = stitching_result['page_texts']
            ocr_extracted_questions = []
            
            for page_text_info in page_texts:
                text = page_text_info['text']
                
                # 문제 번호별로 텍스트 분할
                question_blocks = re.split(r'\n(?=\d+\.)', text)
                
                for block in question_blocks:
                    if not block.strip():
                        continue
                        
                    # 문제 번호 추출
                    question_num_match = re.search(r'^(\d+)\.', block.strip())
                    if not question_num_match:
                        continue
                        
                    question_number = int(question_num_match.group(1))
                    
                    # OCR 기반 선택지 추출
                    choices = []
                    for i, pattern in enumerate(self.choice_patterns, 1):
                        match = re.search(pattern, block, re.DOTALL)
                        if match:
                            choice_text = match.group(1).strip()
                            if choice_text:
                                choices.append({
                                    'number': i,
                                    'symbol': ['①', '②', '③', '④', '⑤'][i-1],
                                    'text': choice_text
                                })
                    
                    # 문제 텍스트 추출 (선택지 제외)
                    question_text = re.sub(r'①.*?(?=\n\d+\.|$)', '', block, flags=re.DOTALL).strip()
                    question_text = re.sub(r'^(\d+\.\s*)', '', question_text).strip()
                    
                    if question_text and len(choices) >= 2:  # 최소 2개 선택지 있어야 유효
                        ocr_extracted_questions.append({
                            'question_number': question_number,
                            'question_text': question_text,
                            'choices': choices,
                            'page_number': page_text_info['page_number'],
                            'extraction_method': 'ocr_regex',
                            'choice_count': len(choices)
                        })
                        
                        print(f"OCR extracted: Q{question_number} with {len(choices)} choices")
            
            return {
                'success': True,
                'questions': ocr_extracted_questions,
                'total_questions': len(ocr_extracted_questions),
                'extraction_method': 'ocr_regex_based'
            }
            
        except Exception as e:
            logger.error(f"OCR 선택지 추출 오류: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _process_assets_pipeline(self, upload_id: int, ocr_result: Dict, db: Session) -> Dict[str, Any]:
        """5단계: 에셋 파이프라인 (표, 그림, 코드)"""
        try:
            print(f"Processing assets (tables, figures, code blocks)...")
            
            questions = ocr_result['questions']
            processed_questions = []
            assets = []
            
            for question in questions:
                question_text = question['question_text']
                
                # 표 감지 및 처리
                if '|' in question_text or '표' in question_text or 'table' in question_text.lower():
                    table_asset = await self._process_table_asset(question_text, question['question_number'])
                    if table_asset:
                        assets.append(table_asset)
                        question['has_table'] = True
                        question['table_asset_id'] = table_asset['asset_id']
                
                # 그림 감지 및 처리  
                if '그림' in question_text or 'figure' in question_text.lower() or '도' in question_text:
                    figure_asset = await self._process_figure_asset(question_text, question['question_number'])
                    if figure_asset:
                        assets.append(figure_asset)
                        question['has_figure'] = True
                        question['figure_asset_id'] = figure_asset['asset_id']
                
                # 코드 감지 및 처리
                if '코드' in question_text or 'code' in question_text.lower() or '```' in question_text:
                    code_asset = await self._process_code_asset(question_text, question['question_number'])
                    if code_asset:
                        assets.append(code_asset)
                        question['has_code'] = True
                        question['code_asset_id'] = code_asset['asset_id']
                
                processed_questions.append(question)
            
            print(f"Assets processed: {len(assets)} total assets")
            
            return {
                'success': True,
                'questions': processed_questions,
                'assets': assets,
                'asset_summary': {
                    'tables': len([a for a in assets if a['type'] == 'table']),
                    'figures': len([a for a in assets if a['type'] == 'figure']),
                    'code_blocks': len([a for a in assets if a['type'] == 'code'])
                }
            }
            
        except Exception as e:
            logger.error(f"에셋 파이프라인 오류: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _process_table_asset(self, question_text: str, question_number: int) -> Optional[Dict]:
        """표 에셋 처리"""
        try:
            # 표 내용 추출 및 구조화 (향상된 프롬프트 사용)
            prompt = EnhancedPrompts.get_asset_extraction_prompt("table")
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": f"""{prompt}

분석할 문제 텍스트:
{question_text}"""
                    }
                ]
            )
            
            table_html = response.content[0].text
            
            return {
                'asset_id': f"table_q{question_number}",
                'type': 'table',
                'question_number': question_number,
                'content': table_html,
                'display_format': 'html'
            }
            
        except Exception as e:
            logger.error(f"표 에셋 처리 오류: {str(e)}")
            return None

    async def _process_figure_asset(self, question_text: str, question_number: int) -> Optional[Dict]:
        """그림 에셋 처리"""
        try:
            # 그림 설명 추출
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": f"""다음 문제에서 그림/도표 설명을 추출해주세요:

{question_text}

출력 형식: 그림 설명만 간결하게 출력"""
                    }
                ]
            )
            
            figure_description = response.content[0].text
            
            return {
                'asset_id': f"figure_q{question_number}",
                'type': 'figure',
                'question_number': question_number,
                'content': figure_description,
                'display_format': 'description'
            }
            
        except Exception as e:
            logger.error(f"그림 에셋 처리 오류: {str(e)}")
            return None

    async def _process_code_asset(self, question_text: str, question_number: int) -> Optional[Dict]:
        """코드 에셋 처리"""
        try:
            # 코드 블록 추출
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": f"""다음 문제에서 코드 부분을 추출하여 구문 강조가 가능한 형식으로 만들어주세요:

{question_text}

출력 형식: ```언어
코드 내용
```"""
                    }
                ]
            )
            
            code_content = response.content[0].text
            
            return {
                'asset_id': f"code_q{question_number}",
                'type': 'code',
                'question_number': question_number,
                'content': code_content,
                'display_format': 'code_block'
            }
            
        except Exception as e:
            logger.error(f"코드 에셋 처리 오류: {str(e)}")
            return None