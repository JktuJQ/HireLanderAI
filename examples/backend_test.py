from backend.application import run
from backend.index_page import index_route
from backend.interview_page import interview_route
from backend.checkpoint_page import checkpoint_route

run(port=5000, host="127.0.0.1")
