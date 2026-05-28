import React, { useState, useEffect } from 'react'

const API_URL = `/api/news`

export default function NewsWidget() {
  const [articles, setArticles] = useState([])
  const [error, setError] = useState(false)

  const fetchNews = () => {
    setError(false)
    fetch(API_URL + '?query=general')
      .then((r) => r.json())
      .then((d) => {
        if (d.articles && Array.isArray(d.articles) && d.articles.length) {
          setArticles(d.articles.slice(0, 3))
        } else {
          setError(true)
        }
      })
      .catch(() => setError(true))
  }

  useEffect(() => { fetchNews() }, [])

  return (
    <div className="news-widget">
      <div className="panel-header">
        <span className="panel-dot" />
        HEADLINES
        <button className="news-refresh" onClick={fetchNews} title="Refresh">\u21BB</button>
      </div>
      {error ? (
        <div className="news-error" onClick={fetchNews}>API key needed \u2014 click to retry</div>
      ) : articles.length === 0 ? (
        <div className="news-loading">Loading...</div>
      ) : (
        <div className="news-list">
          {articles.map((a, i) => (
            <div key={i} className="news-item">
              <div className="news-title">{a.title}</div>
              <div className="news-source">{a.source}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
