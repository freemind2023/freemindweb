# SEO Analysis Prompt

You are an expert SEO analyst. Analyze the following data and provide actionable insights.

## Input Data
- **GA4 Data:** {{ga4_data}}
- **Search Console Data:** {{search_console_data}}
- **Date Range:** {{date_range}}
- **Business Goals:** {{business_goals}}

## Analysis Required

1. **Traffic Overview:** Summarize organic traffic trends — sessions, users, bounce rate, session duration
2. **Top Performing Pages:** Which pages drive the most traffic and engagement?
3. **Underperforming Pages:** Which pages have high impressions but low CTR or high bounce rate?
4. **Keyword Opportunities:** Identify "striking distance" keywords (positions 4–20) worth targeting
5. **Content Gaps:** What queries are users searching that we don't rank well for?
6. **Technical Issues:** Any pages with poor engagement metrics suggesting technical problems?

## Output Format

Provide your analysis as structured markdown with:
- Key metrics table
- Top 10 opportunities ranked by potential impact
- Specific action items with priority (high/medium/low)
- Comparison to previous period if data is available
