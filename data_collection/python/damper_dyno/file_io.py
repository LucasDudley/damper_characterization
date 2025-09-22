import csv
import datetime

def save_test_data(data, filename=None):
    """
    Save test data to CSV. If filename is None, generate one using current date and time.
    """

    # If no filename is provided, create one with the current date and time
    if filename is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"damper_test_{timestamp}.csv"

    # create the file in write mode
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)

        # Write all rows of data to the CSV file
        writer.writerow(["Timestamp", "Force", "Displacement", "Temperature"])
        writer.writerows(data)

