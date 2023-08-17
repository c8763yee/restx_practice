import unittest
from unittest.mock import patch
from random import randint, choices
from time import sleep
from string import ascii_letters
from tasks import AsyncResult, fib_task, pow_
from app import app


def generate_random_string(length=10):
    return "".join(choices(ascii_letters, k=length))


# TODO:
# add this test case since i can't get coverage for tasks.py
class TestCelery(unittest.TestCase):
    def test_status_fib(self):
        with patch("tasks.fib_task.update_state") as mock_func:
            n = randint(3, 60)
            # argument must be an iterable, not int
            task = fib_task.apply(args=(n,))
            task.get()
            self.assertEqual(
                n,
                mock_func.call_count + 1,
                msg=f"n={n} mock_func.call_count={mock_func.call_count}",
            )  # +1 because of for loop start from 2

    def test_status_pow(self):
        with patch("tasks.pow_.update_state") as mock_func:
            x = randint(-40, 40)
            n = randint(5, 40) * (-1 if randint(0, 1) else 1)
            task = pow_.apply(args=(x, n))
            task.get()
            self.assertEqual(
                abs(n),
                mock_func.call_count,
            )


class TestAPI(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def test_post(self):
        """
        test case for /fib (POST) endpoint
        """
        n = randint(10, 60)
        response = self.app.post("/fib", json={"n": n})
        self.assertEqual(response.status_code, 200)

        # assert task id is in response json
        self.assertIn("task_id", response.json.keys())
        task_id = response.json["task_id"]

        # sleep 50% of task time to check if delay function works
        sleep(0.50 * n)

        # get task state
        task_response = self.app.post("/status", json={"task_id": task_id})
        self.assertEqual(task_response.json["state"], "PROGRESS")
        self.assertIsInstance(task_response.json["meta"], dict)

        # wait for task to complete
        sleep(n)

        # check if task is success
        with patch.object(AsyncResult, "state", "SUCCESS"):
            task_response = self.app.post("/status", json={"task_id": task_id})
            self.assertEqual(task_response.json["state"], "SUCCESS")

    def test_post_early_return(self):
        """
        previous test with n<=2 since this case will make /fib early return n>0
        """
        n = randint(-60, 1)
        response = self.app.post("/fib", json={"n": n})
        self.assertEqual(response.status_code, 200)
        task_id = response.json["task_id"]

        sleep(4)

        task_response = self.app.post("/status", json={"task_id": task_id})
        self.assertEqual(task_response.json["state"], "SUCCESS")
        self.assertIn("val", task_response.json)

    def test_task_state(self):
        """
        test case for /pow (GET) endpoint
        """
        x = randint(-40, 40)
        n = randint(5, 40) * (-1 if randint(0, 1) else 1)
        # send request to /pow
        response = self.app.get(f"/pow?x={x}&n={n}")
        self.assertEqual(response.status_code, 200)

        # assert json contains all required keys
        self.assertIn("task_id", response.json.keys())
        task_id = response.json["task_id"]
        n = abs(n)
        # sleep 50% of task time to check if delay function works
        sleep(0.50 * n)

        # get task state
        task_response = self.app.post("/status", json={"task_id": task_id})
        self.assertEqual(task_response.json["state"], "PROGRESS")
        self.assertIsInstance(task_response.json["meta"], dict, msg=task_response.json)

        # wait for task to complete
        sleep(n)
        # check if task success
        with patch.object(AsyncResult, "state", "SUCCESS"):
            task_response = self.app.post("/status", json={"task_id": task_id})
            self.assertEqual(task_response.json["state"], "SUCCESS")

    # exception tests
    def test_task_status_unexcept_behavior(self):
        """
        test case for /status (GET) endpoint but task_id is invalid or not provided
        """
        task_id = generate_random_string()
        with patch.object(AsyncResult, "state", "PENDING"):
            response = self.app.post("/status", json={"task_id": task_id})

            # AsyncResult("invalid task_id")=PENDING
            self.assertEqual(response.json["state"], "PENDING")

            response = self.app.post("/status", json={"task_id": ""})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json["error"], "task_id is required")

    def test_pow_unexcept_behavior(self):
        """
        test_task_state but x and n are not valid
        """
        x = generate_random_string()
        n = generate_random_string()
        response = self.app.get(f"/pow?x={n}&n={n}")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json["error"], "x must be float and n must be integer"
        )

    def test_fib_unexcept_behavior(self):
        """
        test_post but n is not valid
        """
        response = self.app.post(f"/fib", json={"n": generate_random_string()})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"], "n must be integer")


if __name__ == "__main__":
    unittest.main()
