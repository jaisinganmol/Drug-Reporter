# Drug Alert System

A multi-agent system for managing and distributing drug safety alerts to pharmacies with delivery tracking and acknowledgment management.

## Overview

This system uses AI-powered agents (Claude) to intelligently route drug safety alerts to pharmacies. It includes comprehensive delivery receipt tracking to ensure pharmacies acknowledge critical alerts.

### Key Features

- **Multi-Agent Architecture**: Broadcast and Targeted agents for different alert scenarios
- **Delivery Receipt Tracking**: Track sent, acknowledged, pending, and failed deliveries
- **Acknowledgment Management**: Monitor which pharmacies have confirmed receipt
- **Follow-up Support**: Identify pharmacies needing reminders
- **Real-time Statistics**: Dashboard showing delivery metrics

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd DrugIt

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Requirements

```txt
anthropic
streamlit
python-dotenv
```

### Configuration

Create a `.env` file:

```
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

### Command Line Interface

```bash
python main.py
```

Processes all drug reports automatically, routing to appropriate agents.

### Web Interface (Streamlit)

```bash
streamlit run app.py
```

Interactive dashboard for:
- Viewing and creating drug reports
- Adding pharmacies
- Sending alerts (broadcast or targeted)
- Tracking acknowledgments
- Viewing delivery statistics

## Project Structure

```
DrugIt/
├── main.py                      # CLI orchestrator
├── app.py                       # Streamlit web interface
├── delivery_receipt_manager.py  # Standalone receipt manager (optional)
├── .env                         # API key configuration
├── requirements.txt             # Dependencies
└── README.md
```
