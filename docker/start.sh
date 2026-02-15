#!/bin/bash
set -e

echo "Initializing database tables..."
python -c "
from api.database.connection import init_database, DatabaseManager
from api.database.models import Base
from api.config import settings

db = DatabaseManager(settings.DATABASE_URL)
Base.metadata.create_all(bind=db.engine)
print('Database tables created/verified successfully')
db.close()
"

echo "Starting API server..."
exec uvicorn api.main:app --host 0.0.0.0 --port 3010 --workers 4
