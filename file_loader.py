import glob
import os

def load_xml_files(directory='data', pattern='*.xml'):
    # Recursively search for XML files
    xml_file_paths = glob.glob(os.path.join(directory, '**', pattern), recursive=True)
    if not xml_file_paths:
        raise FileNotFoundError(f"No XML files found in {directory}")
    return xml_file_paths

# Usage example:
if __name__ == '__main__':
    files = load_xml_files()
    print("XML files found:", files)
