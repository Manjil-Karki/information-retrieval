import os
from pathlib import Path
from starlette.config import Config


config = Config(".env")


TARGET_URL = "https://pureportal.coventry.ac.uk/en/organisations/ics-research-centre-for-computational-science-and-mathematical-mo/persons/"

DATA_PATH = config("DATA_PATH", default="data/")
os.makedirs(DATA_PATH, exist_ok=True)

OUTPUT_FILE = DATA_PATH + config("OUTPUT_FILE", default="publications.json")
CLEAN_FILE = DATA_PATH + config("CLEAN_FILE", default="clean_publications.json")
INDEX_PATH = DATA_PATH + config("INDEX_PATH", default="index.pkl")

BASE_URL = config("BASE_URL", default="https://pureportal.coventry.ac.uk")
ROBOTS_URL = f"{BASE_URL}/robots.txt"

USER_AGENT = config("USER_AGENT", default="IncrementalPureCrawler/5.0")
HEADERS = {"User-Agent": USER_AGENT}

DEPARTMENT_KEYWORDS = config(
    "DEPARTMENT_KEYWORDS", 
    cast=lambda v: [k.strip() for k in v.split(",")],
    default="computational science,mathematical modelling"
)

PERSONS_CSV = Path(DATA_PATH) / config("PERSONS_CSV", default="persons.csv")
PUBLICATIONS_CSV = Path(DATA_PATH) / config("PUBLICATIONS_CSV", default="publications.csv")
DATA_JSON = Path(DATA_PATH) / config("DATA_JSON", default="data.json")
PROCESSED_DOCUMENTS = Path(DATA_PATH) / config("PROCESSED_DOCUMENTS", default="processed_documents.json")

PERSON_CONCURRENCY = config("PERSON_CONCURRENCY", cast=int, default=6)
PUB_CONCURRENCY = config("PUB_CONCURRENCY", cast=int, default=16)

MIN_DELAY = config("MIN_DELAY", cast=float, default=0.2)
MAX_DELAY = config("MAX_DELAY", cast=float, default=0.7)