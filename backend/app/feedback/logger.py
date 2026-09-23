from pathlib import Path
import csv
from datetime import datetime


class FeedbackLogger:

    def __init__(self, file_path: str | Path = "feedback_log.csv"):
        self.file_path = Path(file_path)

    def log(
        self,
        query: str,
        result: str,
        feedback: str,
    ):
        file_exists = self.file_path.exists()

        with self.file_path.open(
            "a",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.writer(file)

            if not file_exists:
                writer.writerow(
                    [
                        "timestamp",
                        "query",
                        "result",
                        "feedback",
                    ]
                )

            writer.writerow(
                [
                    datetime.now().isoformat(),
                    query,
                    result,
                    feedback,
                ]
            )