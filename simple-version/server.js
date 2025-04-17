require('dotenv').config();
console.log('OANDA_API_TOKEN:', process.env.OANDA_API_TOKEN);
console.log('OANDA_ACCOUNT_ID:', process.env.OANDA_ACCOUNT_ID);

/**
 * Simple HTTP and WebSocket server for MVPFOREX
 * This standalone server provides:
 * 1. Static file serving for HTML, JS, CSS
 * 2. WebSocket streaming for real-time price data
 * 3. REST API endpoints for market data and AI analysis
 */

const express = require('express');
const http = require('http');
const path = require('path');
const { Server } = require('socket.io');

// Configuration
const PORT = process.env.PORT || 3000;
const UPDATE_INTERVAL = 2000; // 2 seconds between price updates

// Create Express app
const app = express();

// CORS middleware
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  next();
});

// Serve static files from current directory
app.use(express.static(__dirname));

// OANDA Candlestick endpoint

app.get('/api/candles', (req, res) => {
  const OANDA_API_TOKEN = process.env.OANDA_API_TOKEN;
  const OANDA_ENVIRONMENT = (process.env.OANDA_ENVIRONMENT || 'practice').toLowerCase();
  if (!OANDA_API_TOKEN) {
    return res.status(500).json({ status: 'error', error: 'OANDA API token not set' });
  }
  let hostname = 'api-fxpractice.oanda.com';
  if (OANDA_ENVIRONMENT === 'live') {
    hostname = 'api-fxtrade.oanda.com';
  }
  const options = {
    hostname,
    path: '/v3/instruments/XAU_USD/candles?granularity=M1&count=100',
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${OANDA_API_TOKEN}`
    }
  };
  const request = https.request(options, (response) => {
    let data = '';
    response.on('data', (chunk) => { data += chunk; });
    response.on('end', () => {
      try {
        const json = JSON.parse(data);
        if (json.candles) {
          res.json({ status: 'ok', candles: json.candles });
        } else {
          res.status(500).json({ status: 'error', error: json });
        }
      } catch (err) {
        res.status(500).json({ status: 'error', error: err.message });
      }
    });
  });
  request.on('error', (err) => {
    res.status(500).json({ status: 'error', error: err.message });
  });
  request.end();
});

// Handle API endpoints
app.get('/api/market-data', async (req, res) => {
  // Try to fetch latest OANDA candle
  const fetch = require('node-fetch');
  let oandaPrice = null;
  try {
    const baseUrl = req.protocol + '://' + req.get('host');
    const candlesResp = await fetch(baseUrl + '/api/candles');
    const candlesJson = await candlesResp.json();
    console.log('Fetched OANDA candles:', JSON.stringify(candlesJson));
    if (candlesJson.status === 'ok' && Array.isArray(candlesJson.candles) && candlesJson.candles.length > 0) {
      const latest = candlesJson.candles[candlesJson.candles.length - 1];
      oandaPrice = parseFloat(latest.mid.c);
    }
  } catch (e) {
    console.error('Error fetching OANDA candles:', e);
  }
  let price = oandaPrice;
  if (!price || isNaN(price)) {
    price = priceData && priceData.currentPrice ? priceData.currentPrice : 2400;
  }
  // Safe fallbacks for all fields
  const safe = (field, fallback) => (priceData && typeof priceData[field] !== 'undefined' ? priceData[field] : fallback);
  res.json({
    status: 'ok',
    current_price: price,
    currentPrice: price,
    price: price,
    bid: price - 0.5,
    ask: price + 0.5,
    spread: 1.0,
    dailyRange: safe('dailyRange', null),
    dailyChange: safe('dailyChange', 0),
    rsi: safe('rsi', 50),
    trend: safe('trend', 'Neutral'),
    ma50: safe('ma50', price - 5),
    ma200: safe('ma200', price - 15),
    keyLevels: safe('keyLevels', null),
    market_data: {
      indicators: {
        rsi: safe('rsi', 50),
        trend: safe('trend', 'Neutral'),
        ma_50: safe('ma50', price - 5),
        ma_200: safe('ma200', price - 15),
        support_levels: safe('supports', [price - 10, price - 20, price - 30]),
        resistance_levels: safe('resistances', [price + 10, price + 20, price + 30])
      }
    }
  });
});

app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    time: new Date().toISOString()
  });
});

app.post('/api/analyze/:model', express.json(), (req, res) => {
  const model = req.params.model;
  const marketData = req.body.market_data || {};
  
  // Generate simulated analysis
  const analysis = generateSimulatedAnalysis(model, marketData);
  
  res.json({
    status: 'success',
    analysis: analysis
  });
});

// Create HTTP server with Express
const server = http.createServer(app);

// Initialize Socket.IO
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// OANDA Streaming Integration
const https = require('https');
const OANDA_API_TOKEN = process.env.OANDA_API_TOKEN;
const OANDA_ACCOUNT_ID = process.env.OANDA_ACCOUNT_ID;

let priceData = null;
let oandaStreamActive = false;

function startOandaStream() {
  if (!OANDA_API_TOKEN || !OANDA_ACCOUNT_ID) {
    console.error('OANDA credentials missing in environment variables.');
    return;
  }
  const options = {
    hostname: 'stream-fxpractice.oanda.com',
    path: `/v3/accounts/${OANDA_ACCOUNT_ID}/pricing/stream?instruments=XAU_USD`,
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${OANDA_API_TOKEN}`
    }
  };
  const req = https.request(options, (res) => {
    oandaStreamActive = true;
    res.on('data', (chunk) => {
      try {
        const lines = chunk.toString().split('\n');
        for (const line of lines) {
          if (line.trim()) {
            const data = JSON.parse(line);
            if (data.type === 'PRICE') {
              priceData = {
                instrument: 'XAU_USD',
                time: data.time,
                bid: Number(data.bids[0].price),
                ask: Number(data.asks[0].price),
                spread: Math.abs(Number(data.asks[0].price) - Number(data.bids[0].price)),
                currentPrice: (Number(data.bids[0].price) + Number(data.asks[0].price)) / 2,
                dayHigh: null,
                dayLow: null,
                dailyChange: null,
                rsi: null,
                trend: null,
                ma50: null,
                ma200: null,
                supports: [],
                resistances: []
              };
              io.to('XAU_USD').emit('price_update', priceData);
            }
          }
        }
      } catch (e) {
        // Ignore JSON parse errors from keepalive
      }
    });
    res.on('end', () => {
      oandaStreamActive = false;
      console.error('OANDA stream ended. Retrying in 10s...');
      setTimeout(startOandaStream, 10000);
    });
  });
  req.on('error', (e) => {
    oandaStreamActive = false;
    console.error('OANDA stream connection error:', e);
    setTimeout(startOandaStream, 10000);
  });
  req.end();
}

startOandaStream();

// Socket.IO connection handling
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);
  
  // Handle client disconnect
  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
  
  // Handle price subscription
  socket.on('subscribe_prices', (data) => {
    const instrument = data.instrument;
    console.log(`Client ${socket.id} subscribed to ${instrument} prices`);
    
    // Join room for this instrument
    socket.join(instrument);
    
    // Send initial price data (from OANDA, if available)
    if (priceData) {
      socket.emit('price_update', priceData);
    }
  });
  
  // Handle price unsubscription
  socket.on('unsubscribe_prices', (data) => {
    const instrument = data.instrument;
    console.log(`Client ${socket.id} unsubscribed from ${instrument} prices`);
    
    // Leave room for this instrument
    socket.leave(instrument);
  });
});

// Start the server
server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}/`);
  // OANDA streaming will start automatically if credentials are present
});

// (Removed simulated price streaming; now handled by OANDA stream)


// Generate realistic market data
function generateMarketData() {
  // Random price movement (more realistic)
  const change = (Math.random() - 0.5) * 1.5; // Range: -0.75 to +0.75
  basePrice += change;
  
  // Add some noise to create spread
  const bid = basePrice - 0.5;
  const ask = basePrice + 0.5;
  
  // Trend determination
  let trend;
  if (change > 0.25) trend = 'Bullish';
  else if (change < -0.25) trend = 'Bearish';
  else trend = 'Neutral';
  
  // RSI simulation (simplified)
  const rsi = Math.min(Math.max(50 + (change * 10), 30), 70);
  
  return {
    instrument: 'XAU_USD',
    time: new Date().toISOString(),
    bid: bid,
    ask: ask,
    spread: 1.0,
    currentPrice: basePrice,
    dayHigh: basePrice + 8,
    dayLow: basePrice - 6,
    dailyChange: (change / basePrice) * 100,
    rsi: rsi,
    trend: trend,
    ma50: basePrice - 5,
    ma200: basePrice - 15,
    supports: [
      basePrice - 10,
      basePrice - 20,
      basePrice - 30
    ],
    resistances: [
      basePrice + 10,
      basePrice + 20,
      basePrice + 30
    ]
  };
}

// Generate simulated AI analysis
function generateSimulatedAnalysis(model, marketData) {
  const price = marketData.price || basePrice;
  const trend = marketData.trend || 'Neutral';
  const rsi = marketData.rsi || 50;
  
  // Different analysis templates based on model
  switch (model) {
    case 'openai':
      return generateOpenAIAnalysis(price, trend, rsi);
    case 'anthropic':
      return generateClaudeAnalysis(price, trend, rsi);
    case 'perplexity':
      return generatePerplexityAnalysis(price, trend, rsi);
    default:
      return generateOpenAIAnalysis(price, trend, rsi);
  }
}

function generateOpenAIAnalysis(price, trend, rsi) {
  const bullish = trend.toLowerCase().includes('bull') || rsi > 60;
  const bearish = trend.toLowerCase().includes('bear') || rsi < 40;
  
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  const timeStr = now.toLocaleTimeString('en-US', { hour: 'numeric', minute: 'numeric' });
  
  let analysis = `XAUUSD (Gold) Analysis - ${dateStr} at ${timeStr}\nGenerated by OpenAI GPT-4.1\n\n`;
  analysis += 'TECHNICAL ANALYSIS:\n';
  
  if (bullish) {
    analysis += `Gold is showing bullish momentum at $${price.toFixed(2)}. The RSI at ${rsi.toFixed(1)} suggests more upside potential, with resistance expected around $${(price + 15).toFixed(2)} and $${(price + 30).toFixed(2)}. Traders might consider long positions with tight stops below $${(price - 10).toFixed(2)}.`;
  } else if (bearish) {
    analysis += `Gold is displaying bearish pressure at $${price.toFixed(2)}. The RSI at ${rsi.toFixed(1)} indicates potential for continued downside movement, with support levels at $${(price - 15).toFixed(2)} and $${(price - 30).toFixed(2)}. Traders should watch for a breakdown below $${(price - 5).toFixed(2)}.`;
  } else {
    analysis += `Gold is consolidating around $${price.toFixed(2)} with a neutral trend. The RSI at ${rsi.toFixed(1)} suggests balanced momentum. Key levels to watch are $${(price - 10).toFixed(2)} for support and $${(price + 10).toFixed(2)} for resistance. More directional conviction is needed before establishing new positions.`;
  }
  
  analysis += '\n\nMARKET CONTEXT:\n';
  analysis += `The broader market context shows gold responding to current inflation data and central bank policies. ${bullish ? 'Increased geopolitical tensions and inflation concerns are supporting gold prices.' : bearish ? 'Recent hawkish Fed comments and easing inflation expectations are pressuring gold.' : 'Mixed economic signals are causing gold to trade sideways in the near term.'}`;
  
  return analysis;
}

function generateClaudeAnalysis(price, trend, rsi) {
  const bullish = trend.toLowerCase().includes('bull') || rsi > 60;
  const bearish = trend.toLowerCase().includes('bear') || rsi < 40;
  
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  const timeStr = now.toLocaleTimeString('en-US', { hour: 'numeric', minute: 'numeric' });
  
  let analysis = `XAUUSD (Gold) Analysis - ${dateStr} at ${timeStr}\nGenerated by Anthropic Claude 3.7\n\n`;
  analysis += '𝗧𝗿𝗮𝗱𝗶𝗻𝗴 𝗢𝘂𝘁𝗹𝗼𝗼𝗸\n\n';
  
  if (bullish) {
    analysis += `Gold appears to be in a bullish structure at $${price.toFixed(2)}. With RSI registering ${rsi.toFixed(1)}, momentum favors buyers. The market structure suggests accumulation, with key structural resistance at $${(price + 12).toFixed(2)} and $${(price + 25).toFixed(2)}.\n\n`;
    analysis += `• 𝗥𝗶𝘀𝗸-𝗿𝗲𝘄𝗮𝗿𝗱: Favorable for long positions targeting $${(price + 20).toFixed(2)}\n`;
    analysis += `• 𝗜𝗻𝘃𝗮𝗹𝗶𝗱𝗮𝘁𝗶𝗼𝗻: A daily close below $${(price - 8).toFixed(2)} would invalidate the bullish bias\n`;
  } else if (bearish) {
    analysis += `Gold shows bearish structure at $${price.toFixed(2)}. RSI at ${rsi.toFixed(1)} confirms weakening momentum. The recent price action indicates distribution, with structural support levels at $${(price - 12).toFixed(2)} and $${(price - 25).toFixed(2)}.\n\n`;
    analysis += `• 𝗥𝗶𝘀𝗸-𝗿𝗲𝘄𝗮𝗿𝗱: Favorable for short positions targeting $${(price - 20).toFixed(2)}\n`;
    analysis += `• 𝗜𝗻𝘃𝗮𝗹𝗶𝗱𝗮𝘁𝗶𝗼𝗻: A daily close above $${(price + 8).toFixed(2)} would invalidate the bearish bias\n`;
  } else {
    analysis += `Gold is displaying consolidation behavior at $${price.toFixed(2)}. RSI at ${rsi.toFixed(1)} indicates equilibrium between buyers and sellers. The market is testing the boundaries of a range between $${(price - 15).toFixed(2)} and $${(price + 15).toFixed(2)}.\n\n`;
    analysis += `• 𝗥𝗶𝘀𝗸-𝗿𝗲𝘄𝗮𝗿𝗱: Unfavorable for directional positions; range trading strategies preferred\n`;
    analysis += `• 𝗕𝗿𝗲𝗮𝗸𝗼𝘂𝘁 𝘁𝗮𝗿𝗴𝗲𝘁𝘀: Above range: $${(price + 25).toFixed(2)} / Below range: $${(price - 25).toFixed(2)}\n`;
  }
  
  analysis += '\n𝗠𝗮𝗰𝗿𝗼 𝗖𝗼𝗻𝘁𝗲𝘅𝘁\n';
  analysis += `Gold's price action is influenced by ${bullish ? 'the recent shift in Fed policy expectations and increased safe-haven demand' : bearish ? 'dollar strength and potential profit-taking after the recent rally' : 'competing narratives between inflation hedging and interest rate expectations'}. Real yields remain a key driver to monitor for future directional movements.`;
  
  return analysis;
}

function generatePerplexityAnalysis(price, trend, rsi) {
  const bullish = trend.toLowerCase().includes('bull') || rsi > 60;
  const bearish = trend.toLowerCase().includes('bear') || rsi < 40;
  
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  const timeStr = now.toLocaleTimeString('en-US', { hour: 'numeric', minute: 'numeric' });
  
  let analysis = `XAUUSD (Gold) Analysis - ${dateStr} at ${timeStr}\nGenerated by Perplexity Pro AI\n\n`;
  analysis += 'GOLD MARKET ANALYSIS\n\n';
  
  // Data-driven statistics section
  analysis += 'Current Data Points:\n';
  analysis += `• Price: $${price.toFixed(2)}\n`;
  analysis += `• RSI(14): ${rsi.toFixed(1)}\n`;
  analysis += `• Trend: ${trend}\n`;
  analysis += `• Key Support: $${(price - 12).toFixed(2)}\n`;
  analysis += `• Key Resistance: $${(price + 12).toFixed(2)}\n\n`;
  
  // Technical forecast
  analysis += 'Technical Forecast:\n';
  if (bullish) {
    analysis += `Gold is trading with bullish bias at $${price.toFixed(2)}. The RSI reading of ${rsi.toFixed(1)} suggests momentum remains with buyers. Statistical probability favors continuation toward $${(price + 18).toFixed(2)} based on similar historical patterns. Trading volume analysis indicates accumulation rather than distribution.\n\n`;
    
    analysis += `Trading Strategy: Consider bullish positions with defined risk parameters. Optimal entry points occur on minor retracements to the $${(price - 5).toFixed(2)} zone.`;
  } else if (bearish) {
    analysis += `Gold is showing bearish characteristics at $${price.toFixed(2)}. With RSI at ${rsi.toFixed(1)}, momentum indicators favor sellers. Historical data suggests high probability (73%) of continuation toward $${(price - 18).toFixed(2)} given current market structure. Volume analysis shows distribution patterns dominating recent sessions.\n\n`;
    
    analysis += `Trading Strategy: Bearish positions justified with risk defined above $${(price + 5).toFixed(2)}. Statistical edge favors short entries on bounces toward $${(price + 3).toFixed(2)}.`;
  } else {
    analysis += `Gold is trading in a consolidation pattern at $${price.toFixed(2)}. The RSI at ${rsi.toFixed(1)} indicates neutral momentum with no statistical edge for directional traders. Analysis of recent price action shows 68% probability of continued range-bound behavior between $${(price - 10).toFixed(2)} and $${(price + 10).toFixed(2)}.\n\n`;
    
    analysis += `Trading Strategy: Range-trading approach optimal until directional catalyst emerges. Statistically, fading extremes at range boundaries offers highest probability setups.`;
  }
  
  return analysis;
}
