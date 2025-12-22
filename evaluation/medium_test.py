"""
Medium-scale test with 50 samples - more comprehensive validation
"""

import sys
import os
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.run_swde_evaluation import SWDEEvaluationRunner


def medium_test():
    """Run a medium test with 50 HTML files."""

    dataset_dir = "/Users/brown/Projects/AILabProject/web2json-agent/evaluationSet"
    groundtruth_dir = "/Users/brown/Projects/AILabProject/web2json-agent/evaluationSet/groundtruth"
    output_dir = "/Users/brown/Projects/AILabProject/web2json-agent/swde_medium_test"

    vertical = "book"
    website = "abebooks"
    sample_size = 50

    print("="*80)
    print(f"SWDE Medium Test - Processing {sample_size} samples")
    print("="*80)
    print(f"\nVertical: {vertical}")
    print(f"Website: {website}")
    print()

    # Create a temporary directory with sample HTML files
    source_dir = Path(dataset_dir) / "book" / f"book-{website}(2000)"
    temp_dir = Path(output_dir) / "temp_html"
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"Copying {sample_size} sample HTML files...")
    html_files = sorted(list(source_dir.glob("*.htm")))[:sample_size]
    for html_file in html_files:
        shutil.copy(html_file, temp_dir / html_file.name)
    print(f"✅ Copied {len(html_files)} files to {temp_dir}")

    # Create modified runner
    runner = SWDEEvaluationRunner(
        dataset_dir=str(temp_dir.parent),
        groundtruth_dir=groundtruth_dir,
        output_root=output_dir
    )

    # Override the get_html_directory method to use our temp dir
    original_method = runner.get_html_directory
    def custom_get_html_directory(v, w):
        return temp_dir
    runner.get_html_directory = custom_get_html_directory

    try:
        print("\n" + "="*80)
        print(f"Running agent on {sample_size} HTML files...")
        print("="*80)

        # Run agent
        agent_output_dir = runner.run_agent(vertical, website)

        print("\n" + "="*80)
        print("Evaluating results...")
        print("="*80)

        # Evaluate
        results = runner.evaluate_website(vertical, website, agent_output_dir)

        # Generate reports
        runner.generate_reports(vertical, website, results)

        print("\n" + "="*80)
        print("MEDIUM TEST COMPLETED!")
        print("="*80)
        print(f"\nResults for {vertical}/{website} ({sample_size} samples):")
        print(f"  Precision: {results['overall_metrics']['precision']:.2%}")
        print(f"  Recall:    {results['overall_metrics']['recall']:.2%}")
        print(f"  F1 Score:  {results['overall_metrics']['f1']:.2%}")
        print(f"\nPer-Attribute Metrics:")
        for attr, metrics in results['attribute_metrics'].items():
            print(f"  {attr:20s} - Precision: {metrics['precision']:.2%}, Recall: {metrics['recall']:.2%}, F1: {metrics['f1']:.2%}")

        print(f"\nStatistics:")
        print(f"  Total pages:     {results['statistics']['total_pages']}")
        print(f"  Evaluated pages: {results['statistics']['evaluated_pages']}")
        print(f"  Errors:          {results['statistics']['errors']}")

        print(f"\nReports saved to: {output_dir}/{vertical}/{website}/evaluation/")
        print(f"  - report.html")
        print(f"  - evaluation_charts.png")
        print(f"  - results.json")
        print(f"  - summary.csv")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup temp directory
        print(f"\nCleaning up temporary files...")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    success = medium_test()
    sys.exit(0 if success else 1)
