// Simple in-memory + file-backed cache for analysis results
// For production, a real DB should be used, but this works for demo/small scale
const fs = require('fs');
const path = require('path');

const CACHE_FILE = path.join(__dirname, 'analysisCache.json');
let cache = {};

// Load cache from disk on startup
try {
  if (fs.existsSync(CACHE_FILE)) {
    cache = JSON.parse(fs.readFileSync(CACHE_FILE, 'utf-8'));
  }
} catch (e) {
  cache = {};
}

function getKey(model, price, trend, rsi) {
  // Key by model and rounded inputs
  return `${model}:${Math.round(price)}:${trend}:${Math.round(rsi)}`;
}

function getCachedAnalysis(model, price, trend, rsi) {
  const key = getKey(model, price, trend, rsi);
  const entry = cache[key];
  if (entry && Date.now() - entry.timestamp < 10 * 60 * 1000) {
    return entry.analysis;
  }
  return null;
}

function setCachedAnalysis(model, price, trend, rsi, analysis) {
  const key = getKey(model, price, trend, rsi);
  cache[key] = { analysis, timestamp: Date.now() };
  fs.writeFileSync(CACHE_FILE, JSON.stringify(cache, null, 2));
}

module.exports = { getCachedAnalysis, setCachedAnalysis };
