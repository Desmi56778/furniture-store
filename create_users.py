from app import app, db
from models import User

with app.app_context():
    # Создаём админа
    admin = User(email='admin@mail.ru', name='Админ', role='admin')
    admin.set_password('admin')

    # Создаём сотрудника
    emp = User(email='emp@mail.ru', name='Сотрудник', role='employee')
    emp.set_password('emp')

    db.session.add_all([admin, emp])
    db.session.commit()
    print("Созданы тестовые пользователи: admin и employee")