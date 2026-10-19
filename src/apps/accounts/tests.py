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

    def test_profile_has_only_direct_payment_details(self):
        self.client.force_login(self.user)
        page = self.client.get(reverse('accounts:profile'))
        self.assertContains(page, 'Your UPI ID')
        self.assertNotContains(page, 'ToroPay')
        self.assertNotContains(page, 'toropay_link')

    def test_upi_id_rejects_parameter_injection_and_name_is_optional(self):
        self.client.force_login(self.user)
        for upi_id in ('wrong@bank&pa=other@bank', 'wrong name@bank', 'wrong\nname@bank'):
            self.client.post(reverse('accounts:profile'), {'form_type': 'upi', 'upi_id': upi_id})
            self.user.refresh_from_db()
            self.assertEqual(self.user.upi_id, '')
