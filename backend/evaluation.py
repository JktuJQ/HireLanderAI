from backend.application import application

from backend.application import db, User

import os
import time

from flask import redirect, url_for, render_template, session, flash, request

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import SubmitField
from werkzeug.utils import secure_filename

from ai.evaluation import Evaluator


class VacancyForm(FlaskForm):
    vacancy_file = FileField("Файл вакансии", validators=[
        FileAllowed(["pdf", "docx", "txt"], "Разрешены только PDF, DOCX и TXT файлы")
    ])
    submit = SubmitField("Обработать вакансию")


class ResumeForm(FlaskForm):
    resume_file = FileField("Файл резюме", validators=[
        FileAllowed(["pdf", "docx", "txt"], "Разрешены только PDF, DOCX и TXT файлы")
    ])
    submit = SubmitField("Оценить резюме")


@application.route("/evaluation", methods=["GET", "POST"])
async def evaluation_route():
    vacancy_form = VacancyForm()
    resume_form = ResumeForm()

    if "user_id" in session:
        user = db.session.execute(
            db.select(User).where(User.id == session["user_id"])
        ).scalar_one()

        user_vacancy = user.document_filepath if session["role_id"] == 1 else None
        user_resume = user.document_filepath if session["role_id"] == 2 else None
    else:
        user_vacancy = None
        user_resume = None

    vacancy_requirements = session.get("vacancy_requirements", [])
    evaluation_results = session.get("evaluation_results", {})
    average_score = session.get("average_score", "")
    summary_text = session.get("summary_text", "")

    if request.method == "POST":
        action = request.form.get("action")

        if action == "process_vacancy":
            vacancy_source = request.form.get("vacancy_source", "new")

            if vacancy_source == "existing" and "user_id" in session and user_vacancy is not None:
                vacancy_path = os.path.join(
                    application.config["UPLOAD_FOLDER"],
                    "vacancies",
                    user_vacancy
                )
            else:
                if vacancy_form.vacancy_file.data:
                    file = vacancy_form.vacancy_file.data
                    filename = secure_filename(
                        f"vacancy_{int(time.time())}.{file.filename.rsplit('.', 1)[1].lower()}")
                    vacancy_path = os.path.join(application.config["UPLOAD_FOLDER"], "vacancies", filename)
                    os.makedirs(os.path.dirname(vacancy_path), exist_ok=True)
                    file.save(vacancy_path)
                else:
                    flash("Пожалуйста, выберите файл вакансии", "error")
                    return redirect(url_for("evaluation_route"))

            try:
                evaluator = Evaluator.from_vacancy_file(vacancy_path)
                vacancy_requirements = evaluator.job_requirements
                for i in range(len(vacancy_requirements)):
                    vacancy_requirements[i] = vacancy_requirements[i].split("Причины:")[0].split("Ссылки:")[0]
                session["vacancy_requirements"] = evaluator.job_requirements
                vacancy_requirements = evaluator.job_requirements

                flash("Вакансия успешно обработана!", "success")
            except Exception as e:
                print(str(e))
                flash(f"Ошибка при обработке вакансии: {str(e)}", "error")
                return redirect(url_for("evaluation_route"))

        elif action == "process_resume" and "vacancy_requirements" in session:
            resume_source = request.form.get("resume_source", "new")

            if resume_source == "existing" and "user_id" in session and user_resume:
                resume_path = os.path.join(
                    application.config["UPLOAD_FOLDER"],
                    "cvs",
                    user_resume
                )
            else:
                if resume_form.resume_file.data:
                    file = resume_form.resume_file.data
                    filename = secure_filename(
                        f"resume_{int(time.time())}.{file.filename.rsplit('.', 1)[1].lower()}")
                    resume_path = os.path.join(application.config["UPLOAD_FOLDER"], "cvs", filename)
                    os.makedirs(os.path.dirname(resume_path), exist_ok=True)
                    file.save(resume_path)
                else:
                    flash("Пожалуйста, выберите файл резюме", "error")
                    return redirect(url_for("evaluation_route"))

            try:
                evaluator = Evaluator(vacancy_requirements)
                results = {key: value for i, (key, value) in enumerate(evaluator.grade(cv_file=resume_path).items()) if i < 7}

                scores = [score for score, _ in results.values()]
                average_score = round(sum(scores) / len(scores) if scores else 0, 2)

                if average_score >= 90:
                    summary_text = "Отличное соответствие! Кандидат полностью подходит для вакансии."
                elif average_score >= 70:
                    summary_text = "Хорошее соответствие. Кандидат подходит для большинства требований."
                elif average_score >= 50:
                    summary_text = "Среднее соответствие. Кандидат требует дополнительного обучения."
                elif average_score >= 30:
                    summary_text = "Слабое соответствие. Рассмотрите других кандидатов."
                else:
                    summary_text = "Не соответствует требованиям. Не рекомендуется к найму."

                session["evaluation_results"] = results
                session["average_score"] = average_score
                session["summary_text"] = summary_text

                flash("Резюме успешно оценено!", "success")
                return redirect(url_for("evaluation_route"))
            except Exception as e:
                flash(f"Ошибка при оценке резюме: {str(e)}", "error")
                return redirect(url_for("evaluation_route"))

    return render_template(
        "evaluation.html",
        enumerate=enumerate,
        vacancy_form=vacancy_form,
        resume_form=resume_form,
        user_vacancy=user_vacancy,
        user_resume=user_resume,
        vacancy_requirements=vacancy_requirements,
        evaluation_results=evaluation_results,
        average_score=average_score,
        summary_text=summary_text
    )


@application.route("/evaluation/clear")
def clear_evaluation_route():
    session["vacancy_requirements"] = None
    session["evaluation_results"] = None
    session["average_score"] = None
    session["summary_text"] = None
    return redirect(url_for("evaluation_route"))
