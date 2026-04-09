# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base
from app.models.user import User
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.notification import Notification 