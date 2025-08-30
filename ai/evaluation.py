import fitz
import pdfplumber
import pandas as pd

class Evaluator:
    """
    Model that can evaluate person's compliance with the vacancy based on their CV or their conversation.

    Evaluator processes document/conversation and gathers context information that is relevant
    for requirements that are imposed for the vacancy.
    It then grades person based on their compliance with the requirements.
    """

    def __init__(self, job_requirements: list[str]=None, pdf_path=None, pretrained: bool = True):
        self.job_requirements = job_requirements
        self.pdf_path = pdf_path
        self.model = None  # https://github.com/shcherbak-ai/contextgem seems interesting for preprocessing

    def extract_text_from_pdf(self):
        """First of the three functions that get the text from the resume.
        Extracts all the text via PyMuPDF library"""
        doc = fitz.open(self.pdf_path)
        full_text = ""

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # Получаем размеры страницы
            width = page.rect.width

            # Определяем среднюю точку для разделения колонок
            mid_x = width / 2

            # Извлекаем текстовые блоки
            blocks = page.get_text("dict")["blocks"]
            left_column = []
            right_column = []

            for block in blocks:
                if "lines" in block:  # Текстовый блок
                    x0 = block["bbox"][0]
                    text = ""
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text += span["text"] + " "

                    # Распределяем по колонкам
                    if x0 < mid_x:
                        left_column.append(
                            (block["bbox"][1], text))  # (y-coord, text)
                    else:
                        right_column.append((block["bbox"][1], text))

            # Сортируем блоки по вертикали
            left_column.sort(key=lambda x: x[0])
            right_column.sort(key=lambda x: x[0])

            # Формируем текст для страницы
            page_text = ""
            for y, text in left_column:
                page_text += text + "\n"
            for y, text in right_column:
                page_text += text + "\n"

            full_text += f"--- Страница {page_num + 1} ---\n{page_text}\n"

        doc.close()
        return full_text

    def extract_tables_from_pdf(self):
        """Second of the three functions that get the text from the resume.
        Extracts all the tables"""
        tables_text = ""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if tables:
                    tables_text += f"\n--- Таблицы на странице {page_num + 1} ---\n"
                    for i, table in enumerate(tables):
                        df = pd.DataFrame(table)
                        tables_text += f"Таблица {i + 1}:\n"
                        tables_text += df.to_string(index=False,
                                                    header=False) + "\n\n"
        return tables_text

    def process_pdf(self):
        """Main function, writes text from pdf resume to a extracted_text.txt file
        usage: Evaluator.process_pdf()"""
        try:
            text = self.extract_text_from_pdf()
            tables = self.extract_tables_from_pdf()

            with open("extracted_text.txt", "w", encoding="utf-8") as f:
                f.write(text)
                f.write(tables)

            print("Текст и таблицы сохранены в extracted_text.txt")
        except:
            raise 'Не удалось обработать файл'

    def grade(self, conversation: str = None, cv_file: str = None) -> dict[str, int]:
        """
        Grades person based on job requirements.

        This function operates on text which is embedded with context information
        (obtained from CV and conversation) that is needed to grade a person.
        Because of that, this function could grade only the conversation or only the CV of a person,
        or both simultaneously.

        :param conversation: Conversation between interviewer/interviewee
        :param cv_file: Filename of the CV file

        :returns: Dictionary with grades for compliance with each requirement
        """

        return {requirement: 0 for requirement in self.job_requirements}

class JobPosition:
    """
    Model that can evaluate job position and requirenments from a PDF-file
    that has a description of a position
    """

    def __init__(self, position: str = None, requirements: list[str] = None, pdf_path: str = None):
        self.position = position
        self.requirements = requirements
        self.pdf_path = pdf_path

    def extract_position(self) -> str:
        """
        Gets a field value from a PDF-file
        """
        try:
            if self.position is not None:
                return self.position

            with pdfplumber.open(self.pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"

            # Разобьём по строкам и ищем нужное поле
            for line in text.splitlines():
                if line.startswith("Название"):
                    # убираем само название поля
                    return line.replace("Название", "").strip()

            return "Не получилось найти название вакансии"
        except:
            raise "Не удалось обработать файл"

    def extract_requirements(self) -> list[str]:
        """
        Gets job requirements from a PDF-file
        """
        doc = fitz.open(self.pdf_path)
        requirements_text = ""
        capture = False

        for page in doc:
            text = page.get_text("text")
            lines = text.splitlines()

            for line in lines:
                if "Требования (для" in line:  # начало нужного блока
                    capture = True
                    continue
                if capture:
                    if line.strip().startswith(
                            "Уровень образования"):  # конец блока
                        capture = False
                        break
                    requirements_text += " " + line.strip()

        return requirements_text[13:].split(';')


if __name__ == '__main__':
    ev = Evaluator(job_requirements=[''], pdf_path='резюме.pdf')
    ev.process_pdf()
    jp = JobPosition(pdf_path='Описание бизнес аналитик.pdf')
    print(jp.extract_position())
    print(jp.extract_requirements())
