from pony.orm import Database, Required, Json

from settings import DB_CONFIG
db = Database()
db.bind(**DB_CONFIG)


class UserState(db.Entity):
    """Состояние пользователя внутри сценария"""
    user_id = Required(str, unique=True)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)


class BaseApplications(db.Entity):
    """Заявки на поиск билетов"""
    today = Required(str)
    to_city = Required(str)
    from_city = Required(str)
    comments = Required(str)
    selected_flight = Required(str)
    number_of_passengers = Required(int)
    tell = Required(str)


db.generate_mapping(create_tables=True)