import pytest
import mimetypes
from src.utils import read_file

def test_read_txt_success(tmpdir):
    file_path = tmpdir.join("test.txt")
    file_path.write("Hello, World!")
    
    result = read_file(str(file_path))
    assert result["content"] == b"Hello, World!"
    assert result["file_type"] == "text/plain"
    assert result["encoding"] is None


def test_read_geojson_success(tmpdir):
    # Ajouter le type MIME pour les fichiers GeoJSON
    mimetypes.add_type('application/geo+json', '.geojson')
    
    # Contenu GeoJSON exemple
    geojson_content = '''
    {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [102.0, 0.5]
                },
                "properties": {
                    "prop0": "value0"
                }
            }
        ]
    }
    '''
    
    file_path = tmpdir.join("test.geojson")
    file_path.write(geojson_content)
    
    result = read_file(str(file_path))
    assert result["content"] == geojson_content.encode()
    assert result["file_type"] == "application/geo+json"
    assert result["encoding"] is None


def test_read_file_not_found():
    # Appeler la fonction read_file avec un chemin de fichier inexistant
    result = read_file("non_existent_file.txt")
    
    # Vérifier le message d'erreur
    assert result["error"] == "File not found"