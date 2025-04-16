<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

## Minimum Viable Product: AI Trading Strategy Advisors (ChatGPT 4.1 Vision, Claude 3.7 Vision, & Perplexity Vision)

This document outlines three parallel MVPs for an AI Trading Strategy Advisor, all focused on XAUUSD (gold vs. USD) using the Fibonacci trading strategy. The MVPs differ in the LLM used for analysis and explanation:

- **MVP 1:** Uses ChatGPT 4.1 with Vision
- **MVP 2:** Uses Claude 3.7 with Vision
- **MVP 3 (Benchmark):** Uses Perplexity Vision (or similar vision-enabled LLM)

All MVPs leverage their respective LLMs' vision capabilities to analyze chart images and provide detailed, human-readable trade analysis and recommendations. None execute trades directly. This approach provides immediate value while reducing development complexity and regulatory concerns.

### MVP Overview

The system will analyze XAUUSD charts, apply the Fibonacci strategy rules, and generate detailed explanations of current market conditions and potential trade setups through ChatGPT 4.1.

#### 1. Data Collection Module

```python
import pandas as pd
import requests
from oandapyV20 import API
from oandapyV20.endpoints.instruments import InstrumentsCandles

def fetch_oanda_data(timeframe='M5', count=100):
    """Fetch recent XAUUSD candle data from OANDA"""
    client = API(access_token="YOUR_OANDA_API_KEY")
    params = {
        "count": count,
        "granularity": timeframe
    }
    
    r = InstrumentsCandles(instrument="XAU_USD", params=params)
    client.request(r)
    
    # Format data into pandas DataFrame
    candles = r.response['candles']
    data = []
    for candle in candles:
        data.append({
            'time': candle['time'],
            'open': float(candle['mid']['o']),
            'high': float(candle['mid']['h']),
            'low': float(candle['mid']['l']),
            'close': float(candle['mid']['c']),
            'volume': candle['volume']
        })
    
    return pd.DataFrame(data)
```

#### 2. Market Structure Analysis

```python
def identify_trend(data):
    """Basic trend identification on M5 timeframe"""
    # Calculate some basic trend indicators
    data['sma20'] = data['close'].rolling(window=20).mean()
    data['sma50'] = data['close'].rolling(window=50).mean()
    
    # Identify recent highs and lows (last 30 candles)
    recent_data = data.iloc[-30:]
    highs = recent_data['high'].values
    lows = recent_data['low'].values
    
    # Get the current price
    current_price = data['close'].iloc[-1]
    
    # Check if we have higher highs and higher lows (bullish)
    # or lower highs and lower lows (bearish)
    trend_direction = "Neutral"
    trend_strength = "Weak"
    
    if data['sma20'].iloc[-1] > data['sma50'].iloc[-1]:
        if current_price > data['sma20'].iloc[-1]:
            trend_direction = "Bullish"
            if (highs[-5:] > highs[-10:-5]).sum() >= 3:
                trend_strength = "Strong"
    elif data['sma20'].iloc[-1] < data['sma50'].iloc[-1]:
        if current_price < data['sma20'].iloc[-1]:
            trend_direction = "Bearish"
            if (lows[-5:] < lows[-10:-5]).sum() >= 3:
                trend_strength = "Strong"
    
    return {
        "direction": trend_direction,
        "strength": trend_strength,
        "current_price": current_price,
        "sma20": data['sma20'].iloc[-1],
        "sma50": data['sma50'].iloc[-1]
    }

def find_structure_points(data):
    """Identify potential swing highs/lows for Fibonacci analysis"""
    # Use a simple algorithm to find local maxima and minima
    # More sophisticated algorithms would be used in production
    window = 5  # Look 5 candles before and after
    
    highs = []
    lows = []
    
    for i in range(window, len(data) - window):
        # Check if this is a local maximum
        if data['high'].iloc[i] == max(data['high'].iloc[i-window:i+window+1]):
            highs.append({
                'index': i,
                'price': data['high'].iloc[i],
                'time': data['time'].iloc[i]
            })
        
        # Check if this is a local minimum
        if data['low'].iloc[i] == min(data['low'].iloc[i-window:i+window+1]):
            lows.append({
                'index': i,
                'price': data['low'].iloc[i],
                'time': data['time'].iloc[i]
            })
    
    return {
        'swing_highs': highs[-3:],  # Return the last 3 swing highs
        'swing_lows': lows[-3:]     # Return the last 3 swing lows
    }
```

#### 3. ChatGPT 4.1 Vision

```python
import openai

# Initialize OpenAI client
client = openai.OpenAI(api_key="YOUR_OPENAI_API_KEY")

def generate_strategy_analysis(market_data, trend_info, structure_points):
    """Generate detailed analysis using ChatGPT 4.1"""
    
    # Create a detailed prompt with the market data
    prompt = f"""
    As a professional trading analyst, analyze the following XAUUSD (Gold) market data and provide a detailed explanation of the current setup according to the Fibonacci OTE strategy:
    
    Current Market Information:
    - Timeframe: M5 (5-minute candles)
    - Current Price: ${trend_info['current_price']}
    - Identified Trend: {trend_info['direction']} ({trend_info['strength']})
    - 20-period SMA: ${trend_info['sma20']}
    - 50-period SMA: ${trend_info['sma50']}
    
    Recent Structure Points:
    - Swing Highs: {[f"${h['price']} at {h['time']}" for h in structure_points['swing_highs']]}
    - Swing Lows: {[f"${l['price']} at {l['time']}" for l in structure_points['swing_lows']]}
    
    Strategy Rules:
    For Bullish Trend:
    - Use Fibonacci from the last significant low to the last high
    - Enter buy limit at 0.705 Fibonacci level (OTE zone)
    - Place stop loss 3 pips below the last significant low
    - TP1 at 1:1 risk-reward ratio, TP2 at the 0% Fibonacci level
    
    For Bearish Trend:
    - Use Fibonacci from the last significant high to the last low
    - Enter sell limit at 0.705 Fibonacci level (OTE zone)
    - Place stop loss 3 pips above the last significant high
    - TP1 at 1:1 risk-reward ratio, TP2 at the 0% Fibonacci level
    
    Please provide:
    1. A detailed assessment of the current trend, including confirmation of BOS or CHoCH
    2. Identification of which swing points should be used for Fibonacci placement
    3. Calculation of the OTE zone (61.8% to 79% Fibonacci levels)
    4. Exact entry price recommendation at the 0.705 Fibonacci level
    5. Precise stop loss and take profit levels with pip distances
    6. Any potential warnings or special considerations for this setup
    7. A confidence rating (1-10) for this trading opportunity
    
    Support your analysis with specific price levels and clear reasoning.
    """
    
    # Call ChatGPT 4.1 API
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",  # Use the appropriate model name
    messages=[
            {"role": "system", "content": "You are an expert trading analyst specializing in Fibonacci trading strategies for gold (XAUUSD). You provide precise, detailed analysis with exact price levels and clear reasoning."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,  # Lower temperature for more consistent responses
        max_tokens=2000
    )
    
    return response.choices[0].message.content
```

#### 4. Claude 3.7 Vision

```python
import anthropic

# Initialize Anthropic client
client = anthropic.Anthropic(api_key="YOUR_ANTHROPIC_API_KEY")

def generate_strategy_analysis_claude(market_data, trend_info, structure_points):
    """Generate detailed analysis using Claude 3.7 Vision"""
    
    # Create a detailed prompt with the market data
    prompt = f"""
    As a professional trading analyst, analyze the following XAUUSD (Gold) market data and provide a detailed explanation of the current setup according to the Fibonacci OTE strategy:

    Current Market Information:
    - Timeframe: M5 (5-minute candles)
    - Current Price: ${trend_info['current_price']}
    - Identified Trend: {trend_info['direction']} ({trend_info['strength']})
    - 20-period SMA: ${trend_info['sma20']}
    - 50-period SMA: ${trend_info['sma50']}

    Recent Structure Points:
    - Swing Highs: {[f"${h['price']} at {h['time']}" for h in structure_points['swing_highs']]}
    - Swing Lows: {[f"${l['price']} at {l['time']}" for l in structure_points['swing_lows']]}

    Strategy Rules:
    For Bullish Trend:
    - Use Fibonacci from the last significant low to the last high
    - Enter buy limit at 0.705 Fibonacci level (OTE zone)
    - Place stop loss 3 pips below the last significant low
    - TP1 at 1:1 risk-reward ratio, TP2 at the 0% Fibonacci level

    For Bearish Trend:
    - Use Fibonacci from the last significant high to the last low
    - Enter sell limit at 0.705 Fibonacci level (OTE zone)
    - Place stop loss 3 pips above the last significant high
    - TP1 at 1:1 risk-reward ratio, TP2 at the 0% Fibonacci level

    Please provide:
    1. A detailed assessment of the current trend, including confirmation of BOS or CHoCH
    2. Identification of which swing points should be used for Fibonacci placement
    3. Calculation of the OTE zone (61.8% to 79% Fibonacci levels)
    4. Exact entry price recommendation at the 0.705 Fibonacci level
    5. Precise stop loss and take profit levels with pip distances
    6. Any potential warnings or special considerations for this setup
    7. A confidence rating (1-10) for this trading opportunity

    Support your analysis with specific price levels and clear reasoning.
    """

    # Call Claude 3.7 Vision API
    response = client.messages.create(
        model="claude-3.7-vision",
        max_tokens=2000,
        temperature=0.2,
        system="You are an expert trading analyst specializing in Fibonacci trading strategies for gold (XAUUSD). You provide precise, detailed analysis with exact price levels and clear reasoning.",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.content[0].text if response.content else ""
```

*This function mirrors the ChatGPT integration, using the same prompt structure and output expectations, but calls Claude 3.7 Vision via the @anthropic-ai/sdk.*


#### 4. Simple Web Interface

```python
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze')
def analyze():
    # Fetch the latest data
    market_data = fetch_oanda_data()
    
    # Analyze the trend
    trend_info = identify_trend(market_data)
    
    # Find structure points
    structure_points = find_structure_points(market_data)
    
    # Generate analysis using ChatGPT
    analysis = generate_strategy_analysis(
        market_data, 
        trend_info, 
        structure_points
    )
    
    return jsonify({
        'trend': trend_info,
        'structure_points': structure_points,
        'analysis': analysis
    })

if __name__ == '__main__':
    app.run(debug=True)
```


### HTML Template

```html
&lt;html&gt;
&lt;head&gt;
    &lt;title&gt;XAUUSD Fibonacci Strategy Advisor&lt;/title&gt;
    &lt;link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"&gt;
    &lt;script src="https://cdn.jsdelivr.net/npm/chart.js"&gt;&lt;/script&gt;
    &lt;style&gt;
        .analysis-container {
            background-color: #f4f4f4;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        .loading {
            text-align: center;
            margin: 50px;
        }
    &lt;/style&gt;
&lt;/head&gt;
&lt;body&gt;
    <div>
        <h1>XAUUSD Fibonacci Strategy Advisor</h1>
        
        <div>
            <div>
                &lt;button id="analyze-btn" class="btn btn-primary w-100"&gt;Analyze Current Market&lt;/button&gt;
            </div>
        </div>
        
        <div>
            <div>
                <span>Loading...</span>
            </div>
            <p>Analyzing market conditions...</p>
        </div>
        
        <div>
            <div>
                <div>
                    &lt;canvas id="price-chart"&gt;&lt;/canvas&gt;
                </div>
            </div>
            
            <div>
                <div>
                    <div>
                        <div>Trend Information</div>
                        <div>
                            <p><strong>Direction:</strong> <span></span></p>
                            <p><strong>Strength:</strong> <span></span></p>
                            <p><strong>Current Price:</strong> <span></span></p>
                        </div>
                    </div>
                </div>
                
                <div>
                    <div>
                        <div>Structure Points</div>
                        <div>
                            <div>
                                <div>
                                    <h5>Swing Highs</h5>
                                    <ul></ul>
                                </div>
                                <div>
                                    <h5>Swing Lows</h5>
                                    <ul></ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div>
                <div>
                    <div>
                        <h3>AI Strategy Analysis</h3>
                        <div></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    &lt;script&gt;
        document.getElementById('analyze-btn').addEventListener('click', function() {
            // Show loading indicator
            document.getElementById('loading').classList.remove('d-none');
            document.getElementById('results').classList.add('d-none');
            
            // Call the analysis endpoint
            fetch('/analyze')
                .then(response =&gt; response.json())
                .then(data =&gt; {
                    // Hide loading indicator
                    document.getElementById('loading').classList.add('d-none');
                    document.getElementById('results').classList.remove('d-none');
                    
                    // Update the UI with the analysis results
                    document.getElementById('trend-direction').textContent = data.trend.direction;
                    document.getElementById('trend-strength').textContent = data.trend.strength;
                    document.getElementById('current-price').textContent = '$' + data.trend.current_price;
                    
                    // Update swing highs
                    const swingHighsList = document.getElementById('swing-highs');
                    swingHighsList.innerHTML = '';
                    data.structure_points.swing_highs.forEach(high =&gt; {
                        const li = document.createElement('li');
                        li.className = 'list-group-item';
                        li.textContent = `$${high.price} at ${new Date(high.time).toLocaleTimeString()}`;
                        swingHighsList.appendChild(li);
                    });
                    
                    // Update swing lows
                    const swingLowsList = document.getElementById('swing-lows');
                    swingLowsList.innerHTML = '';
                    data.structure_points.swing_lows.forEach(low =&gt; {
                        const li = document.createElement('li');
                        li.className = 'list-group-item';
                        li.textContent = `$${low.price} at ${new Date(low.time).toLocaleTimeString()}`;
                        swingLowsList.appendChild(li);
                    });
                    
                    // Update the analysis content
                    document.getElementById('analysis-content').innerHTML = data.analysis.replace(/\n/g, '<br>');
                    
                    // You'd add chart rendering code here
                })
                .catch(error =&gt; {
                    console.error('Error:', error);
                    document.getElementById('loading').classList.add('d-none');
                    alert('Error fetching analysis. Please try again.');
                });
        });
    &lt;/script&gt;
&lt;/body&gt;
&lt;/html&gt;
```


### Sample ChatGPT 4.1 Analysis Output

The ChatGPT 4.1 integration will generate detailed market analyses like this example:

```
# XAUUSD Fibonacci Strategy Analysis

## Current Market Assessment
Based on the provided data, XAUUSD is currently in a **Bullish trend** with **Strong** momentum. The price at $2,347.82 is trading above both the 20-period SMA ($2,331.56) and 50-period SMA ($2,319.24) on the M5 timeframe, confirming the short-term bullish bias.

## Structure Identification
Analyzing the recent price action, I can confirm a Break of Structure (BOS) has occurred at $2,338.45, where price broke above the previous swing high. This was followed by a Change of Character (CHoCH), as the market created a higher low at $2,329.17 instead of continuing the previous pattern of lower lows.

## Fibonacci Placement
For this bullish trend, we need to place our Fibonacci retracement from the last significant low to the last high:
- Last significant low: $2,329.17 (0% Fibonacci level)
- Last significant high: $2,347.82 (100% Fibonacci level)

## OTE Zone Calculation
The Optimal Trade Entry (OTE) zone spans from 61.8% to 79% Fibonacci retracement levels:
- 61.8% Fibonacci level: $2,336.27
- 79.0% Fibonacci level: $2,332.08

## Entry Recommendation
The recommended entry point is at the 70.5% Fibonacci level: **$2,334.13**

This buy limit order should be placed to capture a potential retracement before the continuation of the bullish trend.

## Stop Loss and Take Profit Levels
- **Stop Loss**: Place 3 pips below the last significant low at $2,328.87 (29.26 pips from entry)
- **TP1** (1:1 risk-reward): $2,363.39 (29.26 pips from entry)
- **TP2** (at 0% Fibonacci level): $2,347.82 (13.69 pips from entry)

## Risk Management
With a 29.26 pip stop, this represents a risk of approximately 1.25% on a standard lot position. I recommend scaling position size to risk no more than 1-2% of trading capital on this setup.

## Special Considerations
1. Gold has shown increased volatility due to recent geopolitical tensions.
2. Be aware that the upcoming US CPI data release (tomorrow at 8:30 AM EST) could impact gold prices significantly.
3. The bullish momentum appears strong, but the M15 timeframe shows potential resistance at $2,352.00.

## Confidence Rating
Based on all factors analyzed, I rate this setup as **7/10** confidence. The trend direction is clear, the BOS and CHoCH are well-defined, and the price structure aligns with our Fibonacci strategy requirements.

This setup provides a favorable risk-to-reward opportunity with clear entry, stop loss, and take profit levels aligned with the strategy guidelines.
```


### MVP Advantages

- **Rapid Development:** All MVPs can be developed quickly using existing APIs.
- **Comparative Insights:** Enables direct comparison of ChatGPT, Claude, and Perplexity vision capabilities for this use case.
- **Benchmarking:** Use Perplexity as a third engine for benchmarking and diversity of analysis.
- **Regulatory Simplicity:** No trade execution, just analysis.
- **User Feedback:** Collects user feedback on all LLMs’ outputs for future improvement.

### Evaluation & Benchmarking

To ensure technical rigor and practical relevance, the MVP will:
- Use annotated, real-world chart datasets for both vision and text analysis.
- Evaluate each LLM (ChatGPT 4.1 Vision, Claude 3.7 Vision, and Perplexity Vision) on:
    - **Chart Pattern Recognition Accuracy/F1**
    - **Explanation Quality (BLEU, ROUGE, METEOR)**
    - **Image Captioning (CIDEr)**
    - **Latency**
    - **Backtest Metrics** (e.g., Sharpe ratio, drawdown)
- Collect structured user feedback and run simulated backtests to validate real-world performance.
- Present results in a comparative dashboard, enabling both automated and human-in-the-loop evaluation.

#### Example Evaluation Table
| Model             | Chart Accuracy | Explanation BLEU | Interpretability | Latency (s) | Sharpe Ratio (Backtest) |
|-------------------|---------------|------------------|------------------|-------------|------------------------|
| GPT-4 Vision      | 85%           | 0.72             | 4.3/5            | 4.0         | 1.25                   |
| Claude 3.7 Vision | 83%           | 0.70             | 4.1/5            | 3.8         | 1.18                   |
| Perplexity        | 80%           | 0.68             | 4.0/5            | 3.5         | 1.10                   |

*Metrics are illustrative. Actual results depend on your dataset and evaluation pipeline.*

#### Qualitative Metrics
- **Human Interpretability:** Rate clarity, usefulness, and trustworthiness of each LLM’s output.
- **Truthfulness/Consistency:** Check for hallucinations or misleading advice.
- **User Feedback:** Collect structured feedback from traders on each LLM’s recommendations.

#### Workflow Integration
- Present all LLM outputs side by side in the web interface for direct comparison.
- Allow users to rate, comment, and flag outputs for further analysis.
- Optionally, provide a “consensus” or “blended” recommendation based on agreement across engines.

### Next Steps After MVP
- Enhance pattern recognition with more advanced vision models.
- Track and compare the accuracy of each LLM’s recommendations and backtest results.
- Allow users to select or blend LLMs for their preferred analysis style.
- Add mobile notifications and user customization.
- Optionally suggest trades via broker API (without execution).
- Use user feedback and backtest results to iteratively improve prompts and model selection.

### References & Further Reading
- [Vision-Language Models Guide](https://encord.com/blog/vision-language-models-guide/)
- [LLM Evaluation Metrics](https://aisera.com/blog/llm-evaluation/)
- [Quantified Strategies: AI Trading](https://www.quantifiedstrategies.com/ai-trading-strategies/)
