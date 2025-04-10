from locust import HttpUser, SequentialTaskSet, task, between
import random
import string

class UserBehavior(SequentialTaskSet):
    def on_start(self):
        self.username = f"user_{random.randint(1, 10000)}"
        self.password = "testpassword123"
        self.email = f"{self.username}@example.com"
        self.session_token = None

    @task
    def test_register(self):
        response = self.client.post("/register", data={
            "username": self.username,
            "password": self.password,
            "email": self.email
        }, name="register")
        if response.status_code == 302:
            self.login()

    @task
    def test_login(self):
        response = self.client.post("/login", data={
            "username": self.username,
            "password": self.password
        }, name="login")
        if response.status_code == 302:
            self.session_token = response.cookies.get("session_token")

    @task
    def test_logout(self):
        if self.session_token:
            self.client.get("/logout", cookies={"session_token": self.session_token}, name="logout")
            self.session_token = None

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 5)
    host = "https://docs.stariybog.ru"
