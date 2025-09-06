from backend.application import application

from backend.application import db, User

from flask import redirect, url_for, render_template, session, flash

from werkzeug.security import check_password_hash

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField("Логин", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")


@application.route("/login", methods=["GET", "POST"])
async def login_route():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = db.session.execute(
            db.select(User).where(User.username == username)
        ).scalar()

        if user is not None and check_password_hash(user.password, password):
            session.permanent = True
            session["user_id"] = user.id
            session["username"] = user.username
            session["role_id"] = user.role_id
            session["telegram"] = user.telegram

            flash("Вход выполнен успешно!", "success")
            return redirect(url_for("index_route"))
        else:
            flash("Неверный логин или пароль", "error")

    return render_template("login.html", form=form)


@application.route("/logout", methods=["GET"])
def logout_route():
    session.clear()
    flash('Вы вышли из системы', 'success')
    return redirect(url_for("login_route"))
