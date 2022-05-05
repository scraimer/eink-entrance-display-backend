from dataclasses import dataclass
from PIL import Image

@dataclass
class EinkImage:
    red : Image.Image
    black : Image.Image
