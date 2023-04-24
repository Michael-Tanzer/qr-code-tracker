from flask_sqlalchemy import SQLAlchemy

import base64


db = SQLAlchemy()


def string_to_base64(s):
    return base64.b64encode(s.encode('utf-8')).decode('utf-8')
