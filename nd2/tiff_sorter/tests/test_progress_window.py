from gui.progress_window import ProgressWindow
import time
import threading
import queue

progress_order = ['Read', 'Write', 'Pivlab calls']

progress_data = { 'Read': {'maximum': 10, 'units': 'frames'},
                 'Write': {'maximum': 10, 'units': 'frames'},
                  'Pivlab calls': {'maximum': 5, 'units': 'frame pairs'}
                 }

result_queue = queue.Queue()


def background_work():
    time.sleep(3)
    for i in range(10):
        result_queue.put('Read')
        time.sleep(1)
        result_queue.put('Write')
        time.sleep(1)
        if i % 2 == 1:
            result_queue.put('Pivlab calls')
            time.sleep(1)
    result_queue.put('Quit')


progress_window = ProgressWindow(progress_data, progress_order, result_queue)
threading.Thread(target=background_work, daemon=True).start()
progress_window.start()

