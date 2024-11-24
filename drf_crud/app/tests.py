from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from app.models import Category, Beverage


class CategoryAPITestCase(APITestCase):
    def setUp(self):
        # Создаем пользователя и авторизуемся
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        self.category_data = {'name': 'Hot Beverages'}

    def test_create_category(self):
        response = self.client.post('/categories/', self.category_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Category.objects.first().name, 'Hot Beverages')

    def test_list_categories(self):
        Category.objects.create(name='Cold Beverages')
        response = self.client.get('/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_update_category(self):
        category = Category.objects.create(name='Soft Drinks')
        response = self.client.patch(f'/categories/{category.id}/', {'name': 'Juices'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        category.refresh_from_db()
        self.assertEqual(category.name, 'Juices')

    def test_delete_category(self):
        category = Category.objects.create(name='Soft Drinks')
        response = self.client.delete(f'/categories/{category.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)


class BeverageAPITestCase(APITestCase):
    def setUp(self):
        # Создаем пользователя и авторизуемся
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        self.category = Category.objects.create(name='Hot Beverages')
        self.beverage_data = {
            'name': 'Tea',
            'category': self.category.id,
            'price': 100,
            'is_available': True
        }

    def test_create_beverage(self):
        response = self.client.post('/beverages/', self.beverage_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Beverage.objects.count(), 1)
        self.assertEqual(Beverage.objects.first().name, 'Tea')

    def test_list_beverages(self):
        Beverage.objects.create(
            name='Coffee',
            category=self.category,
            price=150,
            is_available=True
        )
        response = self.client.get('/beverages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_update_beverage(self):
        beverage = Beverage.objects.create(
            name='Hot Chocolate',
            category=self.category,
            price=200,
            is_available=True
        )
        response = self.client.patch(f'/beverages/{beverage.id}/', {'price': 250})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        beverage.refresh_from_db()
        self.assertEqual(beverage.price, 250)

    def test_delete_beverage(self):
        beverage = Beverage.objects.create(
            name='Latte',
            category=self.category,
            price=300,
            is_available=True
        )
        response = self.client.delete(f'/beverages/{beverage.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Beverage.objects.count(), 0)
