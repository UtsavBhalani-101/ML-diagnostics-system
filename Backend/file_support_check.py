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


def _load_dataframe_by_extension(source, extension: str, preview_mode: bool = False) -> pd.DataFrame:
    """
    Helper function to load DataFrame based on extension.
    DRY principle - single source of truth for file loading logic.
    
    Args:
        source: Either a file path (str) or BytesIO stream
        extension: File extension (e.g., '.csv', '.xlsx')
        preview_mode: If True, limit rows for preview (nrows=5 where supported)
        
    Returns:
        pd.DataFrame: Loaded data
        
    Raises:
        ValueError: If format not supported or file has issues
    """
    # Common kwargs for preview mode
    preview_kwargs = {'nrows': 5} if preview_mode else {}
    
    match extension:
        case '.csv' | '.txt' | '.data':
            return pd.read_csv(source, **preview_kwargs)
        case '.tsv':
            return pd.read_table(source, **preview_kwargs)
        case '.xlsx' | '.xls' | '.xlsm' | '.xlsb' | '.odf' | '.ods' | '.odt':
            return pd.read_excel(source, **preview_kwargs)
        case '.json':
            return pd.read_json(source)
        case '.html' | '.htm':
            dfs = pd.read_html(source)
            if dfs:
                return dfs[0]
            else:
                raise ValueError("No tables found in HTML file.")
        case '.xml':
            return pd.read_xml(source)
        case '.parquet':
            return pd.read_parquet(source)
        case '.feather' | '.fea':
            return pd.read_feather(source)
        case '.pkl' | '.pickle':
            return pd.read_pickle(source)
        case '.h5' | '.hdf5':
            return pd.read_hdf(source)
        case '.sas7bdat' | '.xport':
            return pd.read_sas(source, **preview_kwargs)
        case '.sav':
            return pd.read_spss(source)
        case '.dta':
            return pd.read_stata(source, **preview_kwargs)
        case '.orc':
            return pd.read_orc(source)
        case '.dat':
            return pd.read_fwf(source, **preview_kwargs)
        case _:
            raise ValueError(f"Handler not implemented for extension: {extension}")


def validate_and_load(file_content: bytes, filename: str) -> dict:
    """
    Validates and loads file bytes into a DataFrame (preview mode).
    
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

    try:
        # Use the helper function with preview mode
        df = _load_dataframe_by_extension(stream, extension, preview_mode=True)
        
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


def load_dataframe_from_file(file_path: str) -> pd.DataFrame:
    """
    Load a complete DataFrame from a file based on its extension.
    Universal data loader supporting all 28+ file formats.
    
    Args:
        file_path: Path to the data file
        
    Returns:
        pd.DataFrame: Loaded DataFrame
        
    Raises:
        ValueError: If file extension is not supported
        Exception: If file cannot be read
    """
    extension = Path(file_path).suffix.lower()
    
    # Check if extension is supported
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {extension}. Supported: {SUPPORTED_EXTENSIONS}")
    
    try:
        # Use the helper function without preview mode (full data)
        return _load_dataframe_by_extension(file_path, extension, preview_mode=False)
                
    except Exception as e:
        raise Exception(f"Failed to load {file_path}: {str(e)}")


if __name__ == "__main__":
    # Test example
    print("Supported extensions:", get_supported_extensions())