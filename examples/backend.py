from backend.application import run

from backend.index import index_route

from backend.login import login_route
from backend.registration import registration_route
from backend.profile import profile_route

from backend.create_interview import create_interview_route
from backend.join_interview import join_interview_route
from backend.interview import interview_route

from backend.evaluation import evaluation_route
from backend.dashboard import dashboard_route

run()
