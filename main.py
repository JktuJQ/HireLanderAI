# noinspection PyUnresolvedReferences


def run_eval():
    from ai.evaluation import Evaluator

    vacancy_file_name = "test/VacancyExample1.docx"
    cv_file_name = "test/Example2.docx"

    evaluator = Evaluator.from_vacancy_file(vacancy_file_name)
    evaluation_results = evaluator.grade(cv_file=cv_file_name)
    for requirement, (score, justification) in evaluation_results.items():
        print(f"Причина: {requirement.splitlines()[0]}")
        print(f"Оценка: {score}")
        print(f"Обоснование: {justification}")


def run_web():
    from backend.application import run
    from backend.index_page import index_route
    from backend.interview_page import interview_route

    run(port=5000, host="127.0.0.1")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--module", dest="module", type=str,
                        help="Start different modules for testing purposes")
    args = parser.parse_args()

    match args.module:
        case "web":
            run_web()
        case "eval":
            run_eval()
