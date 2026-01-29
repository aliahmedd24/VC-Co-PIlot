"""Curated prompts for vision analysis tasks.

This module contains specialized prompts for different types of visual analysis:
- Pitch deck slides
- Financial charts and graphs
- OCR and text extraction
- Competitor screenshots
- Tables and infographics
"""

# Pitch Deck Analysis Prompts

PITCH_DECK_SLIDE_ANALYSIS = """Analyze this pitch deck slide in detail.

Please provide:

## 1. Slide Type
Identify the slide type (e.g., Title, Problem, Solution, Market Size, Competition, Team, Traction, Business Model, Financial Projections, Ask, etc.)

## 2. Content Analysis
- Key message and value proposition
- Main points and arguments
- Data and metrics presented (with numbers)
- Visual elements (charts, graphs, images, icons)

## 3. Design Quality
- Overall visual appeal (1-10 rating)
- Clarity and readability
- Use of whitespace and layout
- Font choices and hierarchy
- Color scheme effectiveness
- Recommendations for improvement

## 4. Content Gaps
- Missing information that investors would expect
- Questions this slide raises
- Suggestions for additional content

## 5. Extracted Data
Extract all specific numbers, metrics, dates, and quantifiable claims as structured data:
- Financial metrics (revenue, growth rate, etc.)
- Market size numbers
- User/customer counts
- Dates and timelines
- Percentages and rates

Respond in a structured format with clear sections."""

PITCH_DECK_QUICK_SUMMARY = """Provide a brief summary of this pitch deck slide:
- Slide type
- Main message (1-2 sentences)
- Key numbers or metrics
- Design quality (1-10)

Be concise and focused on the essentials."""

# Chart and Graph Analysis Prompts

FINANCIAL_CHART_ANALYSIS = """Analyze this financial chart or graph in detail.

Please provide:

## 1. Chart Type
Identify the chart type (line, bar, pie, scatter, combo, etc.)

## 2. Data Extraction
Extract ALL data points visible in the chart. For each data series:
- Series name
- Time period or categories (x-axis)
- Values (y-axis)
- Units (dollars, percentage, count, etc.)

Present data in a structured table format.

## 3. Trends and Insights
- Overall trend (growing, declining, stable, seasonal)
- Key inflection points
- Growth rates or changes
- Notable patterns or anomalies

## 4. Axes and Labels
- X-axis: label, range, and units
- Y-axis: label, range, and units
- Title and subtitle
- Legend entries

## 5. Visual Quality
- Clarity and readability (1-10)
- Appropriate chart type for the data
- Improvements needed

Extract numbers precisely. If values are approximate, note that."""

CHART_DATA_EXTRACTION_ONLY = """Extract ALL numerical data from this chart/graph.

For each data series, provide:
1. Series name
2. Data points (x, y pairs)
3. Units

Present as structured JSON or table. Focus on accuracy of numbers."""

# OCR and Text Extraction Prompts

OCR_EXTRACT_ALL_TEXT = """Extract ALL visible text from this image.

Include:
- Headings and titles
- Body text and paragraphs
- Bullet points and lists
- Table contents
- Labels and annotations
- Fine print and footnotes

Preserve formatting and structure as much as possible. Use markdown for formatting."""

OCR_STRUCTURED_DOCUMENT = """Extract text from this document page and structure it.

Identify and extract:
1. Document type (form, contract, table, letter, etc.)
2. Headings and sections
3. Key-value pairs (e.g., "Name: John Doe")
4. Tables (as markdown tables)
5. Lists and bullet points

Present in a structured, readable format."""

# Competitor Analysis Prompts

COMPETITOR_SCREENSHOT_ANALYSIS = """Analyze this competitor product screenshot.

Please provide:

## 1. Product Type
Identify what type of product/interface this is (web app, mobile app, landing page, dashboard, etc.)

## 2. UI/UX Analysis
- Overall design quality (1-10)
- User interface patterns used
- Navigation structure
- Key features visible
- User flow and interactions

## 3. Competitive Intelligence
- Unique features or differentiators
- Value proposition (if visible)
- Target audience indicators
- Pricing or business model hints

## 4. Strengths and Weaknesses
- What they're doing well
- Areas for improvement
- Opportunities for differentiation

## 5. Actionable Insights
How can we learn from this to improve our own product?"""

COMPETITOR_LANDING_PAGE = """Analyze this competitor landing page.

Focus on:
1. Value proposition and messaging
2. Key features highlighted
3. Call-to-action (CTA) strategy
4. Social proof (testimonials, logos, metrics)
5. Design and layout effectiveness
6. Target audience signals

Provide actionable competitive insights."""

# Table and Infographic Analysis

TABLE_EXTRACTION = """Extract data from this table.

Provide:
1. Table headers (columns)
2. All rows of data
3. Any footnotes or annotations
4. Units and formatting notes

Present as a markdown table or JSON structure for easy parsing."""

INFOGRAPHIC_ANALYSIS = """Analyze this infographic.

Extract:
1. Main topic and message
2. All statistics and data points
3. Key insights and takeaways
4. Visual flow and structure
5. Data sources (if cited)

Present findings in a structured format."""

# General Image Analysis

GENERAL_IMAGE_ANALYSIS = """Describe this image in detail.

Include:
1. Subject matter and content
2. Visual elements and composition
3. Text (if any)
4. Context and purpose
5. Quality and professionalism

Be thorough and specific."""

# System Prompts for Vision Agents

VISION_ANALYST_SYSTEM = """You are an expert vision analyst for venture capital analysis.

Your capabilities:
- Pitch deck analysis and critique
- Financial chart interpretation and data extraction
- OCR and document digitization
- Competitor UI/UX analysis
- Market research from visual sources

Provide precise, structured, and actionable insights. When extracting data:
- Be accurate with numbers
- Note confidence level if values are approximate
- Structure output for easy parsing
- Cite what you see explicitly

Always maintain a professional, analytical tone."""


def get_prompt_for_analysis_type(analysis_type: str) -> str:
    """Get the appropriate prompt for a given analysis type.

    Args:
        analysis_type: One of: 'pitch_deck', 'chart', 'ocr', 'competitor',
                      'table', 'infographic', 'general'

    Returns:
        Curated prompt for that analysis type
    """
    prompts = {
        "pitch_deck": PITCH_DECK_SLIDE_ANALYSIS,
        "pitch_deck_quick": PITCH_DECK_QUICK_SUMMARY,
        "chart": FINANCIAL_CHART_ANALYSIS,
        "chart_data_only": CHART_DATA_EXTRACTION_ONLY,
        "ocr": OCR_EXTRACT_ALL_TEXT,
        "ocr_structured": OCR_STRUCTURED_DOCUMENT,
        "competitor": COMPETITOR_SCREENSHOT_ANALYSIS,
        "competitor_landing": COMPETITOR_LANDING_PAGE,
        "table": TABLE_EXTRACTION,
        "infographic": INFOGRAPHIC_ANALYSIS,
        "general": GENERAL_IMAGE_ANALYSIS,
    }

    return prompts.get(analysis_type, GENERAL_IMAGE_ANALYSIS)
