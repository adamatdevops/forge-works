"""CLI script for training the template recommendation model.

Usage:
    python -m app.ml.train
    python -m app.ml.train --samples 1000 --output models/custom_model.pkl
"""

import argparse
import sys

from app.core.config import settings
from app.ml.training import generate_training_data, save_training_data, train_model


def main() -> int:
    """Main training script entry point."""
    parser = argparse.ArgumentParser(description="Train the template recommendation model")
    parser.add_argument(
        "--samples",
        type=int,
        default=750,
        help="Number of training samples to generate (default: 750)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=settings.ml_model_path,
        help=f"Output path for trained model (default: {settings.ml_model_path})",
    )
    parser.add_argument(
        "--save-data",
        type=str,
        default=None,
        help="Optional path to save training data as JSON",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of data for testing (default: 0.2)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("ForgeWorks Template Recommender - Model Training")
    print("=" * 60)
    print()

    # Generate training data
    print(f"Generating {args.samples} training examples...")
    dataset = generate_training_data(n_samples=args.samples, seed=args.seed)
    print(f"  Generated {dataset.size} examples")
    print("  Label distribution:")
    for label, count in sorted(dataset.label_distribution().items()):
        print(f"    {label}: {count}")
    print()

    # Optionally save training data
    if args.save_data:
        print(f"Saving training data to {args.save_data}...")
        save_training_data(dataset, args.save_data)
        print("  Done")
        print()

    # Train model
    print("Training model...")
    print(f"  Test size: {args.test_size * 100:.0f}%")
    print(f"  Random seed: {args.seed}")

    try:
        metrics = train_model(
            dataset=dataset,
            output_path=args.output,
            test_size=args.test_size,
            random_state=args.seed,
        )
    except ImportError as e:
        print()
        print("ERROR: scikit-learn is required for training.")
        print("Install it with: pip install scikit-learn")
        print(f"Details: {e}")
        return 1

    print()
    print("Training Results:")
    print("-" * 40)
    print(f"  Accuracy: {metrics['accuracy']:.2%}")
    print(f"  Training samples: {metrics['n_train']}")
    print(f"  Test samples: {metrics['n_test']}")
    print()

    # Print per-class metrics
    report = metrics["classification_report"]
    print("Per-Template Performance:")
    print("-" * 40)
    for label in sorted(report.keys()):
        if label in ("accuracy", "macro avg", "weighted avg"):
            continue
        m = report[label]
        print(f"  {label}:")
        print(f"    Precision: {m['precision']:.2%}")
        print(f"    Recall:    {m['recall']:.2%}")
        print(f"    F1-score:  {m['f1-score']:.2%}")
        print()

    print(f"Model saved to: {metrics['model_path']}")
    print()
    print("=" * 60)
    print("Training complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
