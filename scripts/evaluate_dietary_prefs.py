#!/usr/bin/env python3
import argparse
import csv
import os
import sys
import random
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Tuple
from tqdm import tqdm
from judgy import estimate_success_rate

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


def evaluate_dataset(dataset_path: Path, num_workers: int = 1, sample_size: int = None) -> List[Dict[str, any]]:
    """Evaluate all rows in a dataset using parallel processing."""
    rows = []
    
    # Read the CSV file
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Apply sampling if requested
    if sample_size and len(rows) > sample_size:
        print(f"  Total rows available: {len(rows)}")
        print(f"  Sampling: {sample_size} rows")
        random.seed(42)  # For reproducibility
        rows = random.sample(rows, sample_size)
    
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


def apply_bias_correction(results: List[Dict[str, any]], sample_size: int = None) -> Dict[str, any]:
    """Apply bias correction using judgy library with hardcoded test set metrics."""
    # Hardcoded test set metrics from previous evaluation
    TEST_TPR = 1.000  # True Positive Rate
    TEST_TNR = 0.917  # True Negative Rate
    
    # Convert TPR/TNR to test labels and predictions for judgy
    # Create synthetic test set based on the observed TPR/TNR
    # TPR = 1.0 means TP=34, FN=0 (from actual test)
    # TNR = 0.917 means TN=11, FP=1 (from actual test)
    test_labels = [1]*34 + [0]*12  # 34 positives, 12 negatives
    test_preds = [1]*34 + [0]*11 + [1]*1  # Perfect on positives, 11/12 correct on negatives
    
    # Sample if requested
    if sample_size and len(results) > sample_size:
        results = random.sample(results, sample_size)
    
    # Extract predictions from results
    unlabeled_preds = []
    valid_results = []
    
    for r in results:
        if r.get('llm_judge_result') is not None:
            valid_results.append(r)
            llm_result = r['llm_judge_result']
            if isinstance(llm_result, bool):
                pred = 1 if llm_result else 0
            else:
                pred = 1 if str(llm_result).strip().lower() in ['true', '1', 'yes'] else 0
            unlabeled_preds.append(pred)
    
    if not unlabeled_preds:
        return {
            'sample_size': len(results),
            'valid_evaluations': 0,
            'raw_pass_rate': None,
            'bias_corrected_pass_rate': None,
            'confidence_lower': None,
            'confidence_upper': None,
            'error': 'No valid evaluations'
        }
    
    # Calculate raw pass rate
    raw_passes = sum(unlabeled_preds)
    raw_pass_rate = raw_passes / len(unlabeled_preds)
    
    # Apply bias correction
    try:
        theta_hat, lower_bound, upper_bound = estimate_success_rate(
            test_labels=test_labels,
            test_preds=test_preds,
            unlabeled_preds=unlabeled_preds
        )
        
        return {
            'sample_size': len(results),
            'valid_evaluations': len(valid_results),
            'raw_passes': raw_passes,
            'raw_fails': len(unlabeled_preds) - raw_passes,
            'raw_pass_rate': raw_pass_rate,
            'bias_corrected_pass_rate': theta_hat,
            'confidence_lower': lower_bound,
            'confidence_upper': upper_bound,
            'adjustment': theta_hat - raw_pass_rate,
            'test_tpr': TEST_TPR,
            'test_tnr': TEST_TNR
        }
    except Exception as e:
        return {
            'sample_size': len(results),
            'valid_evaluations': len(valid_results),
            'raw_passes': raw_passes,
            'raw_fails': len(unlabeled_preds) - raw_passes,
            'raw_pass_rate': raw_pass_rate,
            'bias_corrected_pass_rate': None,
            'confidence_lower': None,
            'confidence_upper': None,
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(description='Evaluate dietary preference adherence using LLM judge')
    parser.add_argument(
        'dataset',
        choices=['all', 'train', 'dev', 'test', 'raw_traces'],
        help='Which dataset(s) to evaluate'
    )
    parser.add_argument(
        '--parallel',
        type=int,
        default=1,
        help='Number of parallel workers (default: 1)'
    )
    parser.add_argument(
        '--sample',
        type=int,
        default=None,
        help='For raw_traces: number of samples to evaluate (default: 500)'
    )
    parser.add_argument(
        '--apply-bias-correction',
        action='store_true',
        help='Apply bias correction using judgy library (for unlabeled data)'
    )
    
    args = parser.parse_args()
    
    # Determine which datasets to process
    data_dir = Path(__file__).parent.parent / "data" / "dietary_prefs"
    datasets = []
    
    if args.dataset == 'all':
        datasets = [('train', data_dir / 'train_set.csv'),
                   ('dev', data_dir / 'dev_set.csv'),
                   ('test', data_dir / 'test_set.csv')]
    elif args.dataset == 'raw_traces':
        # Handle raw traces from hw3
        raw_traces_path = Path(__file__).parent.parent / "homeworks" / "hw3" / "data" / "raw_traces.csv"
        datasets = [('raw_traces', raw_traces_path)]
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
        
        # Determine sample size for raw_traces
        sample_size = None
        if dataset_name == 'raw_traces':
            sample_size = args.sample if args.sample else 500
        
        # Evaluate the dataset
        results = evaluate_dataset(dataset_path, num_workers=args.parallel, sample_size=sample_size)
        
        # Generate timestamped output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{dataset_name}_eval_results_{timestamp}.csv"
        output_path = output_dir / output_filename
        
        # Write results
        write_results(results, output_path)
        print(f"Results written to: {output_path}")
        
        # For unlabeled data (raw_traces), apply bias correction if requested
        if dataset_name == 'raw_traces' and args.apply_bias_correction:
            print("\n" + "="*60)
            print("BIAS CORRECTION ANALYSIS")
            print("="*60)
            
            bias_results = apply_bias_correction(results)
            
            if bias_results.get('error'):
                print(f"Error: {bias_results['error']}")
            else:
                print(f"Sample size:                        {bias_results['sample_size']}")
                print(f"Valid evaluations:                  {bias_results['valid_evaluations']}")
                print(f"Raw passes:                         {bias_results['raw_passes']}")
                print(f"Raw fails:                          {bias_results['raw_fails']}")
                print(f"\nTest Set Performance (hardcoded):")
                print(f"  TPR: {bias_results['test_tpr']:.3f}")
                print(f"  TNR: {bias_results['test_tnr']:.3f}")
                print(f"\n" + "-"*60)
                print(f"Raw pass rate (before correction): {bias_results['raw_pass_rate']:.3f} ({bias_results['raw_pass_rate']*100:.1f}%)")
                
                if bias_results.get('bias_corrected_pass_rate') is not None:
                    print(f"Bias-corrected pass rate:          {bias_results['bias_corrected_pass_rate']:.3f} ({bias_results['bias_corrected_pass_rate']*100:.1f}%)")
                    print(f"95% Confidence interval:           [{bias_results['confidence_lower']:.3f}, {bias_results['confidence_upper']:.3f}]")
                    print(f"Confidence interval (percentage):  [{bias_results['confidence_lower']*100:.1f}%, {bias_results['confidence_upper']*100:.1f}%]")
                    print(f"Adjustment from raw:               {bias_results['adjustment']:.3f} ({bias_results['adjustment']*100:.1f} percentage points)")
                print("="*60)
        else:
            # Calculate and display standard metrics for labeled data
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