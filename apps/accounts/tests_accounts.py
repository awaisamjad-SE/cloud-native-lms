from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from .models import UserProfile

User = get_user_model()


class AccountsTests(APITestCase):
    def test_register(self):
        url = reverse('accounts:register')
        data = {
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'strongpassword123'
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', resp.data)

    def test_login_returns_tokens_and_user_profile(self):
        user = User.objects.create_user(
            username='student1',
            email='student1@example.com',
            password='studentpass123',
            role='student',
            first_name='Student',
            last_name='One',
        )
        UserProfile.objects.create(user=user, phone_number='+12345678', bio='Bio text', profile_image='profiles/1/a.png')

        url = reverse('accounts:token_obtain_pair')
        resp = self.client.post(url, {'username': 'student1', 'password': 'studentpass123'}, format='json')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', resp.data)
        self.assertIn('access', resp.data)
        self.assertIn('user', resp.data)
        self.assertEqual(resp.data['user']['role'], 'student')
        self.assertEqual(resp.data['user']['phone_number'], '+12345678')
