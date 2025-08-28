/**
 * Enhanced Passage Formatter - 표, 그림, 코드 등 에셋 렌더링 지원
 * GPT Enhanced PDF Processor의 에셋 파이프라인과 연동
 */

/**
 * 향상된 지문 포맷팅 - HTML 테이블, 코드 블록, 그림 설명 지원
 * @param {string} passage - 원본 지문 텍스트
 * @param {Array} assets - 에셋 배열 (표, 그림, 코드)
 * @returns {string} 포맷된 HTML 문자열
 */
export function formatPassageEnhanced(passage, assets = []) {
  if (!passage) return ''
  
  let formatted = passage
  
  // 1. HTML 테이블 처리 (에셋에서 제공된 경우)
  const tableAssets = assets.filter(asset => asset.type === 'table')
  tableAssets.forEach((tableAsset, index) => {
    const tableId = `table_${tableAsset.asset_id || index}`
    if (formatted.includes(`[TABLE_${tableAsset.question_number}]`) || 
        formatted.includes('표') || 
        formatted.includes('|')) {
      // 기존 표 마커를 HTML 테이블로 교체
      formatted = formatted.replace(
        new RegExp(`\\[TABLE_${tableAsset.question_number}\\]|\\|[^\\n]*\\|`, 'g'),
        `<div class="table-container" id="${tableId}">${tableAsset.content}</div>`
      )
    }
  })
  
  // 2. 기본 파이프 테이블 처리 (에셋이 없는 경우)
  if (!tableAssets.length && formatted.includes('|')) {
    formatted = formatPipeTable(formatted)
  }
  
  // 3. 코드 블록 처리
  const codeAssets = assets.filter(asset => asset.type === 'code')
  codeAssets.forEach((codeAsset, index) => {
    const codeId = `code_${codeAsset.asset_id || index}`
    if (formatted.includes(`[CODE_${codeAsset.question_number}]`) ||
        formatted.includes('```')) {
      // 코드 마커를 하이라이트된 코드로 교체
      formatted = formatted.replace(
        new RegExp(`\\[CODE_${codeAsset.question_number}\\]|```[\\s\\S]*?````, 'g'),
        `<div class="code-container" id="${codeId}">
          <pre><code class="language-${detectLanguage(codeAsset.content)}">${escapeHtml(codeAsset.content)}</code></pre>
        </div>`
      )
    }
  })
  
  // 4. 그림 설명 처리
  const figureAssets = assets.filter(asset => asset.type === 'figure')
  figureAssets.forEach((figureAsset, index) => {
    const figureId = `figure_${figureAsset.asset_id || index}`
    if (formatted.includes(`[FIGURE_${figureAsset.question_number}]`) ||
        formatted.includes('그림') ||
        formatted.includes('도표')) {
      // 그림 마커를 그림 설명으로 교체
      formatted = formatted.replace(
        new RegExp(`\\[FIGURE_${figureAsset.question_number}\\]`, 'g'),
        `<div class="figure-container" id="${figureId}">
          <div class="figure-description">
            <div class="figure-header">
              <i class="el-icon-picture"></i>
              <span class="figure-title">${figureAsset.title || '그림'}</span>
            </div>
            <div class="figure-content">${figureAsset.content}</div>
          </div>
        </div>`
      )
    }
  })
  
  // 5. 일반 텍스트 처리
  formatted = formatGeneralText(formatted)
  
  return formatted
}

/**
 * 파이프 구분자 테이블을 HTML 테이블로 변환
 * @param {string} text - 파이프가 포함된 텍스트
 * @returns {string} HTML 테이블이 포함된 텍스트
 */
function formatPipeTable(text) {
  const lines = text.split('\n')
  let result = []
  let inTable = false
  let tableRows = []
  
  lines.forEach(line => {
    const trimmedLine = line.trim()
    
    // 테이블 행인지 확인 (최소 2개의 파이프 필요)
    if (trimmedLine.includes('|') && (trimmedLine.match(/\|/g) || []).length >= 2) {
      if (!inTable) {
        inTable = true
        tableRows = []
      }
      
      // 파이프로 분할하여 셀 생성
      const cells = trimmedLine.split('|').map(cell => cell.trim()).filter(cell => cell)
      if (cells.length > 0) {
        tableRows.push(cells)
      }
    } else {
      // 테이블이 끝났으면 HTML로 변환
      if (inTable && tableRows.length > 0) {
        result.push(convertToHtmlTable(tableRows))
        tableRows = []
        inTable = false
      }
      
      if (trimmedLine) {
        result.push(line)
      }
    }
  })
  
  // 마지막 테이블 처리
  if (inTable && tableRows.length > 0) {
    result.push(convertToHtmlTable(tableRows))
  }
  
  return result.join('\n')
}

/**
 * 테이블 행 배열을 HTML 테이블로 변환
 * @param {Array<Array<string>>} rows - 테이블 행 배열
 * @returns {string} HTML 테이블 문자열
 */
function convertToHtmlTable(rows) {
  if (rows.length === 0) return ''
  
  let html = '<table class="exam-table">'
  
  // 첫 번째 행을 헤더로 처리
  if (rows.length > 0) {
    html += '<thead><tr>'
    rows[0].forEach(cell => {
      html += `<th>${escapeHtml(cell)}</th>`
    })
    html += '</tr></thead>'
  }
  
  // 나머지 행을 데이터로 처리
  if (rows.length > 1) {
    html += '<tbody>'
    for (let i = 1; i < rows.length; i++) {
      html += '<tr>'
      rows[i].forEach(cell => {
        html += `<td>${escapeHtml(cell)}</td>`
      })
      html += '</tr>'
    }
    html += '</tbody>'
  }
  
  html += '</table>'
  return html
}

/**
 * 일반 텍스트 포맷팅 (줄바꿈, 강조 등)
 * @param {string} text - 원본 텍스트
 * @returns {string} 포맷된 HTML
 */
function formatGeneralText(text) {
  let formatted = text
  
  // 줄바꿈 처리
  formatted = formatted.replace(/\n/g, '<br>')
  
  // 강조 표시 (**텍스트** -> <strong>텍스트</strong>)
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  
  // 기울임 (*텍스트* -> <em>텍스트</em>)
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>')
  
  // 밑줄 (__텍스트__ -> <u>텍스트</u>)
  formatted = formatted.replace(/__(.*?)__/g, '<u>$1</u>')
  
  // 선택지 기호 강화
  formatted = formatted.replace(/([①②③④⑤])/g, '<span class="choice-symbol">$1</span>')
  
  return formatted
}

/**
 * 코드 언어 감지
 * @param {string} code - 코드 내용
 * @returns {string} 언어 식별자
 */
function detectLanguage(code) {
  if (!code) return 'text'
  
  // 간단한 언어 감지 로직
  if (code.includes('function') && code.includes('{')) return 'javascript'
  if (code.includes('def ') && code.includes(':')) return 'python'
  if (code.includes('class ') && code.includes('public')) return 'java'
  if (code.includes('#include') || code.includes('int main')) return 'cpp'
  if (code.includes('<!DOCTYPE') || code.includes('<html>')) return 'html'
  if (code.includes('SELECT') || code.includes('FROM')) return 'sql'
  
  return 'text'
}

/**
 * HTML 이스케이프
 * @param {string} text - 이스케이프할 텍스트
 * @returns {string} 이스케이프된 텍스트
 */
function escapeHtml(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

/**
 * 기존 formatPassage 함수와 호환성 유지
 * @param {string} passage - 지문 텍스트
 * @returns {string} 포맷된 HTML
 */
export function formatPassage(passage) {
  return formatPassageEnhanced(passage, [])
}

/**
 * 에셋 존재 여부 확인 함수들
 */
export function hasTable(question) {
  const additionalInfo = parseAdditionalInfo(question.additional_info)
  return additionalInfo?.has_table || 
         additionalInfo?.table_asset_id ||
         question.passage?.includes('|') || 
         question.passage?.includes('표')
}

export function hasCode(question) {
  const additionalInfo = parseAdditionalInfo(question.additional_info)
  return additionalInfo?.has_code || 
         additionalInfo?.code_asset_id ||
         question.passage?.includes('class') || 
         question.passage?.includes('function') ||
         question.passage?.includes('```')
}

export function hasFigure(question) {
  const additionalInfo = parseAdditionalInfo(question.additional_info)
  return additionalInfo?.has_figure || 
         additionalInfo?.figure_asset_id ||
         question.passage?.includes('그림') || 
         question.passage?.includes('도표') ||
         question.passage?.includes('Figure')
}

function parseAdditionalInfo(additionalInfo) {
  try {
    return typeof additionalInfo === 'string' ? JSON.parse(additionalInfo) : additionalInfo
  } catch {
    return {}
  }
}