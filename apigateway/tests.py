import requests
import time
from base.test import TestCase
from .models import Api
# Create your tests here.


class TestApiGateway(TestCase):

    def speed_test(self):
        start = time.perf_counter()
        resp = self.client.get(
            "/nearby/?latitude=37.48764750944954&longitude=127.02528032814617&filter_simple_location=서초동,남부순환로,효령로68길,강남대로")
        elapsed = time.perf_counter()-start
        print(f"{elapsed=}")
        return resp

    def test_API_Model(self):
        API = Api.objects.create(
            name="nearby",
            request_path='nearby',
            scheme=Api.SchemeType.HTTPS,
            upstream_url="api.test.palzakspot.com/discover/nearby",
            plugin=0,
        )
        self.assertEqual(API.name, 'nearby')
        # resp = self.speed_test()
        # self.assertEqual(resp.status_code, 200)
        for i in range(5):
            resp = self.speed_test()

        start = time.perf_counter()
        requests.get(
            "https://honeycombpizza.link/nearby/?latitude=37.48764750944954&longitude=127.02528032814617&filter_simple_location=서초동,남부순환로,효령로68길,강남대로")
        elapsed = time.perf_counter()-start
        print(f"{elapsed=}")

        start = time.perf_counter()
        requests.get(
            "https://honeycombpizza.link/nearby/?latitude=37.48764750944954&longitude=127.02528032814617&filter_simple_location=서초동,남부순환로,효령로68길,강남대로")
        elapsed = time.perf_counter()-start
        print(f"{elapsed=}")

        start = time.perf_counter()
        requests.get(
            "https://honeycombpizza.link/nearby/?latitude=37.48764750944954&longitude=127.02528032814617&filter_simple_location=서초동,남부순환로,효령로68길,강남대로")
        elapsed = time.perf_counter()-start
        print(f"{elapsed=}")
