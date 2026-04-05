import os
from typing import Dict, List

import matplotlib.pyplot as plt


def compute_placement_accuracy(samples_by_category: Dict[str, List[float]]) -> Dict[str, float]:
    """
    Compute mean placement accuracy per category.

    samples_by_category maps category -> list of per-frame accuracies in [0, 100].
    Returns category -> mean accuracy.
    """
    mean_by_category: Dict[str, float] = {}
    for category, samples in samples_by_category.items():
        if not samples:
            mean_by_category[category] = 0.0
            continue
        mean_by_category[category] = sum(samples) / float(len(samples))
    return mean_by_category


def plot_bar_chart(values_by_category: Dict[str, float], title: str, ylabel: str, output_path: str) -> None:
    categories = list(values_by_category.keys())
    values = [values_by_category[c] for c in categories]

    plt.figure(figsize=(8, 4.5))
    bars = plt.bar(categories, values, color=["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f"])
    plt.ylim(0, 100)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(axis="y", linestyle=":", linewidth=0.7, alpha=0.7)

    for bar, value in zip(bars, values):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, height + 1, f"{value:.1f}%", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()


def main() -> None:
    # Example/mock frame-wise placement accuracy per category (0..100). Replace with your measurements.
    mock_samples = {
        "Glasses": [90, 92, 95, 94, 93, 92, 91, 93, 94, 95],
        "Hats": [86, 88, 89, 90, 89, 88, 90, 91, 89, 88],
        "Necklace": [82, 84, 86, 87, 85, 86, 85, 84, 86, 87],
        "Dress": [78, 81, 82, 83, 82, 81, 82, 83, 84, 83],
    }

    mean_accuracy = compute_placement_accuracy(mock_samples)

    output_dir = os.path.join("static", "images")
    output_path = os.path.join(output_dir, "placement_accuracy_bar.png")

    plot_bar_chart(
        values_by_category=mean_accuracy,
        title="Placement Accuracy by Category",
        ylabel="Accuracy (%)",
        output_path=output_path,
    )

    print(f"Saved bar chart to: {output_path}")


if __name__ == "__main__":
    main()



