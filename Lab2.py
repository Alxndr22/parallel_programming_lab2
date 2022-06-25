import threading
import time
from datetime import datetime
from queue import Queue

parts_to_be_assembled = ['hood', 'left fender', 'right fender', 'left door', 'right door', 'driver chair',
                         'passenger chair', 'left headlight', 'right headlight', 'left brake light', 'right brake light']


def detail_assembly(part):
    time.sleep(1)
    print('Worker has assembled the item: ', part)
    return part


class FutureResult:
    def __init__(self):
        self.lock = threading.Lock()
        self.cond = threading.Condition(self.lock)
        self.hasResult = False
        self.result = None
        self.time = None

    def set_result(self, result):
        with self.cond:
            self.result = result
            self.time = datetime.now().strftime("%H:%M:%S")

            self.hasResult = True
            self.cond.notify_all()

    def get_result(self):
        with self.cond:
            while not self.hasResult:
                print("•• WAIT() REACHED ••")
                self.cond.wait()
        return self.result


class CarDetail:     # workItem
    def __init__(self, parameters, function):
        self.parameters = parameters
        self.function = function
        self.future = FutureResult()


class WorkerThread(threading.Thread):
    def __init__(self, queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue
        self.stop_thread = False

    def run(self):
        while True:
            item = self.queue.get()  # item => carDetail
            res = item.function(item.parameters)
            item.future.set_result(res)
            if self.stop_thread:
                if self.queue.empty():
                    break

    def stop(self):
        self.stop_thread = True


class CustomExecutor:
    def __init__(self, max_workers):
        self.queue = Queue(maxsize=4)
        self.list_of_workers = []
        self.max_workers = max_workers
        print("Max available workers: ", max_workers)

    def execute(self, function, args):
        car_inst = CarDetail(args, function)
        self.queue.put(car_inst)
        return car_inst.future

    def map(self, function, args_for_function):
        future_res = []
        for arg in args_for_function:
            future_res.append(self.execute(function, arg))

            if threading.active_count() <= self.max_workers:
                # print(threading.active_count())
                t = WorkerThread(self.queue)
                self.list_of_workers.append(t)
                t.start()

        self.shutdown()
        return future_res

    def shutdown(self):
        while True:
            for workers in self.list_of_workers:
                workers.stop()
            break


e = CustomExecutor(max_workers=3)
futures = e.map(detail_assembly, parts_to_be_assembled)
print("-" * 10)

for f in futures:
    print(f.get_result(), "-", f.time)
