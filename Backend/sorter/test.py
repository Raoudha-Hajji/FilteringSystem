# test_filter.py
from filter import train_with_sbert, filter_csv

def test_filtering_pipeline():
    print("Training model...")
    acc = train_with_sbert("training_data")
    print(f"Validation accuracy: {acc:.2f}")

    print("Running filter...")
    result = filter_csv("tuneps_offers")
    print(f"Filtered rows:\n{result}")

if __name__ == "__main__":
    test_filtering_pipeline()
