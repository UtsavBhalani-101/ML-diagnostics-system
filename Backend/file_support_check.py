import pandas as pd
import io
from pathlib import Path

def validate_and_load(file_content: bytes, filename: str):
    """
    Tries to load the file bytes into a DataFrame to verify support.
    """
    extension = Path(filename).suffix.lower()
    # Create a stream from the bytes
    stream = io.BytesIO(file_content)

    try:
        match extension:
            case '.csv' | '.txt' | '.data':
                return pd.read_csv(stream, nrows=1)
            case '.tsv':
                return pd.read_table(stream, nrows=1)
            case '.xlsx' | '.xls' | '.xlsm' | '.xlsb' | '.odf' | '.ods' | '.odt':
                return pd.read_excel(stream, nrows=1)
            case '.json':
                return pd.read_json(stream)
            case '.html' | '.htm':
                # read_html returns a list of DataFrames
                dfs = pd.read_html(stream)
                if dfs:
                    df = dfs[0]
                else:
                    raise ValueError("No tables found in HTML file.")
            case '.xml':
                df = pd.read_xml(stream)
            case '.parquet':
                df = pd.read_parquet(stream)
            case '.feather' | '.fea':
                df = pd.read_feather(stream)
            case '.pkl' | '.pickle':
                df = pd.read_pickle(stream)
            case '.h5' | '.hdf5':
                df = pd.read_hdf(stream)
            case '.sas7bdat' | '.xport':
                df = pd.read_sas(stream, nrows=1)
            case '.sav':
                df = pd.read_spss(stream)
            case '.dta':
                df = pd.read_stata(stream, nrows=1)
            case '.orc':
                df = pd.read_orc(stream)
            case '.dat':
                df = pd.read_fwf(stream, nrows=1)
            case _:
                raise ValueError(f"Unsupported file extension: {extension}")
             
    except Exception as e:
        raise ValueError(f"Pandas could not read this file: {str(e)}")

if __name__ == "__main__":
    validate_and_load()