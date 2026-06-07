from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class AdminUserTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password='adminpass', role='admin', is_staff=True)
        self.user = User.objects.create_user(username='bob', email='bob@example.com', password='bobpass')

    def test_admin_can_list_users(self):
        self.client.login(username='admin', password='adminpass')
        url = reverse('accounts:admin_user_list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_non_admin_cannot_list_users(self):
        self.client.login(username='bob', password='bobpass')
        url = reverse('accounts:admin_user_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED))
