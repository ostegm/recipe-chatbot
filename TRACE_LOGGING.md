# Trace Logging in Recipe Chatbot

## Table of Contents
1. [Overview](#overview)
2. [What are Traces?](#what-are-traces)
3. [Core Trace Logging Implementation](#core-trace-logging-implementation)
4. [Trace Data Structures](#trace-data-structures)
5. [Trace Generation Strategies](#trace-generation-strategies)
6. [Trace Annotation Workflow](#trace-annotation-workflow)
7. [Educational Applications](#educational-applications)
8. [Trace Analysis Tools](#trace-analysis-tools)
9. [Best Practices](#best-practices)

## Overview

Trace logging is a fundamental component of the Recipe Chatbot system, providing comprehensive conversation recording for evaluation, debugging, and educational purposes. The system automatically captures every interaction between users and the AI assistant, enabling systematic analysis of system behavior, failure modes, and performance metrics.

## What are Traces?

A **trace** is a complete record of a conversation between a user and the Recipe Chatbot, including:
- All user messages (queries about recipes)
- All assistant responses
- Tool calls and their results
- Timestamps and unique identifiers
- Success/failure states (in labeled traces)
- Metadata about the conversation flow

### Why Trace Logging Matters
1. **Debugging**: Identify when and why the system fails
2. **Evaluation**: Measure system performance systematically
3. **Education**: Learn AI evaluation techniques through real examples
4. **Improvement**: Discover patterns to enhance the system
5. **Compliance**: Maintain audit trails of AI interactions

## Core Trace Logging Implementation

### Automatic Trace Saving (`backend/main.py`)

Every conversation through the API is automatically logged:

```python
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    # Process the chat request
    messages = payload.messages
    response_content = get_agent_response([m.dict() for m in messages])
    response = ChatResponse(messages=messages + [ChatMessage(role="assistant", content=response_content)])
    
    # Save trace (request and response) in one place
    traces_dir = Path(__file__).parent.parent / "annotation" / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    trace_path = traces_dir / f"trace_{ts}.json"
    with open(trace_path, "w") as f:
        json.dump({
            "request": payload.model_dump(),
            "response": response.model_dump()
        }, f)
    
    return response
```

### Key Features
- **Automatic**: No manual intervention required
- **Non-blocking**: Doesn't slow down the API response
- **Chronological**: Microsecond-precision timestamps
- **Complete**: Captures both request and response
- **Location**: `/annotation/traces/` directory

## Trace Data Structures

### 1. Basic Trace Format (API-generated)
```json
{
  "request": {
    "messages": [
      {"role": "user", "content": "What's a good vegetarian protein dish?"},
      {"role": "assistant", "content": "Previous response..."}
    ]
  },
  "response": {
    "messages": [
      {"role": "user", "content": "What's a good vegetarian protein dish?"},
      {"role": "assistant", "content": "Previous response..."},
      {"role": "assistant", "content": "I recommend making a chickpea curry..."}
    ]
  }
}
```

### 2. Enhanced Trace Format (HW5)
```json
{
  "conversation_id": "1373de99-f107-48da-b272-9e47c9b935dd",
  "messages": [
    {
      "role": "user",
      "content": "What vegetarian high-protein meal can I cook tonight?"
    },
    {
      "role": "assistant",
      "content": "Let me help you find a delicious vegetarian meal..."
    },
    {
      "role": "tool",
      "content": "TOOL_CALL[GetCustomerProfile] Unable to access user profile..."
    }
  ],
  "last_success_state": "ParseRequest",
  "first_failure_state": "GetCustomerProfile"
}
```

### 3. Pipeline States Tracked
```
1. ParseRequest         → Understanding user input
2. PlanToolCalls       → Deciding which tools to use
3. GenCustomerArgs     → Creating customer DB arguments
4. GetCustomerProfile  → Fetching customer data
5. GenRecipeArgs       → Creating recipe search arguments
6. GetRecipes          → Searching recipe database
7. GenWebArgs          → Creating web search arguments
8. GetWebInfo          → Fetching web information
9. ComposeResponse     → Drafting final answer
10. DeliverResponse    → Sending response to user
```

### 4. CSV Export Format
For easier analysis, traces can be converted to CSV:
```csv
trace_id,customer_persona,user_query,conversation_messages,tool_calls
uuid-123,gluten_free_family,"Need dinner ideas","USER: Need dinner ideas | AGENT: Let me help...","GetRecipes(input: {}, output: {})"
```

## Trace Generation Strategies

### 1. Natural Trace Collection
- Real user interactions through the web interface
- Stored automatically in `/annotation/traces/`
- Represents actual usage patterns

### 2. Synthetic Trace Generation (`hw5/generation/generate_traces.py`)
```python
# Weighted sampling for failure injection
weights = {
    "ParseRequest": 5,
    "PlanToolCalls": 10,
    "GetCustomerProfile": 20,
    "GetRecipes": 30,
    "ComposeResponse": 15,
    "DeliverResponse": 1
}

# Generate trace with intentional failure
def generate_trace(first_failure_state, last_success_state):
    # Use GPT-4.1 to create realistic conversation
    # that progresses through pipeline states
    # and fails at the specified point
```

### 3. Parallel Trace Generation (`hw3/scripts/generate_traces.py`)
```python
# Generate multiple traces per query for variation
with ThreadPoolExecutor(max_workers=32) as executor:
    futures = []
    for query in queries:
        for i in range(40):  # 40 traces per query
            future = executor.submit(send_query, query)
            futures.append(future)
```

## Trace Annotation Workflow

### Step 1: Generate or Collect Traces
```bash
# Generate synthetic traces
python hw5/generation/generate_traces.py

# Or collect from live system
# (happens automatically via API)
```

### Step 2: Prepare for Annotation
```bash
# Convert to CSV for labeling tool
python lesson-7/scripts/convert_traces_to_csv.py

# Or copy to annotation directory
cp annotation/traces/trace_*.json annotation/golden_dataset/
```

### Step 3: Annotate Using Web Interface

#### Option A: Lesson 7 Labeling Tool
```bash
cd lesson-7/labeling-tool
python main.py
# Access at http://localhost:8000
```

Features:
- View traces one by one
- Add feedback text
- Select/add failure modes
- Track progress

#### Option B: Annotation Tool
```bash
cd annotation
python annotation.py
# Access at http://localhost:5001
```

Features:
- Chat bubble visualization
- Open coding (free-form notes)
- Axial coding (categorized failures)
- Navigation between traces

### Step 4: Use Annotated Data
- Train LLM judges
- Calculate performance metrics
- Identify failure patterns
- Improve system design

## Educational Applications

### Homework 3: LLM-as-Judge
- **Goal**: Build automated evaluation systems
- **Traces Used**: ~2400 dietary restriction queries
- **Process**:
  1. Generate traces with dietary queries
  2. Label as PASS/FAIL using GPT-4
  3. Train few-shot LLM judge
  4. Evaluate judge performance

### Homework 5: Failure Analysis
- **Goal**: Understand pipeline failure patterns
- **Traces Used**: 100 synthetic conversations
- **Process**:
  1. Generate traces with intentional failures
  2. Analyze failure transitions
  3. Create visualization heatmaps
  4. Identify common failure patterns

### Learning Outcomes
1. **Systematic Evaluation**: Learn to evaluate AI systems rigorously
2. **Error Taxonomy**: Develop structured failure categorizations
3. **Statistical Analysis**: Apply metrics like TPR/TNR
4. **Tool Development**: Build custom evaluation tools
5. **Real-world Skills**: Prepare for production AI deployment

## Trace Analysis Tools

### 1. Failure Transition Heatmap (`hw5/analysis/transition_heatmaps.py`)
```python
# Visualize state transitions leading to failures
def create_transition_heatmap(traces):
    # Count transitions from success to failure states
    # Generate heatmap showing common failure paths
```

### 2. Performance Metrics (`backend/evaluation_utils.py`)
```python
class BaseRetrievalEvaluator:
    def calculate_metrics(self, traces):
        # Recall@k
        # Mean Reciprocal Rank (MRR)
        # Success rate
        # Average response time
```

### 3. Judge Evaluation (`hw3/scripts/evaluate_judge.py`)
```python
def evaluate_judge_performance(predictions, ground_truth):
    # True Positive Rate (TPR)
    # True Negative Rate (TNR)
    # Confidence intervals
    # Bias correction
```

## Best Practices

### 1. Storage Management
- Implement log rotation for trace files
- Archive old traces periodically
- Use compression for long-term storage

### 2. Privacy Considerations
- Anonymize user data in traces
- Implement retention policies
- Secure trace storage directories

### 3. Performance Optimization
- Use async I/O for trace writing
- Batch trace processing
- Index traces for faster retrieval

### 4. Trace Quality
- Validate trace format on save
- Include relevant metadata
- Maintain consistent naming conventions

### 5. Analysis Workflow
```python
# Example analysis pipeline
def analyze_traces():
    # 1. Load traces
    traces = load_traces_from_directory("annotation/traces")
    
    # 2. Filter relevant traces
    filtered = filter_by_date_range(traces, start_date, end_date)
    
    # 3. Extract metrics
    metrics = calculate_performance_metrics(filtered)
    
    # 4. Identify patterns
    failure_patterns = find_common_failures(filtered)
    
    # 5. Generate report
    create_analysis_report(metrics, failure_patterns)
```

## Conclusion

Trace logging in the Recipe Chatbot system provides a robust foundation for:
- **Development**: Debug and improve the system
- **Evaluation**: Measure performance objectively
- **Education**: Learn AI evaluation techniques
- **Research**: Understand AI system behavior

The combination of automatic logging, flexible annotation tools, and comprehensive analysis utilities makes it an excellent platform for both practical development and educational purposes. By systematically collecting and analyzing traces, developers and students can gain deep insights into AI system behavior and learn to build more reliable conversational AI systems.