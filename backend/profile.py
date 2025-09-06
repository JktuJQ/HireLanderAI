from backend.application import application

from backend.application import db, User

from flask import redirect, url_for, render_template, session, flash

import os

from werkzeug.utils import secure_filename

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Regexp


class ProfileForm(FlaskForm):
    last_name = StringField("Фамилия", validators=[
        DataRequired(message="Фамилия обязательна"),
        Length(max=50, message="Фамилия не должна превышать 50 символов"),
        Optional()
    ])
    first_name = StringField("Имя", validators=[
        DataRequired(message="Имя обязательно"),
        Length(max=50, message="Имя не должно превышать 50 символов"),
        Optional()
    ])

    telegram = StringField("Телеграм", validators=[
        DataRequired(message="Телеграм обязателен"),
        Regexp("^@?[A-Za-z0-9_]{5,32}$", message="Неверный формат телеграма")
    ])
    email = StringField("Email", validators=[
        Length(max=100, message="Email не должен превышать 100 символов"),
        Optional()
    ])
    phone = StringField("Телефон", validators=[
        Length(max=20, message="Телефон не должен превышать 20 символов"),
        Optional()
    ])

    bio = TextAreaField("О себе", validators=[
        Length(max=500, message="Описание не должно превышать 500 символов"),
        Optional()
    ])

    document = FileField("Документ", validators=[
        FileAllowed(["pdf", "docx", "txt"], "Разрешены только PDF, DOCX и TXT файлы")
    ])

    submit = SubmitField("Сохранить изменения")


class AvatarForm(FlaskForm):
    avatar = FileField("Аватар", validators=[
        FileAllowed(["jpg", "jpeg", "png"], "Разрешены только изображения JPG и PNG")
    ])

    submit = SubmitField("Обновить аватар")


@application.route("/profile", methods=["GET", "POST"])
def profile_route():
    if "user_id" not in session:
        flash("Пожалуйста, войдите в систему", "error")
        return redirect(url_for("login_route"))

    user = db.session.execute(db.select(User).where(User.id == session["user_id"])).scalar_one()

    avatar_form = AvatarForm()
    form = ProfileForm()

    if avatar_form.validate_on_submit():
        avatar = avatar_form.avatar.data
        if avatar and avatar.filename.split(".")[-1] in {"jpg", "jpeg", "png"}:
            avatar_filepath = secure_filename(
                f"avatar_{session['user_id']}.{avatar.filename.rsplit('.', 1)[1].lower()}")

            avatar.save(os.path.join(application.config["UPLOAD_FOLDER"], "avatars", avatar_filepath))

            user = db.session.execute(db.select(User).where(User.id == session["user_id"])).scalar_one()
            user.avatar_filepath = avatar_filepath
            db.session.commit()

            flash("Аватар успешно обновлен!", "success")
            return redirect(url_for("profile_route"))
    if form.validate_on_submit():
        document = form.document.data
        document_filepath = None
        if document and document.filename.split(".")[-1] in {"txt", "pdf", "docx"}:
            document_filepath = secure_filename(f"document_{user.id}_{document.filename}")
            document.save(
                os.path.join(application.config["UPLOAD_FOLDER"], ["vacancies", "cvs"][user.role_id - 1], document_filepath)
            )

        user.last_name = form.last_name.data
        user.first_name = form.first_name.data
        user.telegram = form.telegram.data
        user.email = form.email.data
        user.phone = form.phone.data
        user.bio = form.bio.data
        user.document_filepath = document_filepath
        db.session.commit()

        flash("Профиль успешно обновлен!", "success")
        return redirect(url_for("profile_route"))

    return render_template("profile.html", user=user, form=form, avatar_form=avatar_form)
