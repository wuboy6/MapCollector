import threading
import queue
import uuid
import time

class ThreadPool:

    def __init__(self, num_threads):

        self.task_queue = queue.Queue()
        self.results = {}  # 存储任务ID对应的状态和结果
        self.lock = threading.Lock()
        self.workers = []
        self.running = True

        # 初始化工作线程
        for _ in range(num_threads):
            worker = Worker(self)
            worker.start()
            self.workers.append(worker)


    def _submit(self, func, *args, **kwargs):
        """提交任务到线程池，返回任务ID"""
        task_id = uuid.uuid4().hex
        with self.lock:
            self.results[task_id] = {
                'status': 'pending',  # 任务状态：pending, completed, failed
                'result': None,
                'exception': None,
                'condition': threading.Condition(self.lock)
            }
        self.task_queue.put((task_id, func, args, kwargs))
        return task_id

    def _get_result(self, task_id, timeout=None):
        """获取任务结果，支持超时和阻塞等待"""
        with self.lock:
            if task_id not in self.results:
                raise ValueError("Task ID does not exist")

            task_info = self.results[task_id]
            cond = task_info['condition']

            # 等待任务完成或超时
            while task_info['status'] == 'pending':
                if not cond.wait(timeout=timeout):
                    raise TimeoutError("Timeout while waiting for result")

            # 获取结果后自动清理任务信息
            result = task_info['result']
            exception = task_info['exception']
            del self.results[task_id]

        if task_info['status'] == 'completed':
            return result
        else:
            raise exception

    def _shutdown(self, wait=True):
        """关闭线程池，可选是否等待队列任务完成"""
        self.running = False
        if wait:
            self.task_queue.join()  # 等待所有任务处理完毕

        # 发送停止信号给所有工作线程
        for _ in self.workers:
            self.task_queue.put(None)
        for worker in self.workers:
            worker.join()

class Worker(threading.Thread):
    def __init__(self, pool):
        super().__init__()
        self.pool = pool
        self.daemon = True  # 主线程退出时自动终止

    def run(self):
        while self.pool.running or not self.pool.task_queue.empty():
            try:
                # 获取任务，支持超时避免永久阻塞
                task = self.pool.task_queue.get(block=True, timeout=0.1)
            except queue.Empty:
                continue

            if task is None:  # 收到终止信号
                self.pool.task_queue.task_done()
                break

            task_id, func, args, kwargs = task
            try:
                result = func(*args, **kwargs)
                with self.pool.lock:
                    task_info = self.pool.results[task_id]
                    task_info['status'] = 'completed'
                    task_info['result'] = result
                    task_info['condition'].notify_all()
            except Exception as e:
                with self.pool.lock:
                    task_info = self.pool.results[task_id]
                    task_info['status'] = 'failed'
                    task_info['exception'] = e
                    task_info['condition'].notify_all()
            finally:
                self.pool.task_queue.task_done()


if __name__ == "__main__":
    # 示例函数
    def calculate_square(x):
        time.sleep(x)  # 模拟耗时操作
        return x * x


    def raise_error():
        raise ValueError("Intentional error")


    # 使用线程池
    if __name__ == "__main__":
        # 创建包含2个工作线程的线程池
        pool = ThreadPool(2)

        # 提交任务
        task1 = pool.submit(calculate_square, 1)
        task2 = pool.submit(calculate_square, 5)
        task3 = pool.submit(raise_error)

        try:
            # 获取正常任务结果
            print("Task1 result:", pool.get_result(task1))  # 100
            print(pool.results)
            print("Task2 result:", pool.get_result(task2,2))  # 25
            print(pool.results)




            # 获取会抛出异常的任务结果
            pool.get_result(task3)
        except Exception as e:
            print("Task3 error:", repr(e))  # ValueError: Intentional error

            time.sleep(4)
            print("Task2 result:", pool.get_result(task2, 2))  # 25

        # 关闭线程池（会自动等待剩余任务完成）

