from enum import Enum

class SearchType(str, Enum):
  TEXT = "TEXT"
  IMAGE = "IMAGE"
  MULTIMODAL = "MULTIMODAL"