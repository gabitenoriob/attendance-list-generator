import os
from flask_sqlalchemy import SQLAlchemy
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
db = SQLAlchemy()
