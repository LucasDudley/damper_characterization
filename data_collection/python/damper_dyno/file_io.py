import csv
import datetime

def save_test_data(data, filename=None):
    """
    Save test data to CSV. If filename is None, generate one using current date and time.
    """
    if filename is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"damper_test_{timestamp}.csv"

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "AI0", "AI1", "AI2"])
        writer.writerows(data)

