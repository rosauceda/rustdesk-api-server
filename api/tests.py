import datetime
import json

from django.test import TestCase

from api.models import RustDeskPeer, ShareLink, UserProfile


class ShareFlowTests(TestCase):
    def setUp(self):
        self.owner = UserProfile.objects.create(
            username='owner_user',
            rid='100000001',
            uuid='owner-uuid',
            rtype='desktop',
            is_active=True,
        )
        self.owner.set_password('Password123')
        self.owner.save(update_fields=['password'])

        self.receiver = UserProfile.objects.create(
            username='receiver_user',
            rid='100000002',
            uuid='receiver-uuid',
            rtype='desktop',
            is_active=True,
        )
        self.receiver.set_password('Password123')
        self.receiver.save(update_fields=['password'])

        for rid, alias in [('111111111', 'pc-1'), ('222222222', 'pc-2'), ('333333333', 'pc-3')]:
            RustDeskPeer.objects.create(
                uid=str(self.owner.id),
                rid=rid,
                username='osuser',
                hostname=f'host-{rid[-1]}',
                alias=alias,
                platform='linux',
                tags='',
                rhash='',
            )

    def _login(self, user):
        self.client.force_login(user)

    def _create_share_link(self, selected_rids):
        payload = [{'value': i + 1, 'title': f'{rid}|alias'} for i, rid in enumerate(selected_rids)]
        response = self.client.post('/api/share', {'data': json.dumps(payload)})
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content.decode())
        self.assertEqual(body.get('code'), 1)
        return body['shash']

    def test_share_page_with_trailing_slash_renders_share_ui(self):
        self._login(self.owner)
        response = self.client.get('/api/share/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'showdevice')
        self.assertContains(response, '/api/share')

    def test_share_link_is_single_use(self):
        self._login(self.owner)
        shash = self._create_share_link(['111111111', '222222222'])

        self.client.logout()
        self._login(self.receiver)
        first = self.client.get(f'/api/share/{shash}')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(RustDeskPeer.objects.filter(uid=str(self.receiver.id)).count(), 2)
        self.assertTrue(ShareLink.objects.get(shash=shash).is_used)

        second = self.client.get(f'/api/share/{shash}')
        self.assertEqual(second.status_code, 200)
        self.assertEqual(RustDeskPeer.objects.filter(uid=str(self.receiver.id)).count(), 2)
        self.assertTrue(ShareLink.objects.get(shash=shash).is_used)

    def test_expired_share_link_cannot_be_claimed(self):
        self._login(self.owner)
        shash = self._create_share_link(['111111111'])
        ShareLink.objects.filter(shash=shash).update(
            create_time=datetime.datetime.now() - datetime.timedelta(minutes=16)
        )

        self.client.logout()
        self._login(self.receiver)
        response = self.client.get(f'/api/share/{shash}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RustDeskPeer.objects.filter(uid=str(self.receiver.id)).count(), 0)
        self.assertTrue(ShareLink.objects.get(shash=shash).is_expired)
