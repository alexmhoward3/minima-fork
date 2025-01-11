Let me take a look at the MCP documentation:

After reviewing the MCP documentation, I have some suggestions for improving how Claude uses the tool:

1. Clarify Deep Search Behaviors
- The documentation should be clearer about what each search mode does (summary, timeline, topics, trends)
- Add example searches that illustrate good use cases for each mode
- Better explain how date filtering and tag filtering can be combined with semantic search 

2. Improve Tool Function Description
- The current description focuses on the capabilities but not when/how to use them
- Add examples of appropriate usage in different scenarios
- Include suggested prompting patterns for each mode
- Clarify that semantic search is optional and date-only/tag-only searches are valid

3. Add More Context on Data Sources
- Explain how the tool interacts with file metadata
- Document what metadata fields are available for filtering
- Provide examples of metadata-driven search patterns

4. Document Rate Limits & Performance
- Add guidance on result limits and pagination
- Document any rate limiting or throttling
- Provide performance optimization tips

5. Clarify Error Handling
- Document common error scenarios
- Provide examples of how to handle errors gracefully
- Show how to interpret error messages

Specific suggestions for improving the tool description:

```
"Advanced semantic search with temporal filtering and analysis capabilities.
        
Modes:
- summary: Summarize and analyze matching documents 
- timeline: Show documents chronologically with key events highlighted
- topics: Extract and group key topics/themes from documents
- trends: Analyze how topics and discussions evolve over time

Search types supported:
- Semantic search with query terms
- Date range filtering
- Tag-based filtering 
- Any combination of the above

Examples:
- Find recent meetings about project X
- Show timeline of all docs from Q1 
- Get topics from research notes with #ML tag
- Analyze trends in customer feedback

Response includes:
- Analysis based on selected mode
- Document metadata (dates, tags, etc)
- Raw content (optional)
- Match scores and relevance details

Use this tool when you need to:
1. Find and analyze documents by content and/or metadata
2. Track how topics evolve over time 
3. Extract key themes and relationships
4. Build chronological views of information
"""
```

This provides Claude with more context about WHEN and HOW to use the tool effectively. Let me know if you would like me to elaborate on any of these suggestions or provide additional recommendations!