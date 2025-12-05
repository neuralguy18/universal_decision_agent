# LangGraph Nodes — UDA-Hub

## Node List
- ingest_node
- supervisor_node
- classifier_node
- decision_node
- retriever_node
- resolver_node
- tool_node
- escalation_node
- logger_node

## Example Node JSON
```json
{
  "node_id": "classifier_node",
  "type": "llm",
  "model": "gpt-5-mini",
  "prompt_template_file": "prompts/classifier.txt",
  "output_schema_file": "schemas/classifier_schema.json"
}

