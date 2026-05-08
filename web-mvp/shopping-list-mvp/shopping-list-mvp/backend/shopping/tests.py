from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class ShoppingMVPScenarioTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.User = get_user_model()

    def register(self, email: str):
        response = self.client.post(
            "/api/auth/register/",
            {"email": email, "password": "strong-pass-123"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        return response.data

    def auth(self, access: str):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_main_user_flow(self):
        owner = self.register("owner@example.com")
        self.auth(owner["access"])

        create_list = self.client.post("/api/lists/", {"name": "Продукты"}, format="json")
        self.assertEqual(create_list.status_code, 201, create_list.content)
        list_id = create_list.data["id"]

        create_invite = self.client.post(f"/api/lists/{list_id}/invite/", {}, format="json")
        self.assertEqual(create_invite.status_code, 201, create_invite.content)
        invite_code = create_invite.data["code"]

        product = self.client.post(
            f"/api/lists/{list_id}/products/",
            {"name": "Молоко", "quantity": "2", "unit": "л", "category_name": "Молочка"},
            format="json",
        )
        self.assertEqual(product.status_code, 201, product.content)
        product_id = product.data["id"]

        member = self.register("member@example.com")
        self.auth(member["access"])
        accept = self.client.post(f"/api/invitations/{invite_code}/accept/", {}, format="json")
        self.assertEqual(accept.status_code, 200, accept.content)
        self.assertEqual(accept.data["status"], "joined")

        buy = self.client.post(f"/api/products/{product_id}/buy/", {}, format="json")
        self.assertEqual(buy.status_code, 200, buy.content)
        self.assertTrue(buy.data["is_bought"])

        history = self.client.get(f"/api/lists/{list_id}/history/")
        self.assertEqual(history.status_code, 200, history.content)
        self.assertEqual(len(history.data), 1)
