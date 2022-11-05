from base.test import TestCase

# Create your tests here.


class TestAuth(TestCase):
    def test_signin(self):
        # self.client.authorize(self.user)
        resp = self.client.post('/auth/signin', {
            "email": self.email,
            "password": self.password
        })
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post('/auth/signin', {
            "email": "wrong",
            "password": self.password
        })
        self.assertEqual(resp.status_code, 401)
        resp = self.client.get("/wddddwdsd")
        self.assertEqual(resp.status_code, 200)
        print(resp.json())
