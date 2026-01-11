from typing import Annotated
from fastapi import Depends
from sqlmodel import Session

from .db import get_session, get_graph_db_session
from ..graph_db import Neo4jHelper

# PostgreSQL Session Dependency
SessionDep = Annotated[Session, Depends(get_session)]

# Neo4j Helper Dependency
GraphDatabaseSessionDep = Annotated[Neo4jHelper, Depends(get_graph_db_session)]
