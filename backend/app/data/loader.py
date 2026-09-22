from pathlib import Path
import pandas as pd

class CSVLoader:
    """Load and profile CSV datasets."""
    def load(self,file_path:str | Path)->pd.DataFrame:
        path=Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")
        if path.suffix.lower()!=".csv":
            raise ValueError("Only CSV files are supported.")

        df=pd.read_csv(file_path,sep=",")
        if df.empty:
            raise ValueError("The uploaded CSV is empty.")
        return df
    def profile(self,df:pd.DataFrame)->dict:
        """Create schema metadata for the query planner."""
        columns=[]
        for column in df.columns:
            series=df[column]

            columns.append(
                {
                    "name":column,
                    "dtype":str(series.dtype),
                    "nullable":bool(series.isna().any()),
                    "unique_values": int(series.nunique(dropna=True)),
                    "sample_values":series.dropna().head(5).tolist()
                }
            )
        return{
            "row_count":len(df),
            "column_count":len(df.columns),
            "columns":columns
        }    

    