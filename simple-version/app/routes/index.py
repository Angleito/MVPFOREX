@app.route('/analyze/claude', methods=['POST'])
def analyze_with_claude():
    """Generate trading strategy analysis using Claude 3.7 with chart image."""
    try:
        # Extract market data from request
        market_data = request.json.get('market_data', {})
        chart_image_path = request.json.get('chart_image_path')
        
        # Check if we have enough data to proceed
        if not market_data:
            logger.error("Missing market data in request")
            return jsonify({
                'status': 'error',
                'message': 'Missing market data in request'
            }), 400
        
        # Extract trend information from market data
        trend_info = {
            'direction': market_data.get('trend_direction', 'Unknown'),
            'strength': market_data.get('trend_strength', 'Unknown'),
            'current_price': market_data.get('current_price'),
            'sma20': market_data.get('sma20'),
            'sma50': market_data.get('sma50')
        }
        
        # Extract structure points from market data
        structure_points = {
            'swing_highs': market_data.get('swing_highs', []),
            'swing_lows': market_data.get('swing_lows', [])
        }
        
        # Extract OTE zone if available
        ote_zone = market_data.get('ote_zone')
        
        # Generate analysis using Claude 3.7
        from app.utils.ai_analysis_claude import generate_strategy_analysis_claude
        
        logger.info(f"Generating Claude analysis with chart: {chart_image_path}")
        analysis_result = generate_strategy_analysis_claude(
            trend_info=trend_info,
            structure_points=structure_points,
            ote_zone=ote_zone,
            chart_image_path=chart_image_path
        )
        
        # Log completion
        logger.info(f"Claude analysis generated in {analysis_result.get('elapsed_time', 0):.2f} seconds")
        
        return jsonify(analysis_result)
        
    except Exception as e:
        logger.error(f"Error in Claude analysis: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f"Error generating analysis: {str(e)}",
            'analysis': "Failed to generate trading strategy analysis due to an error."
        })