# UI Bug Detector

A proof-of-concept tool that uses LangGraph to automatically detect frontend/UI bugs on web pages. The tool combines web crawling, Selenium automation, and LLM-powered analysis to identify and document UI issues.

## Features

- Automated web page crawling and parsing
- Interactive element detection and testing
- Console error monitoring
- Screenshot capture
- Bug reproduction script generation
- LLM-powered bug analysis and reporting

## Requirements

- Python 3.8+
- Chrome browser (for Selenium)
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/lg-ui-bug-detector.git
cd lg-ui-bug-detector
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

Run the tool with a target URL:

```bash
python src/main.py https://example.com
```

Optional authentication:
```bash
python src/main.py https://example.com --username user --password pass
```

## Output

The tool generates the following outputs in the `reports` directory:

- Screenshots of detected issues
- Console error logs
- A Python script to reproduce the bug
- A Markdown report with LLM-generated analysis

## Project Structure

```
lg-ui-bug-detector/
├── src/
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── crawler_agent.py
│   │   ├── interaction_agent.py
│   │   ├── detector_agent.py
│   │   ├── reproducer_agent.py
│   │   └── explainer_agent.py
│   └── main.py
├── reports/
├── tests/
├── requirements.txt
└── README.md
```

## How It Works

1. **CrawlerAgent**: Uses BeautifulSoup to parse the target URL and extract interactive elements
2. **InteractionAgent**: Uses Selenium to interact with the page (clicks, form submissions)
3. **DetectorAgent**: Monitors console logs and captures screenshots
4. **ReproducerAgent**: Generates a standalone Selenium script to reproduce bugs
5. **ExplainerAgent**: Uses LangChain + OpenAI to analyze and explain detected issues

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 