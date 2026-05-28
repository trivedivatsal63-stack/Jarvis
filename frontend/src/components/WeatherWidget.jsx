import React, { useState, useEffect } from 'react'

const ICONS = {
  '01d': '\u2600\uFE0F', '01n': '\uD83C\uDF19',
  '02d': '\u26C5', '02n': '\u26C5',
  '03d': '\u2601\uFE0F', '03n': '\u2601\uFE0F',
  '04d': '\u2601\uFE0F', '04n': '\u2601\uFE0F',
  '09d': '\uD83C\uDF27\uFE0F', '09n': '\uD83C\uDF27\uFE0F',
  '10d': '\uD83C\uDF26\uFE0F', '10n': '\uD83C\uDF26\uFE0F',
  '11d': '\u26C8\uFE0F', '11n': '\u26C8\uFE0F',
  '13d': '\u2744\uFE0F', '13n': '\u2744\uFE0F',
  '50d': '\uD83C\uDF2B\uFE0F', '50n': '\uD83C\uDF2B\uFE0F',
}

const API_URL = `/api/weather`

export default function WeatherWidget() {
  const [weather, setWeather] = useState(null)
  const [error, setError] = useState(false)

  const fetchWeather = () => {
    setError(false)
    fetch(API_URL + '?city=London')
      .then((r) => r.json())
      .then((d) => { if (d && d.temp) setWeather(d); else setError(true) })
      .catch(() => setError(true))
  }

  useEffect(() => { fetchWeather() }, [])

  if (error) {
    return (
      <div className="weather-widget">
        <div className="panel-header"><span className="panel-dot" />WEATHER</div>
        <div className="weather-error" onClick={fetchWeather}>API key needed</div>
      </div>
    )
  }
  if (!weather) {
    return (
      <div className="weather-widget">
        <div className="panel-header"><span className="panel-dot" />WEATHER</div>
        <div className="weather-loading">Loading...</div>
      </div>
    )
  }

  return (
    <div className="weather-widget">
      <div className="panel-header"><span className="panel-dot" />WEATHER</div>
      <div className="weather-main">
        <span className="weather-icon">{ICONS[weather.icon] || '\u2600\uFE0F'}</span>
        <div>
          <div className="weather-temp">{weather.temp}\u00B0C</div>
          <div className="weather-city">{weather.city}, {weather.country}</div>
        </div>
      </div>
      <div className="weather-details">
        <span>{weather.description}</span>
        <span>Humidity: {weather.humidity}%</span>
        <span>Wind: {weather.wind_speed} m/s</span>
      </div>
    </div>
  )
}
