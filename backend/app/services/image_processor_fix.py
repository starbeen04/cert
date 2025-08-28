"""
이미지 처리 로직 수정 - 선택지 011 문제 해결
"""

import re
from typing import List, Dict, Any

class ImageProcessorFix:
    """이미지 처리 문제 해결 전용 클래스"""
    
    @staticmethod
    def fix_choice_image_references(questions: List[Dict[str, Any]], upload_id: int) -> List[Dict[str, Any]]:
        """선택지의 이상한 이미지 참조 패턴 수정"""
        
        fixed_questions = []
        
        for question in questions:
            if not question.get('options'):
                fixed_questions.append(question)
                continue
                
            # 선택지 수정
            fixed_options = []
            for option in question['options']:
                if not option:
                    continue
                    
                option_str = str(option)
                
                # 🚨 문제 패턴들 수정
                fixed_option = option_str
                
                # 1. "선택지 011", "선택지 012" 패턴 수정
                if re.match(r'선택지 \d{3}', fixed_option):
                    # 번호 추출
                    match = re.search(r'선택지 (\d{3})', fixed_option)
                    if match:
                        img_num = match.group(1)
                        fixed_option = f"![IMG_{img_num}](/images/upload_{upload_id}/IMG_{img_num}.png)"
                
                # 2. "IMG_XXX_IMAGE" 패턴을 올바른 마크다운으로 수정  
                fixed_option = re.sub(
                    r'IMG_(\d{3})_IMAGE', 
                    rf'![IMG_\1](/images/upload_{upload_id}/IMG_\1.png)',
                    fixed_option
                )
                
                # 3. "DIAGRAM_IMAGE" 패턴 수정
                if 'DIAGRAM_IMAGE' in fixed_option:
                    fixed_option = re.sub(
                        r'DIAGRAM_IMAGE',
                        f'![IMG_DIAGRAM](/images/upload_{upload_id}/IMG_DIAGRAM.png)',
                        fixed_option
                    )
                
                # 4. 빈 선택지나 무의미한 선택지 제거
                if fixed_option.strip() in ['', '...', 'NULL', 'null', 'None']:
                    continue
                
                # 5. 선택지 번호 정리 (①②③④⑤가 없으면 추가)
                if not re.match(r'^[①②③④⑤]', fixed_option.strip()):
                    option_number = len(fixed_options) + 1
                    if option_number <= 5:
                        circles = ['①', '②', '③', '④', '⑤']
                        fixed_option = f"{circles[option_number-1]} {fixed_option.strip()}"
                
                fixed_options.append(fixed_option)
            
            # 업데이트된 문제 추가
            updated_question = question.copy()
            updated_question['options'] = fixed_options
            
            # 선택지 개수 검증
            if len(fixed_options) >= 2:  # 최소 2개 이상
                updated_question['choice_fix_applied'] = True
                updated_question['original_choice_count'] = len(question.get('options', []))
                updated_question['fixed_choice_count'] = len(fixed_options)
                fixed_questions.append(updated_question)
            else:
                # 선택지가 부족하면 불완전 표시
                updated_question['incomplete_choices'] = True
                updated_question['choice_fix_failed'] = True
                fixed_questions.append(updated_question)
        
        return fixed_questions
    
    @staticmethod
    def validate_image_paths(questions: List[Dict[str, Any]], upload_id: int) -> Dict[str, Any]:
        """이미지 경로 유효성 검증"""
        import os
        
        validation_result = {
            'valid_images': [],
            'invalid_images': [],
            'total_image_references': 0,
            'valid_percentage': 0.0
        }
        
        image_base_path = f"C:/cert_fast/backend/static/images/upload_{upload_id}"
        
        for question in questions:
            if not question.get('options'):
                continue
                
            for option in question.get('options', []):
                if not option:
                    continue
                    
                # ![IMG_XXX] 패턴 찾기
                img_matches = re.findall(r'!\[IMG_(\d+)\]', str(option))
                
                for img_num in img_matches:
                    validation_result['total_image_references'] += 1
                    
                    # 실제 파일 존재 확인
                    possible_files = [
                        f"{image_base_path}/IMG_{img_num}.png",
                        f"{image_base_path}/IMG_{img_num}.jpg", 
                        f"{image_base_path}/IMG_{img_num}.jpeg"
                    ]
                    
                    file_exists = any(os.path.exists(path) for path in possible_files)
                    
                    if file_exists:
                        validation_result['valid_images'].append(img_num)
                    else:
                        validation_result['invalid_images'].append(img_num)
        
        # 유효성 비율 계산
        if validation_result['total_image_references'] > 0:
            validation_result['valid_percentage'] = (
                len(validation_result['valid_images']) / 
                validation_result['total_image_references']
            ) * 100
            
        return validation_result
    
    @staticmethod
    def generate_processing_report(original_questions: List[Dict], fixed_questions: List[Dict], upload_id: int) -> str:
        """처리 결과 리포트 생성"""
        
        report = f"""
🔧 **이미지 처리 수정 리포트 - Upload {upload_id}**
═══════════════════════════════════════════════════════════

📊 **처리 결과**:
- 원본 문제 수: {len(original_questions)}개
- 수정된 문제 수: {len(fixed_questions)}개
- 수정 적용 문제: {len([q for q in fixed_questions if q.get('choice_fix_applied')])}개
- 수정 실패 문제: {len([q for q in fixed_questions if q.get('choice_fix_failed')])}개

🎯 **주요 수정 사항**:
"""
        
        # 수정된 문제들 분석
        fixed_count = 0
        pattern_fixes = {
            'choice_011_pattern': 0,
            'img_xxx_image_pattern': 0,
            'diagram_image_pattern': 0,
            'empty_choice_removal': 0
        }
        
        for question in fixed_questions:
            if question.get('choice_fix_applied'):
                fixed_count += 1
                
                # 어떤 패턴이 수정되었는지 확인
                original_options = str(original_questions[question.get('question_number', 1)-1].get('options', []))
                
                if '선택지 0' in original_options:
                    pattern_fixes['choice_011_pattern'] += 1
                if 'IMG_' in original_options and '_IMAGE' in original_options:
                    pattern_fixes['img_xxx_image_pattern'] += 1
                if 'DIAGRAM_IMAGE' in original_options:
                    pattern_fixes['diagram_image_pattern'] += 1
        
        report += f"""
- ✅ "선택지 011" 패턴 수정: {pattern_fixes['choice_011_pattern']}개
- ✅ "IMG_XXX_IMAGE" 패턴 수정: {pattern_fixes['img_xxx_image_pattern']}개  
- ✅ "DIAGRAM_IMAGE" 패턴 수정: {pattern_fixes['diagram_image_pattern']}개
- ✅ 빈 선택지 제거: {pattern_fixes['empty_choice_removal']}개

🏆 **최종 결과**:
- 정상 처리율: {(fixed_count/len(fixed_questions)*100):.1f}%
- 이미지 참조 정리 완료
- 마크다운 이미지 문법 적용 완료
"""
        
        return report