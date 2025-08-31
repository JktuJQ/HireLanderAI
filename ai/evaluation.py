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
            model="openai/gpt-4o-mini",
            api_key=SECRETS["OPENAI_API_KEY"],
            # fetch free key for 5 dollars https://benjamincrozat.com/gpt-4o-mini#introduction-to-gpt-4o-mini
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
        document.add_concepts([
            contextgem.StringConcept(
                name="Job name",
                description="Name of the vacancy's job",
                reference_depth="sentences"
            )
        ])
        document.add_aspect([
            contextgem.Aspect(
                name="Job requirements",
                description="Sections or sentences describing job requirements (what is expected from job applicant)",
                reference_depth="sentences",
                add_justifications=True,
                justification_depth="balanced",
                # TODO: test this stuff
                concepts=[
                    contextgem.StringConcept(
                        name="Education",
                        description="Presence or absence of a specialized education, any information about it: whether it has to be higher or not, description, specialization",
                    ),
                    contextgem.StringConcept(
                        name="Stack",
                        description="A full list of programs, programming languages or any other technologies that are required for a job",
                    ),
                    contextgem.StringConcept(
                        name="Skills",
                        description="Something that can't be connected to a stack aspect. Necessary skills or abilities to make a job done",
                    ),
                    contextgem.StringConcept(
                        name="Experience",
                        description="Anything related to needed job experience: years, required knowledge and skills",
                    ),
                    contextgem.StringConcept(
                        name="Tasks",
                        description="What tasks an employee will need to do to successfully do their job",
                    ),
                    contextgem.StringConcept(
                        name="Advantages",
                        description="Anything that can increase the odds of an employee, but not necessarily required",
                    ),
                ]
            )
        ])

        processed_document = evaluator.extractor_model.extract_all(document)
        evaluator.job_requirements.append(processed_document.concepts[0].extracted_items[0].value)
        for job_requirement in processed_document.aspects[0].extracted_items:
            job_requirement_text = [
                f"{job_requirement.value}",
                f"Причины: {job_requirement.justification}",
                "\n",
                "Ссылки:"
            ]
            for sentence in job_requirement.reference_sentences:
                job_requirement_text.append(f"* {sentence.raw_text}")
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

        full_document = [None, None]
        if cv_file is not None:
            full_document[0] = "Резюме:\n" + Evaluator.__file_to_document(cv_file).raw_text
        if conversation is not None:
            full_document[1] = "Записанное интервью\n" + conversation
        full_document = contextgem.Document(raw_text="\n\n".join(full_document))

        job_requirements_text = []
        for i, job_requirement in enumerate(self.job_requirements):
            job_requirements_text.append(f"Requirement №{i + 1}:" + job_requirement)
        job_requirements_text = "\n".join(job_requirements_text)

        full_document.add_concept([
            contextgem.RatingConcept(
                name="Job applicant rating",
                description=(
                    "Evaluate job applicant using his CV and interview.\n"
                    f"You need to find scores and justifications for each job requirement, listed below:\n"
                    f"{job_requirements_text}"
                ),
                rating_scale=(1, 100),
                add_justifications=True,
                justification_depth="balanced",
                justification_max_sents=5,
            )
        ])

        evaluation = {}
        grades = self.extractor_model.extract_concepts_from_document(full_document)[0]
        for job_requirement, grade in zip(self.job_requirements, grades.extracted_items):
            evaluation[job_requirement] = (grade.value, grade.justification)
        return evaluation

if __name__ == '__main__':
    pass
