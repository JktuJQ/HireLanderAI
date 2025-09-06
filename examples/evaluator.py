from ai.evaluation import Evaluator

vacancy_file_name = "examples/VacancyExample1.docx"
cv_file_name = "examples/Example2.docx"

evaluator = Evaluator.from_vacancy_file(vacancy_file_name)
evaluation_results = evaluator.grade(cv_file=cv_file_name)
for requirement, (score, justification) in evaluation_results.items():
    print(f"Причина: {requirement.splitlines()[0]}")
    print(f"Оценка: {score}")
    print(f"Обоснование: {justification}")
