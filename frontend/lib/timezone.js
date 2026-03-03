export const TIMEZONE_OPTIONS = [
  { label: 'UTC-8', value: '-8' },
  { label: 'UTC-7', value: '-7' },
  { label: 'UTC-6', value: '-6' },
  { label: 'UTC-5', value: '-5' },
  { label: 'UTC-4', value: '-4' },
  { label: 'UTC-3', value: '-3' },
  { label: 'UTC-2', value: '-2' },
  { label: 'UTC-1', value: '-1' },
  { label: 'UTC+0', value: '0' },
  { label: 'UTC+1', value: '1' },
  { label: 'UTC+2', value: '2' },
  { label: 'UTC+3', value: '3' },
  { label: 'UTC+4', value: '4' },
  { label: 'UTC+5', value: '5' },
  { label: 'UTC+6', value: '6' },
  { label: 'UTC+7', value: '7' },
  { label: 'UTC+8', value: '8' },
]

export const DEFAULT_TIMEZONE = '0'

export const LOCALSTORAGE_KEY = 'rendlog-timezone'

/**
 * Format a UTC timestamp applying a manual hour offset.
 * Supabase returns naive timestamps (no Z suffix), so we force UTC parsing
 * and then apply the offset manually to avoid browser local-timezone interference.
 *
 * @param {string} timestamp - ISO 8601 timestamp (may lack timezone suffix)
 * @param {string} offsetStr - Hour offset as string, e.g. '-6', '0', '3'
 * @param {{ includeDate?: boolean, includeSeconds?: boolean }} options
 */
export function formatTime(timestamp, offsetStr, options = {}) {
  if (!timestamp) return '--'
  const { includeDate = false, includeSeconds = false } = options

  // Ensure the timestamp is parsed as UTC
  let iso = String(timestamp).trim()
  if (!iso.endsWith('Z') && !iso.includes('+') && !/\d{2}-\d{2}:\d{2}$/.test(iso)) {
    iso += 'Z'
  }

  const offsetHours = Number(offsetStr) || 0
  const adjusted = new Date(new Date(iso).getTime() + offsetHours * 3_600_000)

  const fmt = { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }
  if (includeDate) {
    fmt.day = '2-digit'
    fmt.month = '2-digit'
  }
  if (includeSeconds) {
    fmt.second = '2-digit'
  }

  return adjusted.toLocaleString('es-ES', fmt)
}
