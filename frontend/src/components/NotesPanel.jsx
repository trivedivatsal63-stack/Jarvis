import React, { useState, useEffect, useCallback } from 'react'

const API_URL = '/api/notes'

export default function NotesPanel() {
  const [notes, setNotes] = useState([])
  const [selected, setSelected] = useState(null)
  const [searchQ, setSearchQ] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const [newTitle, setNewTitle] = useState('')
  const [newContent, setNewContent] = useState('')
  const [newTags, setNewTags] = useState('')

  const fetchNotes = useCallback(async (q) => {
    setLoading(true)
    setError(null)
    try {
      const url = q && q.trim() ? `${API_URL}/search?q=${encodeURIComponent(q)}` : API_URL
      const res = await fetch(url)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setNotes(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchNotes()
  }, [fetchNotes])

  useEffect(() => {
    if (!searchQ.trim()) {
      fetchNotes()
    }
  }, [searchQ, fetchNotes])

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchQ.trim()) fetchNotes(searchQ)
  }

  const handleSave = async () => {
    if (!newTitle.trim() || !newContent.trim()) return
    setSaving(true)
    setError(null)
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newTitle,
          content: newContent,
          tags: newTags.split(',').map((t) => t.trim()).filter(Boolean),
        }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setNewTitle('')
      setNewContent('')
      setNewTags('')
      await fetchNotes(searchQ)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleUpdate = async () => {
    if (!selected || !selected.title.trim() || !selected.content.trim()) return
    setSaving(true)
    setError(null)
    try {
      const res = await fetch(`${API_URL}/${selected.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: selected.title,
          content: selected.content,
          tags: selected.tags || [],
        }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await fetchNotes(searchQ)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!selected) return
    setDeleting(true)
    setError(null)
    try {
      const res = await fetch(`${API_URL}/${selected.id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setSelected(null)
      await fetchNotes(searchQ)
    } catch (e) {
      setError(e.message)
    } finally {
      setDeleting(false)
    }
  }

  const formatDate = (d) => {
    if (!d) return ''
    const dt = new Date(d)
    return dt.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
  }

  const noteCardStyle = (isSelected) => ({
    padding: '8px 10px',
    background: isSelected ? 'rgba(0,212,255,0.08)' : 'rgba(0,212,255,0.02)',
    borderLeft: `2px solid ${isSelected ? 'rgba(0,212,255,0.5)' : 'rgba(0,212,255,0.15)'}`,
    borderRadius: '3px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    marginBottom: '6px',
  })

  const inputStyle = {
    width: '100%',
    background: 'rgba(0,212,255,0.04)',
    border: '1px solid rgba(0,212,255,0.12)',
    borderRadius: '3px',
    color: '#e0e8f0',
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '11px',
    padding: '6px 8px',
    outline: 'none',
    marginBottom: '6px',
  }

  const btnStyle = (color = '#00d4ff') => ({
    background: `rgba(0,212,255,0.08)`,
    border: `1px solid ${color}`,
    color,
    fontFamily: "'Orbitron', monospace",
    fontSize: '9px',
    letterSpacing: '2px',
    padding: '5px 12px',
    cursor: 'pointer',
    borderRadius: '2px',
    transition: 'all 0.2s',
  })

  const tagStyle = {
    display: 'inline-block',
    fontSize: '9px',
    color: '#00ff9d',
    background: 'rgba(0,255,157,0.08)',
    border: '1px solid rgba(0,255,157,0.15)',
    borderRadius: '2px',
    padding: '1px 5px',
    marginRight: '4px',
    fontFamily: "'Share Tech Mono', monospace",
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="panel-header">
        <span className="panel-dot" />
        NOTES
      </div>

      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '4px', marginBottom: '8px' }}>
        <input
          style={{ ...inputStyle, marginBottom: 0 }}
          placeholder="Search notes..."
          value={searchQ}
          onChange={(e) => setSearchQ(e.target.value)}
        />
        <button type="submit" style={{ ...btnStyle(), flexShrink: 0, padding: '5px 8px' }}>
          GO
        </button>
      </form>

      {error && (
        <div style={{ fontSize: '10px', color: '#ff4444', fontFamily: "'Share Tech Mono', monospace", marginBottom: '6px' }}>
          {error}
        </div>
      )}

      <div style={{ padding: '8px 0', borderBottom: '1px solid rgba(0,212,255,0.08)', marginBottom: '8px' }}>
        <input
          style={inputStyle}
          placeholder="Title"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
        />
        <textarea
          style={{ ...inputStyle, minHeight: '50px', resize: 'vertical' }}
          placeholder="Content"
          value={newContent}
          onChange={(e) => setNewContent(e.target.value)}
        />
        <input
          style={inputStyle}
          placeholder="Tags (comma separated)"
          value={newTags}
          onChange={(e) => setNewTags(e.target.value)}
        />
        <button
          style={btnStyle('#00ff9d')}
          onClick={handleSave}
          disabled={saving || !newTitle.trim() || !newContent.trim()}
        >
          {saving ? 'SAVING...' : 'SAVE'}
        </button>
      </div>

      {selected && (
        <div style={{
          padding: '10px',
          background: 'rgba(0,212,255,0.03)',
          border: '1px solid rgba(0,212,255,0.12)',
          borderRadius: '3px',
          marginBottom: '8px',
        }}>
          <input
            style={inputStyle}
            value={selected.title}
            onChange={(e) => setSelected({ ...selected, title: e.target.value })}
          />
          <textarea
            style={{ ...inputStyle, minHeight: '80px', resize: 'vertical' }}
            value={selected.content}
            onChange={(e) => setSelected({ ...selected, content: e.target.value })}
          />
          <input
            style={inputStyle}
            value={(selected.tags || []).join(', ')}
            onChange={(e) => setSelected({ ...selected, tags: e.target.value.split(',').map((t) => t.trim()).filter(Boolean) })}
          />
          <div style={{ display: 'flex', gap: '6px' }}>
            <button style={btnStyle('#00d4ff')} onClick={handleUpdate} disabled={saving}>
              {saving ? 'UPDATING...' : 'UPDATE'}
            </button>
            <button style={btnStyle('#ff4444')} onClick={handleDelete} disabled={deleting}>
              {deleting ? 'DELETING...' : 'DELETE'}
            </button>
          </div>
        </div>
      )}

      <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
        {loading && (
          <div style={{ fontSize: '10px', color: '#666', fontFamily: "'Share Tech Mono', monospace", textAlign: 'center', padding: '12px 0' }}>
            LOADING...
          </div>
        )}
        {!loading && notes.length === 0 && (
          <div style={{ fontSize: '11px', color: '#666', fontFamily: "'Share Tech Mono', monospace", textAlign: 'center', padding: '12px 0' }}>
            No notes yet, Sir.
          </div>
        )}
        {notes.map((note) => (
          <div
            key={note.id}
            style={noteCardStyle(selected && selected.id === note.id)}
            onClick={() => setSelected(note)}
          >
            <div style={{
              fontFamily: "'Orbitron', monospace",
              fontSize: '10px',
              color: '#00d4ff',
              letterSpacing: '1px',
              marginBottom: '3px',
            }}>
              {note.title}
            </div>
            <div style={{
              fontSize: '10px',
              color: '#888',
              lineHeight: '1.3',
              marginBottom: '4px',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}>
              {note.content && note.content.length > 100 ? note.content.substring(0, 100) + '...' : note.content}
            </div>
            <div style={{ marginBottom: '3px' }}>
              {(note.tags || []).map((tag, i) => (
                <span key={i} style={tagStyle}>{tag}</span>
              ))}
            </div>
            <div style={{ fontSize: '8px', color: '#555', fontFamily: "'Share Tech Mono', monospace" }}>
              {formatDate(note.created_at || note.updated_at)}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
