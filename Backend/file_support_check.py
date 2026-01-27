import pandas as pd
import io
from pathlib import Path
from typing import Optional

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    '.csv', '.txt', '.data', '.tsv',
    '.xlsx', '.xls', '.xlsm', '.xlsb', '.odf', '.ods', '.odt',
    '.json', '.html', '.htm', '.xml',
    '.parquet', '.feather', '.fea',
    '.pkl', '.pickle', '.h5', '.hdf5',
    '.sas7bdat', '.xport', '.sav', '.dta', '.orc', '.dat'
}


def validate_and_load(file_content: bytes, filename: str) -> dict:
    """
    Validates and loads file bytes into a DataFrame.
    
    Returns:
        dict with keys:
            - is_valid: bool
            - extension: str
            - filename: str
            - error: str | None
    """
    extension = Path(filename).suffix.lower()
    result = {
        "is_valid": False,
        "extension": extension,
        "filename": filename,
        "error": None
    }
    
    # Check if extension is supported
    if extension not in SUPPORTED_EXTENSIONS:
        result["error"] = f"Unsupported file extension: {extension}"
        return result
    
    # Create a stream from the bytes
    stream = io.BytesIO(file_content)
    df: Optional[pd.DataFrame] = None

    try:
        match extension:
            case '.csv' | '.txt' | '.data':
                df = pd.read_csv(stream, nrows=5)
            case '.tsv':
                df = pd.read_table(stream, nrows=5)
            case '.xlsx' | '.xls' | '.xlsm' | '.xlsb' | '.odf' | '.ods' | '.odt':
                df = pd.read_excel(stream, nrows=5)
            case '.json':
                df = pd.read_json(stream)
            case '.html' | '.htm':
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
                df = pd.read_sas(stream, nrows=5)
            case '.sav':
                df = pd.read_spss(stream)
            case '.dta':
                df = pd.read_stata(stream, nrows=5)
            case '.orc':
                df = pd.read_orc(stream)
            case '.dat':
                df = pd.read_fwf(stream, nrows=5)
        
        # If we got here, file is valid
        if df is not None:
            result["is_valid"] = True
        
        return result
             
    except Exception as e:
        result["error"] = f"Pandas could not read this file: {str(e)}"
        return result


def get_supported_extensions() -> list[str]:
    """Returns list of supported file extensions."""
    return sorted(list(SUPPORTED_EXTENSIONS))


if __name__ == "__main__":
    # Test example
    print("Supported extensions:", get_supported_extensions())