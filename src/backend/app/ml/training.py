"""Training data generation and model training utilities."""

import json
import pickle
import random
from pathlib import Path

import numpy as np

from app.schemas.ml import (
    DatabaseType,
    ProgrammingLanguage,
    TemplateType,
    TrainingDataset,
    TrainingExample,
    WorkloadFeatures,
    WorkloadType,
)


def generate_training_data(
    n_samples: int = 750,
    seed: int = 42,
) -> TrainingDataset:
    """Generate synthetic training data for template recommendation.

    Args:
        n_samples: Total number of training examples to generate
        seed: Random seed for reproducibility

    Returns:
        TrainingDataset with generated examples
    """
    random.seed(seed)
    np.random.seed(seed)

    examples: list[TrainingExample] = []

    # Distribution: ~150 examples per template
    samples_per_template = n_samples // 5

    # Generate examples for each template
    examples.extend(_generate_python_microservice_examples(samples_per_template))
    examples.extend(_generate_node_microservice_examples(samples_per_template))
    examples.extend(_generate_worker_examples(samples_per_template))
    examples.extend(_generate_ml_pipeline_examples(samples_per_template))
    examples.extend(_generate_frontend_examples(samples_per_template))

    # Add some edge cases and noise
    n_edge = n_samples - len(examples)
    if n_edge > 0:
        examples.extend(_generate_edge_cases(n_edge))

    # Shuffle
    random.shuffle(examples)

    return TrainingDataset(
        examples=examples,
        version="1.0.0",
        description=f"Synthetic training data with {len(examples)} examples",
    )


def _generate_python_microservice_examples(n: int) -> list[TrainingExample]:
    """Generate examples for microservice-python template."""
    examples = []
    frameworks = ["fastapi", "flask", "django", "starlette", None]

    for _ in range(n):
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,
            framework=random.choice(frameworks),
            workload_type=random.choice([
                WorkloadType.API,
                WorkloadType.API,
                WorkloadType.API,  # Weight towards API
                WorkloadType.WORKER,
            ]),
            needs_database=random.random() > 0.2,
            database_type=random.choice([
                DatabaseType.POSTGRESQL,
                DatabaseType.POSTGRESQL,
                DatabaseType.POSTGRESQL,  # Weight towards PostgreSQL
                DatabaseType.MYSQL,
                DatabaseType.REDIS,
            ]) if random.random() > 0.2 else DatabaseType.NONE,
            needs_queue=random.random() > 0.6,
            needs_cache=random.random() > 0.4,
            needs_gpu=False,
            expected_rps=random.randint(10, 5000),
            expected_memory_mb=random.randint(256, 4096),
            team_size=random.randint(2, 30),
            compliance_required=random.random() > 0.7,
        )
        examples.append(TrainingExample(
            features=features,
            label=TemplateType.MICROSERVICE_PYTHON,
        ))

    return examples


def _generate_node_microservice_examples(n: int) -> list[TrainingExample]:
    """Generate examples for microservice-node template."""
    examples = []
    frameworks = ["express", "fastify", "nestjs", "koa", None]

    for _ in range(n):
        lang = random.choice([
            ProgrammingLanguage.JAVASCRIPT,
            ProgrammingLanguage.TYPESCRIPT,
            ProgrammingLanguage.TYPESCRIPT,  # Weight towards TypeScript
        ])
        features = WorkloadFeatures(
            language=lang,
            framework=random.choice(frameworks),
            workload_type=random.choice([
                WorkloadType.API,
                WorkloadType.API,
                WorkloadType.API,
                WorkloadType.WORKER,
            ]),
            needs_database=random.random() > 0.3,
            database_type=random.choice([
                DatabaseType.MONGODB,
                DatabaseType.MONGODB,
                DatabaseType.POSTGRESQL,
                DatabaseType.REDIS,
            ]) if random.random() > 0.3 else DatabaseType.NONE,
            needs_queue=random.random() > 0.5,
            needs_cache=random.random() > 0.4,
            needs_gpu=False,
            expected_rps=random.randint(100, 10000),
            expected_memory_mb=random.randint(256, 2048),
            team_size=random.randint(2, 25),
            compliance_required=random.random() > 0.8,
        )
        examples.append(TrainingExample(
            features=features,
            label=TemplateType.MICROSERVICE_NODE,
        ))

    return examples


def _generate_worker_examples(n: int) -> list[TrainingExample]:
    """Generate examples for worker-service template."""
    examples = []

    for _ in range(n):
        lang = random.choice([
            ProgrammingLanguage.PYTHON,
            ProgrammingLanguage.PYTHON,
            ProgrammingLanguage.GO,
            ProgrammingLanguage.JAVA,
        ])
        features = WorkloadFeatures(
            language=lang,
            framework=random.choice(["celery", "rq", "dramatiq", None]),
            workload_type=random.choice([
                WorkloadType.WORKER,
                WorkloadType.WORKER,
                WorkloadType.CRON,
                WorkloadType.BATCH,
            ]),
            needs_database=random.random() > 0.5,
            database_type=random.choice([
                DatabaseType.REDIS,
                DatabaseType.REDIS,
                DatabaseType.POSTGRESQL,
                DatabaseType.NONE,
            ]),
            needs_queue=random.random() > 0.2,  # Usually needs queue
            needs_cache=random.random() > 0.6,
            needs_gpu=False,
            expected_rps=random.randint(1, 500),  # Lower RPS for workers
            expected_memory_mb=random.randint(512, 8192),
            team_size=random.randint(1, 15),
            compliance_required=random.random() > 0.8,
        )
        examples.append(TrainingExample(
            features=features,
            label=TemplateType.WORKER_SERVICE,
        ))

    return examples


def _generate_ml_pipeline_examples(n: int) -> list[TrainingExample]:
    """Generate examples for ml-pipeline template."""
    examples = []

    for _ in range(n):
        features = WorkloadFeatures(
            language=ProgrammingLanguage.PYTHON,  # ML is almost always Python
            framework=random.choice(["pytorch", "tensorflow", "scikit-learn", None]),
            workload_type=random.choice([
                WorkloadType.ML_PIPELINE,
                WorkloadType.ML_PIPELINE,
                WorkloadType.BATCH,
                WorkloadType.WORKER,
            ]),
            needs_database=random.random() > 0.4,
            database_type=random.choice([
                DatabaseType.POSTGRESQL,
                DatabaseType.REDIS,
                DatabaseType.NONE,
            ]),
            needs_queue=random.random() > 0.5,
            needs_cache=random.random() > 0.5,
            needs_gpu=random.random() > 0.3,  # Often needs GPU
            expected_rps=random.randint(1, 100),  # Low RPS for ML
            expected_memory_mb=random.randint(4096, 32768),  # High memory
            team_size=random.randint(2, 20),
            compliance_required=random.random() > 0.6,
        )
        examples.append(TrainingExample(
            features=features,
            label=TemplateType.ML_PIPELINE,
        ))

    return examples


def _generate_frontend_examples(n: int) -> list[TrainingExample]:
    """Generate examples for frontend-app template."""
    examples = []
    frameworks = ["nextjs", "react", "vue", "angular", "svelte"]

    for _ in range(n):
        lang = random.choice([
            ProgrammingLanguage.TYPESCRIPT,
            ProgrammingLanguage.TYPESCRIPT,
            ProgrammingLanguage.JAVASCRIPT,
        ])
        features = WorkloadFeatures(
            language=lang,
            framework=random.choice(frameworks),
            workload_type=WorkloadType.FRONTEND,
            needs_database=False,  # Frontend typically doesn't need direct DB
            database_type=DatabaseType.NONE,
            needs_queue=False,
            needs_cache=random.random() > 0.7,  # CDN caching
            needs_gpu=False,
            expected_rps=random.randint(100, 50000),  # High RPS for static
            expected_memory_mb=random.randint(128, 1024),  # Low memory
            team_size=random.randint(2, 20),
            compliance_required=random.random() > 0.9,
        )
        examples.append(TrainingExample(
            features=features,
            label=TemplateType.FRONTEND_APP,
        ))

    return examples


def _generate_edge_cases(n: int) -> list[TrainingExample]:
    """Generate ambiguous/edge case examples."""
    examples = []

    for _ in range(n):
        # Random mix that could go multiple ways
        lang = random.choice(list(ProgrammingLanguage))
        workload = random.choice(list(WorkloadType))

        # Determine reasonable label based on some rules
        if workload == WorkloadType.FRONTEND:
            label = TemplateType.FRONTEND_APP
        elif workload == WorkloadType.ML_PIPELINE:
            label = TemplateType.ML_PIPELINE
        elif workload in (WorkloadType.WORKER, WorkloadType.CRON, WorkloadType.BATCH):
            label = TemplateType.WORKER_SERVICE
        elif lang == ProgrammingLanguage.PYTHON:
            label = TemplateType.MICROSERVICE_PYTHON
        elif lang in (ProgrammingLanguage.JAVASCRIPT, ProgrammingLanguage.TYPESCRIPT):
            label = TemplateType.MICROSERVICE_NODE
        else:
            label = random.choice([
                TemplateType.MICROSERVICE_PYTHON,
                TemplateType.WORKER_SERVICE,
            ])

        features = WorkloadFeatures(
            language=lang,
            framework=None,
            workload_type=workload,
            needs_database=random.choice([True, False]),
            database_type=random.choice(list(DatabaseType)),
            needs_queue=random.choice([True, False]),
            needs_cache=random.choice([True, False]),
            needs_gpu=random.choice([True, False]),
            expected_rps=random.randint(1, 10000),
            expected_memory_mb=random.randint(128, 16384),
            team_size=random.randint(1, 50),
            compliance_required=random.choice([True, False]),
        )

        examples.append(TrainingExample(
            features=features,
            label=label,
            weight=0.5,  # Lower weight for edge cases
        ))

    return examples


def features_to_vector(features: WorkloadFeatures) -> np.ndarray:
    """Convert WorkloadFeatures to numeric feature vector for training.

    Args:
        features: Input workload features

    Returns:
        Numpy array of numeric features
    """
    # Language encoding
    lang_map = {
        "python": 0, "javascript": 1, "typescript": 2,
        "go": 3, "java": 4, "rust": 5,
    }
    lang_idx = lang_map.get(features.language.value, 0)

    # Workload type encoding
    workload_map = {
        "api": 0, "worker": 1, "cron": 2,
        "ml-pipeline": 3, "frontend": 4, "batch": 5,
    }
    workload_idx = workload_map.get(features.workload_type.value, 0)

    # Database type encoding
    db_map = {
        "none": 0, "postgresql": 1, "mongodb": 2,
        "redis": 3, "mysql": 4,
    }
    db_idx = db_map.get(features.database_type.value, 0)

    return np.array([
        lang_idx,
        workload_idx,
        db_idx,
        1 if features.needs_database else 0,
        1 if features.needs_queue else 0,
        1 if features.needs_cache else 0,
        1 if features.needs_gpu else 0,
        min(features.expected_rps / 10000, 1.0),
        min(features.expected_memory_mb / 8192, 1.0),
        min(features.team_size / 100, 1.0),
        1 if features.compliance_required else 0,
    ])


def train_model(
    dataset: TrainingDataset,
    output_path: str | Path,
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict:
    """Train template recommendation model.

    Args:
        dataset: Training dataset
        output_path: Path to save trained model
        test_size: Fraction of data for testing
        random_state: Random seed for reproducibility

    Returns:
        Dictionary with training metrics
    """
    # Import sklearn here to avoid import errors if not installed
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.model_selection import train_test_split

    # Prepare data
    features_array = np.array([
        features_to_vector(ex.features)
        for ex in dataset.examples
    ])
    labels = np.array([ex.label.value for ex in dataset.examples])
    weights = np.array([ex.weight for ex in dataset.examples])

    # Split data
    x_train, x_test, y_train, y_test, w_train, _ = train_test_split(
        features_array, labels, weights,
        test_size=test_size,
        random_state=random_state,
        stratify=labels,
    )

    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(x_train, y_train, sample_weight=w_train)

    # Evaluate
    y_pred = model.predict(x_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)

    # Save model
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    feature_names = [
        "language", "workload_type", "database_type",
        "needs_database", "needs_queue", "needs_cache", "needs_gpu",
        "expected_rps_norm", "expected_memory_norm", "team_size_norm",
        "compliance_required",
    ]

    with open(output_path, "wb") as f:
        pickle.dump({
            "model": model,
            "feature_names": feature_names,
            "accuracy": accuracy,
            "version": "1.0.0",
        }, f)

    return {
        "accuracy": accuracy,
        "classification_report": report,
        "n_train": len(x_train),
        "n_test": len(x_test),
        "model_path": str(output_path),
    }


def save_training_data(dataset: TrainingDataset, output_path: str | Path) -> None:
    """Save training dataset to JSON file.

    Args:
        dataset: Training dataset to save
        output_path: Path to output JSON file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "version": dataset.version,
        "description": dataset.description,
        "examples": [
            {
                "features": ex.features.model_dump(),
                "label": ex.label.value,
                "weight": ex.weight,
            }
            for ex in dataset.examples
        ],
    }

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


def load_training_data(input_path: str | Path) -> TrainingDataset:
    """Load training dataset from JSON file.

    Args:
        input_path: Path to input JSON file

    Returns:
        TrainingDataset
    """
    with open(input_path) as f:
        data = json.load(f)

    examples = [
        TrainingExample(
            features=WorkloadFeatures(**ex["features"]),
            label=TemplateType(ex["label"]),
            weight=ex.get("weight", 1.0),
        )
        for ex in data["examples"]
    ]

    return TrainingDataset(
        examples=examples,
        version=data.get("version", "1.0.0"),
        description=data.get("description"),
    )
