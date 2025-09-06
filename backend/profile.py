from backend.application import application

from backend.application import db, User

import os

from flask import redirect, url_for, render_template, session, flash, request

from werkzeug.utils import secure_filename

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Regexp


class AvatarForm(FlaskForm):
    avatar = FileField("Аватар", validators=[
        FileAllowed(["jpg", "jpeg", "png"], "Разрешены только изображения JPG и PNG")
    ])
    submit = SubmitField("Обновить аватар")


class InterviewerProfileForm(FlaskForm):
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

    document = FileField("Вакансия", validators=[
        FileAllowed(["pdf", "docx", "txt"], "Разрешены только PDF, DOCX и TXT файлы")
    ])

    submit = SubmitField("Сохранить изменения")


@application.route("/profile", methods=["GET", "POST"])
@application.route("/profile/<int:user_id>", methods=["GET"])
async def profile_route(user_id=None):
    if user_id is None:
        if "user_id" not in session:
            flash("Пожалуйста, войдите в систему", "error")
            return redirect(url_for("login_route"))
        user_id = session["user_id"]
        is_own_profile = True
    else:
        is_own_profile = session.get("user_id") == user_id

    user = db.session.execute(db.select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        flash("Пользователь не найден", "error")
        return redirect(url_for("index_route"))

    if is_own_profile and request.method == "POST":
        return handle_profile_update(user)

    avatar_form = AvatarForm() if is_own_profile else None
    form = InterviewerProfileForm() if is_own_profile else None

    return render_template("profile.html",
                           user=user,
                           form=form,
                           avatar_form=avatar_form,
                           is_own_profile=is_own_profile,
                           profile_url=request.host_url + f"profile/{user_id}")


def handle_profile_update(user):
    avatar_form = AvatarForm()
    form = InterviewerProfileForm()

    avatar = avatar_form.avatar.data
    if avatar_form.validate_on_submit() and avatar and avatar.filename.split(".")[-1].lower() in {"jpg", "jpeg", "png"}:
        avatar_filepath = secure_filename(
            f"avatar_{user.id}.{avatar.filename.rsplit('.', 1)[1].lower()}")

        avatar_path = os.path.join(application.config["UPLOAD_FOLDER"], "avatars", avatar_filepath)
        os.makedirs(os.path.dirname(avatar_path), exist_ok=True)
        avatar.save(avatar_path)

        user.avatar_filepath = avatar_filepath
        db.session.commit()
        flash("Аватар успешно обновлен!", "success")

    if form.validate_on_submit():
        document = form.document.data
        document_filepath = None

        if document and document.filename.split(".")[-1].lower() in {"txt", "pdf", "docx"}:
            folder = "vacancies" if user.role_id == 1 else "cvs"
            document_filepath = secure_filename(f"document_{user.id}_{document.filename}")
            document_path = os.path.join(application.config["UPLOAD_FOLDER"], folder, document_filepath)
            os.makedirs(os.path.dirname(document_path), exist_ok=True)
            document.save(document_path)

        user.last_name = form.last_name.data
        user.first_name = form.first_name.data
        user.telegram = form.telegram.data
        user.email = form.email.data
        user.phone = form.phone.data
        user.bio = form.bio.data

        if document_filepath:
            user.document_filepath = document_filepath

        db.session.commit()
        flash("Профиль успешно обновлен!", "success")

    return redirect(url_for("profile_route"))
