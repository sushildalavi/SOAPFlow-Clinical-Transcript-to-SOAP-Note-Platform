import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api } from '@/lib/api'

// Mock fetch globally
const mockFetch = vi.fn()
globalThis.fetch = mockFetch as typeof fetch

function mockResponse(data: unknown, ok = true, status = 200) {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(data),
  } as Response)
}

beforeEach(() => {
  mockFetch.mockReset()
})

describe('api.health', () => {
  it('uses the local backend docs URL by default', () => {
    expect(api.docsUrl()).toBe('http://localhost:8000/docs')
  })

  it('returns health response', async () => {
    const mockData = {
      status: 'ok',
      version: '1.0.0',
      generation_mode: 'demo',
      openai_configured: false,
      anthropic_configured: false,
    }
    mockFetch.mockReturnValueOnce(mockResponse(mockData))
    const result = await api.health()
    expect(result.status).toBe('ok')
    expect(result.generation_mode).toBe('demo')
  })

  it('throws on non-ok response', async () => {
    mockFetch.mockReturnValueOnce(mockResponse({ detail: 'Server error' }, false, 500))
    await expect(api.health()).rejects.toThrow('Server error')
  })
})

describe('api.generate', () => {
  it('posts transcript to /generate', async () => {
    const mockData = {
      success: true,
      soap_note: {
        subjective: 'Test S',
        objective: 'Test O',
        assessment: 'Test A',
        plan: 'Test P',
      },
      warnings: [],
      metadata: {
        model: 'demo-rule-based',
        mode: 'demo',
        transcript_word_count: 10,
        transcript_char_count: 50,
        note_word_count: 20,
        processing_time_ms: 5.0,
        sections_populated: 4,
      },
    }
    mockFetch.mockReturnValueOnce(mockResponse(mockData))
    const result = await api.generate('Doctor: Hi\nPatient: Headache.')
    expect(result.success).toBe(true)
    expect(result.soap_note.subjective).toBe('Test S')
  })

  it('includes mode in request when provided', async () => {
    mockFetch.mockReturnValueOnce(mockResponse({ success: true, soap_note: {}, warnings: [], metadata: {} }))
    await api.generate('some transcript', 'demo')
    const [, options] = mockFetch.mock.calls[0] as [RequestInfo | URL, RequestInit]
    const body = JSON.parse(String(options.body))
    expect(body.mode).toBe('demo')
  })
})

describe('api.listHistory', () => {
  it('returns note list response', async () => {
    const mockData = { success: true, total: 2, notes: [] }
    mockFetch.mockReturnValueOnce(mockResponse(mockData))
    const result = await api.listHistory()
    expect(result.total).toBe(2)
    expect(Array.isArray(result.notes)).toBe(true)
  })
})

describe('api.saveNote', () => {
  it('posts to /history endpoint', async () => {
    const mockRecord = {
      id: 1,
      title: 'Test Note',
      transcript: 'Doctor: Hi',
      soap_note: { subjective: '', objective: '', assessment: '', plan: '' },
      metadata: { model: 'demo', mode: 'demo' },
      warnings: [],
      created_at: new Date().toISOString(),
    }
    mockFetch.mockReturnValueOnce(mockResponse(mockRecord, true, 201))
    const result = await api.saveNote({
      transcript: 'Doctor: Hi',
      soap_note: { subjective: '', objective: '', assessment: '', plan: '' },
    })
    expect(result.id).toBe(1)
    expect(result.title).toBe('Test Note')
  })
})

describe('api.deleteNote', () => {
  it('handles empty responses', async () => {
    mockFetch.mockReturnValueOnce(
      Promise.resolve({
        ok: true,
        status: 204,
        json: () => Promise.reject(new Error('no body')),
      } as Response)
    )

    await expect(api.deleteNote(1)).resolves.toBeUndefined()
  })
})
