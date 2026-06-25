from app import app, db
from models import Category, Product

def seed():
    with app.app_context():
        db.create_all()
        # Категории
        cats = ['Диваны', 'Кровати', 'Столы', 'Стулья', 'Шкафы']
        for c in cats:
            if not Category.query.filter_by(name=c).first():
                db.session.add(Category(name=c))
        db.session.commit()

        # 15 товаров на каждую категорию (пример)
        products = []
        for cat_name in cats:
            cat = Category.query.filter_by(name=cat_name).first()
            for i in range(1, 16):
                p = Product(
                    name=f'{cat_name} модель {i}',
                    description=f'Комфортный {cat_name.lower()} для дома и офиса.',
                    price=round(5000 + i * 1234, 2),
                    stock=20 + i,
                    category_id=cat.id
                )
                products.append(p)
        db.session.add_all(products)
        db.session.commit()
        print("База заполнена: 5 категорий, 75 товаров")

if __name__ == '__main__':
    seed()