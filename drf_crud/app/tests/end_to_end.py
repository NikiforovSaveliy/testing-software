import json

from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.test import Client
from django.test import TestCase

from app.models import Category, Beverage


class APITestCase(TestCase):
    def setUp(self):
        """
        Инициализация данных для тестов.
        """
        self.client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username="testuser", password="password123")

        # Создаем тестовые данные
        self.group = Group.objects.create(name="Test Group")
        self.category = Category.objects.create(name="Test Category")
        self.beverage = Beverage.objects.create(name="Test Beverage", category=self.category)

    def authenticate(self):
        """
        Получение JWT Access Token для авторизации.
        """
        response = self.client.post(
            "/auth/jwt/create/",
            {"username": "testuser", "password": "password123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        access_token = response.json().get("access")
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"

    def test_user_list(self):
        """
        Тест: получить список пользователей.
        """
        self.authenticate()
        response = self.client.get("/users/")
        self.assertEqual(response.status_code, 200)
        users = json.loads(response.content)
        self.assertGreater(len(users), 0)
        self.assertEqual(users[0]["username"], "testuser")

    def test_category_crud(self):
        """
        Тесты CRUD для модели Category.
        """
        self.authenticate()

        # Create
        response = self.client.post("/categories/", {"name": "New Category"}, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Category.objects.count(), 2)

        # Read
        response = self.client.get(f"/categories/{self.category.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Category", json.loads(response.content)['name'])

        # Update
        response = self.client.patch(
            f"/categories/{self.category.id}/",
            {"name": "Updated Category"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Updated Category")

        # Delete
        response = self.client.delete(f"/categories/{self.category.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Category.objects.count(), 1)

    def test_beverage_crud(self):
        """
        Тесты CRUD для модели Beverage.
        """
        self.authenticate()

        # Create
        response = self.client.post(
            "/beverages/",
            {"name": "New Beverage", "category": self.category.id},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Beverage.objects.count(), 2)

        # Read
        response = self.client.get(f"/beverages/{self.beverage.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Beverage", json.loads(response.content)['name'])

        # Update
        response = self.client.patch(
            f"/beverages/{self.beverage.id}/",
            {"name": "Updated Beverage"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.beverage.refresh_from_db()
        self.assertEqual(self.beverage.name, "Updated Beverage")

        # Delete
        response = self.client.delete(f"/beverages/{self.beverage.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Beverage.objects.count(), 1)


class UserScenarioTestCase(TestCase):
    def setUp(self):
        """
        Инициализация данных для тестов.
        """
        self.client = Client()
        self.category1 = Category.objects.create(name="Category 1")
        self.category2 = Category.objects.create(name="Category 2")

    def register_and_get_token(self, username, password):
        """
        Регистрирует пользователя и возвращает JWT токен.
        """
        # Регистрация пользователя
        response = self.client.post(
            "/auth/users/",
            {"username": username, "password": password},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

        # Получение токена
        response = self.client.post(
            "/auth/jwt/create/",
            {"username": username, "password": password},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        access_token = response.json().get("access")
        self.assertIsNotNone(access_token)

        # Устанавливаем токен в заголовок
        self.client.defaults["Authorization"] = f"Bearer {access_token}"
        return access_token

    def test_user_scenario(self):
        """
        Сценарий: регистрация, получение токена, создание напитков, изменение категории.
        """
        username = "newuser"
        password = "securepassword"

        # Регистрация и авторизация
        access_token = self.register_and_get_token(username, password)

        # Создание напитков
        response1 = self.client.post(
            "/beverages/",
            {"name": "Beverage 1", "category": self.category1.id},
            headers={"Authorization": f"Bearer {access_token}"},
            content_type="application/json",
        )
        self.assertEqual(response1.status_code, 201)
        beverage1_id = response1.json().get("id")

        response2 = self.client.post(
            "/beverages/",
            {"name": "Beverage 2", "category": self.category1.id},
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, 201)
        beverage2_id = response2.json().get("id")

        self.assertEqual(Beverage.objects.count(), 2)

        # Проверка созданных напитков
        beverage1 = Beverage.objects.get(id=beverage1_id)
        beverage2 = Beverage.objects.get(id=beverage2_id)
        self.assertEqual(beverage1.name, "Beverage 1")
        self.assertEqual(beverage1.category, self.category1)
        self.assertEqual(beverage2.name, "Beverage 2")
        self.assertEqual(beverage2.category, self.category1)

        # Изменение категории у напитка
        response = self.client.patch(
            f"/beverages/{beverage1_id}/",
            {"category": self.category2.id},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # Проверка изменений
        beverage1.refresh_from_db()
        self.assertEqual(beverage1.category, self.category2)
        self.assertEqual(beverage2.category, self.category1)  # Второй напиток остается в старой категории
