from backend.application import application

from backend.application import db, User, UserRole
from sqlalchemy.exc import IntegrityError

from flask import redirect, url_for, render_template, flash

from werkzeug.security import generate_password_hash

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, RadioField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp


class RegistrationForm(FlaskForm):
    username = StringField("Логин", validators=[
        DataRequired(message="Логин обязателен"),
        Length(min=3, max=20, message="Логин должен быть от 3 до 20 символов"),
        Regexp("^[A-Za-z0-9_]+$", message="Логин может содержать только буквы, цифры и подчеркивания")
    ])

    password = PasswordField("Пароль", validators=[
        DataRequired(message="Пароль обязателен"),
        Length(min=6, message="Пароль должен быть не менее 6 символов")
    ])

    role = RadioField("Роль", choices=[
        ("interviewer", "Интервьюер"),
        ("interviewee", "Кандидат")
    ], validators=[DataRequired(message="Выберите роль")])

    submit = SubmitField("Зарегистрироваться")


@application.route("/registration", methods=["GET", "POST"])
async def registration_route():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        role = form.role.data

        user = User(
            username=username,
            password=generate_password_hash(password),
            role_id=db.session.execute(db.select(UserRole.id).where(UserRole.role == role)).scalar()
        )

        try:
            db.session.add(user)
            db.session.commit()

            flash("Регистрация успешна! Теперь вы можете войти.", "success")
            return redirect(url_for("login_route"))
        except IntegrityError:
            flash("Пользователь с таким логином уже существует", "error")

    return render_template("registration.html", form=form)
