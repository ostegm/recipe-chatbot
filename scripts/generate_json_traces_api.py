#!/usr/bin/env python3
"""Generate JSON traces by calling the Recipe Bot API."""

import csv
import time
import json
from pathlib import Path
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.progress import track
import httpx

console = Console()

API_URL = "http://localhost:8000/chat"

def send_query_to_api(query: str) -> Dict[str, any]:
    """Send a query to the Recipe Bot API."""
    payload = {
        "messages": [
            {"role": "user", "content": query}
        ]
    }
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(API_URL, json=payload)
        response.raise_for_status()
        return response.json()

def generate_traces_from_csv(csv_path: str, max_workers: int = 5):
    """Generate traces from queries in a CSV file."""
    # Read queries from CSV
    queries = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'query' in row:
                queries.append(row['query'])
            elif 'user_query' in row:
                queries.append(row['user_query'])
    
    console.print(f"[bold green]Found {len(queries)} queries to process[/bold green]")
    console.print(f"[yellow]Make sure the Recipe Bot API is running at {API_URL}[/yellow]")
    
    # Test API connection
    try:
        send_query_to_api("test")
        console.print("[green]✓ API is responding[/green]")
    except Exception as e:
        console.print(f"[red]✗ API is not responding: {e}[/red]")
        console.print("[yellow]Start the API with: cd recipe-chatbot && uvicorn backend.main:app --reload[/yellow]")
        return
    
    # Process queries with rate limiting
    successful = 0
    failed = 0
    
    for i, query in enumerate(track(queries, description="Generating traces")):
        try:
            # API call - the backend will automatically save the trace
            response = send_query_to_api(query)
            successful += 1
            console.print(f"✓ Trace {i+1}: {query[:50]}...")
            
            # Small delay to be nice to the API
            time.sleep(0.5)
            
        except Exception as e:
            failed += 1
            console.print(f"[red]✗ Error processing query {i+1}: {e}[/red]")
    
    console.print(f"\n[bold green]Complete! {successful} successful, {failed} failed[/bold green]")
    console.print(f"[blue]Traces saved to: recipe-chatbot/annotation/traces/[/blue]")

def generate_sample_traces():
    """Generate some sample traces for testing."""
    sample_queries = [
        "I need a gluten-free dinner recipe",
        "Can you suggest a vegan dessert?",
        "What's a good recipe for someone with a nut allergy?",
        "I'm lactose intolerant, what breakfast options do you have?",
        "Suggest a keto-friendly lunch",
        "I need a recipe that's both vegetarian and low-sodium",
        "What can I make that's dairy-free and egg-free?",
        "Suggest a paleo dinner recipe",
        "I have celiac disease, what bread alternatives do you recommend?",
        "What's a good recipe for someone avoiding shellfish?"
    ]
    
    console.print(f"[yellow]Make sure the Recipe Bot API is running at {API_URL}[/yellow]")
    
    # Test API connection
    try:
        send_query_to_api("test")
        console.print("[green]✓ API is responding[/green]")
    except Exception as e:
        console.print(f"[red]✗ API is not responding: {e}[/red]")
        console.print("[yellow]Start the API with: cd recipe-chatbot && uvicorn backend.main:app --reload[/yellow]")
        return
    
    for i, query in enumerate(track(sample_queries, description="Generating sample traces")):
        try:
            response = send_query_to_api(query)
            console.print(f"✓ Trace {i+1}: {query[:50]}...")
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate JSON traces via Recipe Bot API")
    parser.add_argument("--csv", type=str, help="Path to CSV file with queries")
    parser.add_argument("--sample", action="store_true", help="Generate sample traces")
    
    args = parser.parse_args()
    
    if args.csv:
        generate_traces_from_csv(args.csv)
    elif args.sample:
        generate_sample_traces()
    else:
        console.print("[yellow]Please specify --csv <path> or --sample[/yellow]")
        console.print("\nExamples:")
        console.print("  python generate_json_traces_api.py --sample")
        console.print("  python generate_json_traces_api.py --csv ../homeworks/hw3/data/dietary_queries.csv")