import { describe, it, expect } from 'vitest'
import { countWords, formatProcessingTime, cn, toPrintableHtml } from '@/lib/utils'

describe('countWords', () => {
  it('counts words in a string', () => {
    expect(countWords('Hello World')).toBe(2)
  })

  it('handles empty string', () => {
    expect(countWords('')).toBe(0)
  })

  it('handles multiple spaces', () => {
    expect(countWords('one  two   three')).toBe(3)
  })

  it('handles single word', () => {
    expect(countWords('word')).toBe(1)
  })

  it('handles newlines and tabs', () => {
    expect(countWords('word1\nword2\tword3')).toBe(3)
  })
})

describe('formatProcessingTime', () => {
  it('formats milliseconds under 1000', () => {
    expect(formatProcessingTime(500)).toBe('500ms')
  })

  it('formats seconds for 1000ms and above', () => {
    expect(formatProcessingTime(1500)).toBe('1.5s')
  })

  it('rounds milliseconds', () => {
    expect(formatProcessingTime(499.7)).toBe('500ms')
  })

  it('formats exactly 1 second', () => {
    expect(formatProcessingTime(1000)).toBe('1.0s')
  })
})

describe('cn (className utility)', () => {
  it('merges class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })

  it('handles conditional classes', () => {
    const isActive = true
    const isInactive = false
    expect(cn('base', isActive && 'active', isInactive && 'inactive')).toBe('base active')
  })

  it('handles undefined values', () => {
    expect(cn('base', undefined)).toBe('base')
  })

  it('deduplicates tailwind classes', () => {
    // tailwind-merge should handle conflicting classes
    const result = cn('text-red-500', 'text-blue-500')
    expect(result).toBe('text-blue-500')
  })
})

describe('toPrintableHtml', () => {
  it('escapes HTML-sensitive characters', () => {
    expect(toPrintableHtml('<script>alert("x")</script>')).toBe(
      '&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;'
    )
  })

  it('preserves line breaks for printing', () => {
    expect(toPrintableHtml('line 1\nline 2')).toBe('line 1<br>line 2')
  })
})
