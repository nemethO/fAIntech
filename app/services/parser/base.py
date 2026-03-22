from abc import ABC, abstractmethod
import pandas as pd


class BaseBankParser(ABC):
    """Abstract base class for bank statement parsers.

    Each bank parser must implement the `parse` method that returns
    a standardized DataFrame with these columns:
        - date (datetime)
        - amount (float)
        - currency (str)
        - partner (str)
        - description (str)
        - is_income (bool)
    """

    REQUIRED_COLUMNS = ['date', 'amount', 'currency', 'partner', 'description', 'is_income']

    @abstractmethod
    def parse(self, file_path: str) -> pd.DataFrame:
        """Parse a bank statement file and return standardized DataFrame."""
        pass

    def validate(self, df: pd.DataFrame) -> bool:
        """Check that all required columns are present."""
        return all(col in df.columns for col in self.REQUIRED_COLUMNS)
