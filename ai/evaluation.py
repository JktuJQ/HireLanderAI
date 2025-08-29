class Evaluator:
    """
    Model that can evaluate person's compliance with the vacancy based on their CV or their conversation.

    Evaluator processes document/conversation and gathers context information that is relevant
    for requirements that are imposed for the vacancy.
    It then grades person based on their compliance with the requirements.
    """

    def __init__(self, job_requirements: list[str], pretrained: bool = True):
        self.job_requirements = job_requirements

        self.model = None  # https://github.com/shcherbak-ai/contextgem seems interesting for preprocessing

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