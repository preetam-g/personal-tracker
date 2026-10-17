from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class ProfileUPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('upi_user', password='test-password-123')
        cls.other = get_user_model().objects.create_user('other_user', password='test-password-123')

    def test_user_can_save_and_remove_only_their_own_upi_id(self):
        self.client.force_login(self.user)
        url = reverse('accounts:profile')
        self.assertEqual(self.client.post(url, {
            'form_type': 'upi', 'upi_id': '  My.Name@okaxis  ',
        }).status_code, 302)
        self.user.refresh_from_db()
        self.other.refresh_from_db()
        self.assertEqual(self.user.upi_id, 'my.name@okaxis')
        self.assertEqual(self.other.upi_id, '')
        self.assertContains(self.client.get(url), 'my.name@okaxis')

        self.client.post(url, {'form_type': 'upi', 'upi_id': 'bad upi id'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.upi_id, 'my.name@okaxis')

        self.assertEqual(self.client.post(url, {'form_type': 'upi', 'upi_id': ''}).status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.upi_id, '')
