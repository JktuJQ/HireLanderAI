from globals import *

import contextgem

import pymupdf


class Evaluator:
    """
    Model that can evaluate person's compliance with the vacancy based on their CV or their conversation.

    Evaluator processes document/conversation and gathers context information that is relevant
    for requirements that are imposed for the vacancy.
    It then grades person based on their compliance with the requirements.
    """

    def __init__(self, job_requirements: list[str]):
        self.job_requirements = job_requirements

        self.extractor_model = contextgem.DocumentLLM(
            model="mistral/codestral-2508",
            api_key=SECRETS["EVALUATOR_MODEL_API_KEY"],
            output_language="adapt",
        )

    @staticmethod
    def __pdf_to_text(pdf_file: str) -> str:
        """
        Extracts all text from PDF file.

        :param pdf_file: Name of PDF file

        :return: Extracted text
        """

        text = []
        with pymupdf.open(pdf_file) as f:
            text.append(f"--- Название файла: {pdf_file[:-4]} ---")
            for num, page in enumerate(f.pages()):
                text.append(f"--- Страница №{num + 1} ---")
                text.append(page.getText())
        return "\n".join(text)

    @staticmethod
    def __file_to_document(filename: str) -> contextgem.Document:
        """
        Converts file into structured document.

        :param filename: Name of the file (only PDF and DOCX are supported)
        :return: Structured document with contents of given file
        """

        extension = filename.split(".")[-1]
        if extension == "pdf":
            document = contextgem.Document(raw_text=Evaluator.__pdf_to_text(filename))
        elif extension == "docx":
            document = contextgem.DocxConverter().convert(filename)
        else:
            raise Exception("Only PDF or DOCX files are allowed")

        return document

    @classmethod
    def from_vacancy_file(cls, filename: str) -> 'Evaluator':
        """
        Extracts job requirements from file.

        :param filename: Name of file (PDF and DOCX are supported)

        :return: List of job requirements (first element of the list will contain vacation name)
        """

        evaluator = cls([])

        document = Evaluator.__file_to_document(filename)
        document.add_aspects([
            contextgem.Aspect(
                name="Название вакансии",
                description=("Извлеките ТОЛЬКО название должности/позиции. Ищите: "
                 "1) Текст после поля 'Название' или 'Позиция', "
                 "2) Заголовки, выделенные жирным шрифтом, указывающие на позицию, "
                 "3) Основное название должности (не название компании). "
                 "Верните только название позиции, больше ничего."),
                reference_depth="sentences",
                add_justifications=False,
            ),

            contextgem.Aspect(
                name="Детальные требования к кандидату",
                description=("Все конкретные требования к кандидату. "
                "Сосредоточьтесь на: уровне образования, технических навыках, опыте работы и обязанностях."),
                reference_depth="sentences",
                add_justifications=True,
                justification_depth="balanced",
                concepts=[
                    contextgem.StringConcept(
                        name="Уровень образования",
                        description=("Требуемое образование: высшее, среднее специальное, среднее профессиональное и т.д.")
                    ),
                    contextgem.StringConcept(
                    name="Технический стек",
                    description=("Конкретные технологии, языки программирования, программное обеспечение и оборудование. "
                                "Включите: серверы, сетевое оборудование, языки программирования, базы данных, ОС.")
                    ),
                    contextgem.StringConcept(
                        name="Ключевые обязанности",
                        description="Главные должностные обязанности и задачи, которые должен выполнять сотрудник."
                    ),
                    contextgem.StringConcept(
                        name="Требуемые навыки",
                        description="Гибкие навыки и общие способности: коммуникация, работа в команде, аналитическое мышление и т.д."
                    )
                ]
            )
        ])

        processed_document = evaluator.extractor_model.extract_all(document, max_items_per_call=1)
        evaluator.job_requirements.append(str(processed_document.aspects[0].extracted_items[0].value))
        for job_requirement in processed_document.aspects[1].extracted_items:
            job_requirement_text = [
                f"{job_requirement.value}",
                f"Причины: {job_requirement.justification}",
                "Ссылки:"
            ]
            for sentence in job_requirement.reference_sentences:
                job_requirement_text.append(f"* {sentence.raw_text} \n")
            evaluator.job_requirements.append("\n".join(job_requirement_text))
        return evaluator

    def grade(self, cv_file: str = None, conversation: str = None) -> dict[str, (int, str)]:
        """
        Grades person based on job requirements.

        This function operates on text which is embedded with context information
        (obtained from CV and conversation) that is needed to grade a person.
        Because of that, this function could grade only the conversation or only the CV of a person,
        or both simultaneously.

        :param cv_file: Filename of the CV file (only PDF and DOCX are supported)
        :param conversation: Conversation between interviewer/interviewee

        :return: Dictionary with grades and justifications for compliance with each requirement
        """

        full_document = ["", ""]
        if cv_file is not None:
            full_document[0] = "Резюме:\n" + Evaluator.__file_to_document(cv_file).raw_text
        if conversation is not None:
            full_document[1] = "Записанное интервью\n" + conversation
        full_document = contextgem.Document(raw_text="\n\n".join(full_document))

        job_requirements_text = []
        for i, job_requirement in enumerate(self.job_requirements):
            job_requirements_text.append(f"Requirement №{i + 1}:" + job_requirement)
        job_requirements_text = "\n".join(job_requirements_text)

        full_document.add_concepts([
            contextgem.RatingConcept(
                name="Overall Vacancy Fit Assessment",
                description=(
                    "Оцените кандидата по каждому критерию отдельно по шкале 1-100.\n"
                    "ВАЖНО: Дайте отдельную оценку для КАЖДОГО из перечисленных критериев.\n\n"
                    "КРИТЕРИИ ДЛЯ ОЦЕНКИ:\n"
                    f"{job_requirements_text}\n"
                    "ПРАВИЛА ОЦЕНКИ:\n"
                    "• 90-100: Полностью соответствует или превышает требования\n"
                    "• 70-89: Хорошо соответствует большинству требований\n"
                    "• 50-69: Частично соответствует, есть потенциал\n"
                    "• 30-49: Слабое соответствие\n"
                    "• 1-29: Не соответствует требованиям\n\n"
                    "Для КАЖДОГО критерия укажите конкретные факты из резюме/интервью и\n"
                    "ВАЖНО: указать в обосновании почему оценка не выше и не ниже установленной"
                ),
                rating_scale=(1, 100),
                add_justifications=True,
                justification_depth="balanced",
                justification_max_sents=3,
            )
        ])

        evaluation = {}
        grades = self.extractor_model.extract_concepts_from_document(full_document)[0]
        for job_requirement, grade in zip(self.job_requirements, grades.extracted_items):
            evaluation[job_requirement] = (grade.value, grade.justification)
        return evaluation
