# noinspection PyUnresolvedReferences

def main():
    """ Program's entry point."""
    #from backend.application import run

    #from backend.index_page import index_route
    #from backend.interview_page import interview_route

    from ai.evaluation import Evaluator


    vacancy_file_name = "test\VacancyExample1.docx"
    cv_file_name = "test\Example1.docx"


    evaluator = Evaluator.from_vacancy_file(vacancy_file_name)
    evaluation_results = evaluator.grade(cv_file=cv_file_name)
    for requirement, (score, justification) in evaluation_results.items():
        print(f"Причина: {requirement.splitlines()[0]}")
        print(f"Оценка: {score}")
        print(f"Обоснование: {justification}")

    #run()


if __name__ == '__main__':
    main()


#if __name__ == "__main__":
    #main()
