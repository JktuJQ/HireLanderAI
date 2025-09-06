from ai.interviewer import Interviewer
from RealtimeSTT import AudioToTextRecorder



print("Wait until it says 'speak now'")
recorder = AudioToTextRecorder(language="ru", silero_use_onnx = True, silero_sensitivity = 1)    

while True:
    recorder.text(Interviewer.process_text)