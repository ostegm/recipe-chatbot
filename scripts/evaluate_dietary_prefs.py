#!/usr/bin/env python3
import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Tuple
import time
from tqdm import tqdm

from baml_client.sync_client import b
from baml_client.types import DietaryPrefEvalResult


def evaluate_single_row(row: Dict[str, str]) -> Dict[str, any]:
    """Evaluate a single row using the BAML LLM judge."""
    try:
        result: DietaryPrefEvalResult = b.EvalDietaryPrefs(
            query=row['query'],
            preference=row['dietary_restriction'],
            response=row['response']
        )
        
        return {
            **row,  # Keep all original columns
            'llm_judge_result': result.result,
            'llm_judge_reasoning': result.reasoning,
            'llm_judge_dietary_preference': result.dietary_preference,
            'llm_judge_error': None
        }
    except Exception as e:
        return {
            **row,
            'llm_judge_result': None,
            'llm_judge_reasoning': None,
            'llm_judge_dietary_preference': None,
            'llm_judge_error': str(e)
        }


def evaluate_dataset(dataset_path: Path, num_workers: int = 1) -> List[Dict[str, any]]:
    """Evaluate all rows in a dataset using parallel processing."""
    rows = []
    
    # Read the CSV file
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Evaluate rows
    results = []
    
    if num_workers == 1:
        # Single-threaded evaluation with progress bar
        for row in tqdm(rows, desc=f"Evaluating {dataset_path.stem}"):
            results.append(evaluate_single_row(row))
    else:
        # Multi-process evaluation with progress bar
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(evaluate_single_row, row): row for row in rows}
            
            for future in tqdm(as_completed(futures), total=len(futures), 
                             desc=f"Evaluating {dataset_path.stem} (parallel)"):
                results.append(future.result())
    
    return results


def calculate_metrics(results: List[Dict[str, any]]) -> Tuple[float, float, Dict[str, int]]:
    """Calculate True Positive Rate (TPR) and True Negative Rate (TNR)."""
    # Filter out rows that have both human labels and LLM judge results
    valid_results = []
    for r in results:
        label = str(r.get('label', '')).strip().upper()
        # Check if we have a valid human label (TRUE/FALSE or PASS/FAIL)
        if label in ['TRUE', 'FALSE', 'PASS', 'FAIL'] and r.get('llm_judge_result') is not None:
            valid_results.append(r)
    
    if not valid_results:
        return None, None, {"total": len(results), "labeled": 0, "valid": 0}
    
    # Convert string labels to boolean
    true_positives = 0
    true_negatives = 0
    false_positives = 0
    false_negatives = 0
    
    for result in valid_results:
        # Parse human label (TRUE/PASS = positive, FALSE/FAIL = negative)
        human_label_str = str(result['label']).strip().upper()
        human_label = human_label_str in ['TRUE', 'PASS']
        
        # Parse LLM label (handle both boolean and string representations)
        llm_result = result['llm_judge_result']
        if isinstance(llm_result, bool):
            llm_label = llm_result
        else:
            llm_label = str(llm_result).strip().lower() in ['true', '1', 'yes']
        
        if human_label and llm_label:
            true_positives += 1
        elif not human_label and not llm_label:
            true_negatives += 1
        elif not human_label and llm_label:
            false_positives += 1
        elif human_label and not llm_label:
            false_negatives += 1
    
    # Calculate TPR and TNR
    tpr = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    tnr = true_negatives / (true_negatives + false_positives) if (true_negatives + false_positives) > 0 else 0
    
    stats = {
        "total": len(results),
        "labeled": len([r for r in results if str(r.get('label', '')).strip().upper() in ['TRUE', 'FALSE', 'PASS', 'FAIL']]),
        "valid": len(valid_results),
        "true_positives": true_positives,
        "true_negatives": true_negatives,
        "false_positives": false_positives,
        "false_negatives": false_negatives
    }
    
    return tpr, tnr, stats


def write_results(results: List[Dict[str, any]], output_path: Path):
    """Write evaluation results to CSV."""
    if not results:
        return
    
    # Get all fieldnames, preserving original order and adding new fields
    fieldnames = list(results[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def main():
    parser = argparse.ArgumentParser(description='Evaluate dietary preference adherence using LLM judge')
    parser.add_argument(
        'dataset',
        choices=['all', 'train', 'dev', 'test'],
        help='Which dataset(s) to evaluate'
    )
    parser.add_argument(
        '--parallel',
        type=int,
        default=1,
        help='Number of parallel workers (default: 1)'
    )
    
    args = parser.parse_args()
    
    # Determine which datasets to process
    data_dir = Path(__file__).parent.parent / "data" / "dietary_prefs"
    datasets = []
    
    if args.dataset == 'all':
        datasets = [('train', data_dir / 'train_set.csv'),
                   ('dev', data_dir / 'dev_set.csv'),
                   ('test', data_dir / 'test_set.csv')]
    else:
        dataset_path = data_dir / f'{args.dataset}_set.csv'
        datasets = [(args.dataset, dataset_path)]
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / "data" / "dietary_prefs" / "eval_outputs"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Process each dataset
    for dataset_name, dataset_path in datasets:
        if not dataset_path.exists():
            print(f"Error: Dataset file not found: {dataset_path}")
            continue
        
        print(f"\nProcessing {dataset_name} dataset...")
        
        # Evaluate the dataset
        results = evaluate_dataset(dataset_path, num_workers=args.parallel)
        
        # Generate timestamped output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{dataset_name}_eval_results_{timestamp}.csv"
        output_path = output_dir / output_filename
        
        # Write results
        write_results(results, output_path)
        print(f"Results written to: {output_path}")
        
        # Calculate and display metrics
        tpr, tnr, stats = calculate_metrics(results)
        
        print(f"\n{dataset_name.upper()} Dataset Metrics:")
        print(f"  Total rows: {stats['total']}")
        print(f"  Labeled rows: {stats['labeled']}")
        print(f"  Valid evaluations: {stats['valid']}")
        
        if tpr is not None and tnr is not None:
            print(f"  True Positive Rate (TPR): {tpr:.3f}")
            print(f"  True Negative Rate (TNR): {tnr:.3f}")
            print(f"  Confusion Matrix:")
            print(f"    TP: {stats['true_positives']}, FN: {stats['false_negatives']}")
            print(f"    FP: {stats['false_positives']}, TN: {stats['true_negatives']}")
        else:
            print("  No labeled data available for metrics calculation")


if __name__ == "__main__":
    main()