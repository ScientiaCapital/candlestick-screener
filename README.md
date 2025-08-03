# Technical Scanner

A web application that scans stocks for various technical patterns using pandas-ta for pattern detection and yfinance for stock data. The application includes Redis caching for improved performance and rate limiting for API protection.

## Features

- Real-time stock data fetching using yfinance
- Support for 60+ technical patterns using pandas-ta
- Interactive web interface
- Visual chart display for each stock
- Bullish/Bearish signal detection
- Redis caching for improved performance
- Rate limiting for API protection
- Comprehensive test suite

## Architecture

### System Overview

The Candlestick Screener follows a modular Flask-based architecture with Redis for caching and rate limiting:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │───▶│  Flask App      │───▶│   yfinance      │
│   (Frontend)    │    │  (app.py)       │    │   API           │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Pattern Engine │    │   Redis Cache   │
                       │  (patterns.py)  │    │  & Rate Limiter │
                       └─────────────────┘    └─────────────────┘
```

### Core Components

- **app.py**: Main Flask application with route handlers and business logic
- **config.py**: Centralized configuration management with environment variable support
- **patterns.py**: 60+ candlestick pattern definitions and detection algorithms
- **cache_manager.py**: Redis-based caching with intelligent invalidation strategies
- **rate_limiter.py**: API rate limiting using Redis for distributed rate tracking
- **security.py**: Input validation, CSRF protection, and security middleware

### Data Flow

1. **User Request**: Web interface sends pattern selection to Flask backend
2. **Rate Limiting**: Request validated against Redis-based rate limits
3. **Cache Check**: System checks Redis cache for existing pattern results
4. **Data Fetching**: If cache miss, yfinance fetches real-time stock data
5. **Pattern Analysis**: pandas-ta library processes data for pattern detection
6. **Result Caching**: Results stored in Redis with configurable TTL
7. **Response**: JSON results returned to frontend for display

### Technology Stack

- **Backend**: Flask (Python 3.8+)
- **Data Processing**: pandas, numpy, pandas-ta
- **Stock Data**: yfinance (primary), Alpha Vantage (optional)
- **Caching**: Redis with Flask-Caching
- **Rate Limiting**: Flask-Limiter with Redis backend
- **Security**: Custom middleware with CSRF protection
- **Testing**: pytest with comprehensive coverage
- **Frontend**: HTML templates with responsive CSS/JavaScript

## Prerequisites

- Python 3.8 or higher
- Redis server
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd candlestick-screener
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Redis:
   - On macOS:
     ```bash
     brew install redis
     ```
   - On Linux:
     ```bash
     sudo apt-get install redis-server
     ```

4. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file and customize it:
```bash
cp .env.example .env
```

2. Edit the `.env` file with your specific settings:
   - Set a secure `SECRET_KEY` for production
   - Configure Redis URLs for your environment
   - Adjust batch sizes and rate limits as needed
   - Add API keys if using Alpha Vantage (optional)

3. Add your stock symbols to `datasets/symbols.csv` in the format:
```
SYMBOL,Company Name
AAPL,Apple Inc.
MSFT,Microsoft Corporation
```

## Usage

1. Start Redis server:
```bash
redis-server
```

2. Start the application:
```bash
flask run
```

3. Open your web browser and navigate to `http://localhost:5000`

4. Select a technical pattern from the dropdown menu and click "Scan"

5. View the results showing stocks that match the selected pattern

## Testing

The application includes a comprehensive test suite. To run the tests:

1. Make sure you have all dependencies installed:
```bash
pip install -r requirements.txt
```

2. Run the tests:
```bash
pytest
```

The test suite includes:
- Unit tests for pattern detection
- Integration tests for API endpoints
- Cache testing
- Rate limit testing
- Error handling tests

## API Endpoints

- `/` - Main page with pattern scanning interface
- `/snapshot` - Update stock data for all symbols
- `/stats` - View cache and rate limit statistics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Video Tutorials for this repository:

* Candlestick Pattern Recognition - https://www.youtube.com/watch?v=QGkf2-caXmc
* Building a Web-based Technical Screener - https://www.youtube.com/watch?v=OhvQN_yIgCo
* Finding Breakouts - https://www.youtube.com/watch?v=exGuyBnhN_8