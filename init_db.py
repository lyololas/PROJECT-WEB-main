from app import app, db, User, Product
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@swagcraft.com').first():
            admin = User(
                username='admin',
                email='admin@swagcraft.com',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
        Product.query.delete()
        db.session.commit()
        if not Product.query.first():
            products = [
                Product(
                    name='Толстовка "Enderman"',
                    description='Черная толстовка с принтом Эндермена',
                    price=3299.99,
                    category='толстовки',
                    image='enderman_hoodie.jpg',
                    stock=3
                ),
                Product(
                    name='Футболка "Creeper"',
                    description='Футболка с изображением Крипера',
                    price=1499.99,
                    category='футболки',
                    image='creeper_tshirt.jpg',
                    stock=10
                ),
                Product(
                    name='Толстовка "Diamond Sword"',
                    description='Голубая толстовка с мечом',
                    price=2999.99,
                    category='толстовки',
                    image='diamond_hoodie.jpg',
                    stock=5
                )
            ]
            for product in products:
                db.session.add(product)
        db.session.commit()
        print("База данных успешно инициализирована!")

if __name__ == '__main__':
    init_db() 