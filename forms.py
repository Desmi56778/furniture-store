from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, FloatField, IntegerField, SelectField, TextAreaField, SubmitField
from wtforms.validators import InputRequired, Email, Length, NumberRange, Optional
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms.validators import Optional, ValidationError

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Пароль', validators=[InputRequired()])

class RegisterForm(FlaskForm):
    name = StringField('Имя', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Пароль', validators=[InputRequired(), Length(min=6)])
    name = StringField('ФИО', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), Email()])
    phone = StringField('Номер телефона', validators=[InputRequired()])
    password = PasswordField('Пароль', validators=[InputRequired(), Length(min=6)])

class ProductForm(FlaskForm):
    name = StringField('Название', validators=[InputRequired()])
    description = TextAreaField('Описание')
    price = FloatField('Цена', validators=[InputRequired(), NumberRange(min=0)])
    stock = IntegerField('Остаток', validators=[InputRequired(), NumberRange(min=0)])
    category = SelectField('Категория', coerce=int, validators=[InputRequired()])
    image = FileField('Изображение товара', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Допустимы только изображения (jpg, jpeg, png, webp)')
    ])
    submit = SubmitField('Сохранить')

class RequestForm(FlaskForm):
    subject = StringField('Тема запроса', validators=[InputRequired()])
    body = TextAreaField('Текст запроса', validators=[InputRequired()])
    images = MultipleFileField('Прикрепить фото (до 5 шт.)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Только изображения!')
    ])
    submit = SubmitField('Отправить запрос')

    def validate_images(self, field):
        if len(field.data) > 5:
            raise ValidationError('Можно прикрепить не более 5 изображений.')

class ProfileForm(FlaskForm):
    name = StringField('ФИО', validators=[InputRequired()])
    phone = StringField('Номер телефона', validators=[InputRequired()])
    address = TextAreaField('Адрес доставки', validators=[InputRequired()])
    payment_method = SelectField('Способ платежа', choices=[
        ('карта', 'Карта'),
        ('наличные', 'Наличные средства'),
        ('чек оплаты', 'Предъявить чек оплаты')
    ], validators=[InputRequired()])
    avatar = FileField('Фото профиля', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Только изображения!')
    ])
    submit = SubmitField('Сохранить')

class ReplenishForm(FlaskForm):
    amount = FloatField('Сумма пополнения', validators=[InputRequired(), NumberRange(min=1)])
    payment_method = SelectField('Способ оплаты', choices=[
        ('card', 'Банковская карта'),
        ('phone', 'Перевод по номеру телефона')
    ], validators=[InputRequired()])
    # Поля карты (появляются, только если выбран способ "card")
    card_number = StringField('Номер карты')
    card_expiry = StringField('Срок действия (ММ/ГГ)')
    card_cvv = StringField('CVV')
    # Для перевода по телефону – просто информация, никаких дополнительных полей
    submit = SubmitField('Отправить запрос на пополнение')