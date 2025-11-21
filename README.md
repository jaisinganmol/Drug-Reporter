# 💊 Drug Reporter - Multi-Agent Drug Safety Alert System

A sophisticated multi-agent system designed for managing and distributing drug safety alerts to pharmacies with comprehensive tracking and acknowledgment management.

## 🎯 Overview

Drug Reporter leverages AI-powered agents (Claude) to intelligently route drug safety alerts to pharmacies. The system ensures critical alerts reach the right pharmacies and tracks confirmation of receipt for regulatory compliance and patient safety.

## ✨ Key Features

### 🤖 Multi-Agent Architecture
- **Broadcast Agent**: Sends alerts to all pharmacies simultaneously
- **Targeted Agent**: Intelligently routes alerts to specific pharmacies based on criteria (location, type, region)
- **Extensible Design**: Easy to add new agent types for future scenarios

### 📊 Delivery Management
- Real-time delivery receipt tracking
- Acknowledgment status monitoring
- Follow-up reminder system for pending pharmacies
- Detailed delivery statistics and reporting

### 💻 Dual Interface
- **CLI Mode** (`main.py`): Automated batch processing and testing
- **Web Dashboard** (`app.py`): Interactive Streamlit interface for manual operations

### 📋 Pre-loaded Data
- 5 default pharmacies across multiple regions
- 3 sample drug reports for testing
- Ready-to-use alert scenarios

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- Anthropic API key (get one at [console.anthropic.com](https://console.anthropic.com))

### Installation

1. **Clone and navigate to the project:**
```bash
cd DrugIt
```

2. **Create virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure API key:**
```bash
nano .env  # or use your favorite editor
```

Add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### Running the Application

#### Option 1: Web Dashboard (Recommended)
```bash
streamlit run app.py
```
Then open `http://localhost:8501` in your browser

#### Option 2: CLI Demo
```bash
python3 main.py
```

## 📁 Project Structure

```
DrugIt/
├── agents/                 # AI agent implementations
│   ├── base_agent.py      # Abstract base class
│   ├── broadcast_agent.py # Broadcasts to all pharmacies
│   ├── targeted_agent.py  # Targets specific pharmacies
│   └── agent_factory.py   # Factory pattern for agent creation
│
├── interfaces/            # Abstract interfaces
│   ├── alert_interface.py      # Alert sending contract
│   └── pharmacy_interface.py   # Pharmacy management contract
│
├── models/               # Data models
│   ├── drug_report.py    # Drug safety report
│   ├── pharmacy.py       # Pharmacy information
│   └── delivery_receipt.py # Delivery tracking
│
├── utils/               # Helper functions
│   └── helpers.py       # Utility functions
│
├── main.py             # CLI entry point
├── app.py              # Streamlit web interface
├── requirements.txt    # Dependencies
├── .env               # API configuration
└── README.md          # This file
```