import React from 'react'

const dotKeyframes = `
@keyframes searchDot {
  0%, 20% { opacity: 0; }
  50% { opacity: 1; }
  80%, 100% { opacity: 0; }
}
`

export default function SearchResultsCard({ results, query, type, onDeepResearch }) {
  const containerStyle = {
    background: 'rgba(0,212,255,0.02)',
    border: '1px solid rgba(0,212,255,0.08)',
    borderLeft: '3px solid #00d4ff',
    borderRadius: '4px',
    padding: '14px 16px',
    marginBottom: '12px',
  }

  const headerStyle = {
    fontFamily: "'Orbitron', monospace",
    fontSize: '11px',
    letterSpacing: '2px',
    color: '#00d4ff',
    marginBottom: '12px',
    textShadow: '0 0 8px rgba(0,212,255,0.2)',
  }

  const titleStyle = {
    fontSize: '13px',
    color: '#c0d8e0',
    cursor: 'pointer',
    textDecoration: 'none',
    transition: 'color 0.15s',
    marginBottom: '2px',
    display: 'block',
  }

  const snippetStyle = {
    fontSize: '11px',
    color: '#777',
    lineHeight: '1.4',
    display: '-webkit-box',
    WebkitLineClamp: 2,
    WebkitBoxOrient: 'vertical',
    overflow: 'hidden',
  }

  const sourceStyle = {
    fontSize: '9px',
    color: '#555',
    fontFamily: "'Share Tech Mono', monospace",
    marginTop: '4px',
  }

  const dividerStyle = {
    height: '1px',
    background: 'rgba(0,212,255,0.06)',
    margin: '8px 0',
  }

  const btnStyle = {
    background: 'rgba(0,212,255,0.08)',
    border: '1px solid rgba(0,212,255,0.2)',
    color: '#00d4ff',
    fontFamily: "'Orbitron', monospace",
    fontSize: '9px',
    letterSpacing: '2px',
    padding: '6px 14px',
    cursor: 'pointer',
    borderRadius: '2px',
    marginTop: '10px',
    transition: 'all 0.2s',
  }

  const handleResultClick = (url) => {
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  if (!query) return null

  if (type === 'images') {
    return (
      <div style={containerStyle}>
        <style>{dotKeyframes}</style>
        <div style={headerStyle}>SEARCH: {query}</div>
        {!results || results.length === 0 ? (
          <div style={{ fontSize: '11px', color: '#666', fontFamily: "'Share Tech Mono', monospace", padding: '12px 0' }}>
            No results found, Sir.
          </div>
        ) : (
          <>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '8px',
            }}>
              {results.map((item, i) => (
                <div
                  key={i}
                  style={{
                    cursor: 'pointer',
                    borderRadius: '3px',
                    overflow: 'hidden',
                    border: '1px solid rgba(0,212,255,0.08)',
                    background: 'rgba(0,212,255,0.02)',
                  }}
                  onClick={() => handleResultClick(item.url)}
                >
                  <img
                    src={item.thumbnail || item.url}
                    alt={item.title || ''}
                    style={{ width: '100%', height: '80px', objectFit: 'cover', display: 'block' }}
                    onError={(e) => { e.target.style.display = 'none' }}
                  />
                  <div style={{ padding: '4px 6px', fontSize: '9px', color: '#999', fontFamily: "'Share Tech Mono', monospace" }}>
                    {item.title || 'Image'}
                  </div>
                </div>
              ))}
            </div>
            {onDeepResearch && (
              <button
                style={btnStyle}
                onMouseEnter={(e) => { e.target.style.background = 'rgba(0,212,255,0.15)' }}
                onMouseLeave={(e) => { e.target.style.background = 'rgba(0,212,255,0.08)' }}
                onClick={() => onDeepResearch(query)}
              >
                DEEP RESEARCH
              </button>
            )}
          </>
        )}
      </div>
    )
  }

  if (type === 'videos') {
    return (
      <div style={containerStyle}>
        <style>{dotKeyframes}</style>
        <div style={headerStyle}>SEARCH: {query}</div>
        {!results || results.length === 0 ? (
          <div style={{ fontSize: '11px', color: '#666', fontFamily: "'Share Tech Mono', monospace", padding: '12px 0' }}>
            No results found, Sir.
          </div>
        ) : (
          <>
            {results.map((item, i) => (
              <div key={i}>
                {i > 0 && <div style={dividerStyle} />}
                <div
                  style={{ display: 'flex', gap: '10px', cursor: 'pointer', padding: '4px 0' }}
                  onClick={() => handleResultClick(item.url)}
                >
                  <div style={{ position: 'relative', flexShrink: 0 }}>
                    <img
                      src={item.thumbnail}
                      alt={item.title || ''}
                      style={{ width: '80px', height: '54px', objectFit: 'cover', borderRadius: '3px', display: 'block' }}
                      onError={(e) => { e.target.style.display = 'none' }}
                    />
                    {item.duration && (
                      <div style={{
                        position: 'absolute',
                        bottom: '2px',
                        right: '2px',
                        background: 'rgba(0,0,0,0.75)',
                        color: '#e0e8f0',
                        fontSize: '9px',
                        fontFamily: "'Share Tech Mono', monospace",
                        padding: '1px 4px',
                        borderRadius: '2px',
                      }}>
                        {item.duration}
                      </div>
                    )}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={titleStyle}
                      onMouseEnter={(e) => { e.target.style.color = '#00d4ff' }}
                      onMouseLeave={(e) => { e.target.style.color = '#c0d8e0' }}
                    >
                      {item.title}
                    </div>
                    {item.snippet && <div style={snippetStyle}>{item.snippet}</div>}
                    <div style={sourceStyle}>{item.source || ''}</div>
                  </div>
                </div>
              </div>
            ))}
            {onDeepResearch && (
              <button
                style={btnStyle}
                onMouseEnter={(e) => { e.target.style.background = 'rgba(0,212,255,0.15)' }}
                onMouseLeave={(e) => { e.target.style.background = 'rgba(0,212,255,0.08)' }}
                onClick={() => onDeepResearch(query)}
              >
                DEEP RESEARCH
              </button>
            )}
          </>
        )}
      </div>
    )
  }

  return (
    <div style={containerStyle}>
      <style>{dotKeyframes}</style>
      <div style={headerStyle}>SEARCH: {query}</div>

      {results === null || results === undefined ? (
        <div style={{ fontSize: '11px', color: '#666', fontFamily: "'Share Tech Mono', monospace", padding: '12px 0' }}>
          SEARCHING
          <span style={{ animation: 'searchDot 1.4s infinite', opacity: 0 }}>.</span>
          <span style={{ animation: 'searchDot 1.4s infinite', animationDelay: '0.2s', opacity: 0 }}>.</span>
          <span style={{ animation: 'searchDot 1.4s infinite', animationDelay: '0.4s', opacity: 0 }}>.</span>
        </div>
      ) : results.length === 0 ? (
        <div style={{ fontSize: '11px', color: '#666', fontFamily: "'Share Tech Mono', monospace", padding: '12px 0' }}>
          No results found, Sir.
        </div>
      ) : (
        <>
          {results.map((item, i) => (
            <div key={i}>
              {i > 0 && <div style={dividerStyle} />}
              <div
                style={{ cursor: 'pointer' }}
                onClick={() => handleResultClick(item.url)}
              >
                <div
                  style={titleStyle}
                  onMouseEnter={(e) => { e.target.style.color = '#00d4ff' }}
                  onMouseLeave={(e) => { e.target.style.color = '#c0d8e0' }}
                >
                  {item.title}
                </div>
                {item.snippet && <div style={snippetStyle}>{item.snippet}</div>}
                <div style={sourceStyle}>{item.source || item.url}</div>
              </div>
            </div>
          ))}
          {onDeepResearch && (
            <button
              style={btnStyle}
              onMouseEnter={(e) => { e.target.style.background = 'rgba(0,212,255,0.15)' }}
              onMouseLeave={(e) => { e.target.style.background = 'rgba(0,212,255,0.08)' }}
              onClick={() => onDeepResearch(query)}
            >
              DEEP RESEARCH
            </button>
          )}
        </>
      )}
    </div>
  )
}
