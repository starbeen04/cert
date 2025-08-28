import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import localizedFormat from 'dayjs/plugin/localizedFormat'

dayjs.extend(relativeTime)
dayjs.extend(localizedFormat)

/**
 * Format date to a readable string
 */
export const formatDate = (date: string | Date): string => {
  return dayjs(date).format('MMM DD, YYYY')
}

/**
 * Format date and time to a readable string
 */
export const formatDateTime = (date: string | Date): string => {
  return dayjs(date).format('MMM DD, YYYY HH:mm')
}

/**
 * Format date to relative time (e.g., "2 hours ago")
 */
export const formatRelativeTime = (date: string | Date): string => {
  return dayjs(date).fromNow()
}

/**
 * Format file size in bytes to human readable format
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * Format number with thousand separators
 */
export const formatNumber = (num: number | undefined | null): string => {
  if (num === undefined || num === null || isNaN(num)) {
    return '0'
  }
  return new Intl.NumberFormat().format(num)
}

/**
 * Format percentage
 */
export const formatPercentage = (value: number, decimals = 1): string => {
  return `${(value * 100).toFixed(decimals)}%`
}

/**
 * Safe currency formatting
 */
export const formatCurrency = (value: number | undefined | null, decimals = 2): string => {
  if (value === undefined || value === null || isNaN(value)) {
    return '$0.' + '0'.repeat(decimals)
  }
  return `$${value.toFixed(decimals)}`
}

/**
 * Safe number formatting with decimal places
 */
export const safeToFixed = (value: number | undefined | null, decimals = 2): string => {
  if (value === undefined || value === null || isNaN(value)) {
    return '0.' + '0'.repeat(decimals)
  }
  return value.toFixed(decimals)
}

/**
 * Truncate text to specified length
 */
export const truncateText = (text: string, length: number): string => {
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

/**
 * Format duration in seconds to human readable format
 */
export const formatDuration = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds}s`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`
  }
}

/**
 * Capitalize first letter of string
 */
export const capitalize = (str: string): string => {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}

/**
 * Convert camelCase to Title Case
 */
export const camelToTitle = (str: string): string => {
  return str
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase())
}

/**
 * Format API error message
 */
export const formatErrorMessage = (error: any): string => {
  if (typeof error === 'string') {
    return error
  }
  
  if (error?.response?.data?.detail) {
    return error.response.data.detail
  }
  
  if (error?.message) {
    return error.message
  }
  
  return 'An unexpected error occurred'
}