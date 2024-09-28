import unittest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from app.models import User
from app.schemas import UserCreate, UserUpdate
from app.crud import get_user_by_email, create_user, update_user, delete_user


class TestUserRepository(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)  # Мок для імітації сесії бази даних
        self.user = User(id=1, email="test@example.com")

    async def test_get_user_by_email_found(self):
        """Тест знаходження користувача по email"""
        self.session.query().filter().first.return_value = self.user
        result = await get_user_by_email(db=self.session, email="test@example.com")
        self.assertEqual(result, self.user)

    async def test_get_user_by_email_not_found(self):
        """Тест, коли користувача не знайдено по email"""
        self.session.query().filter().first.return_value = None
        result = await get_user_by_email(db=self.session, email="test@example.com")
        self.assertIsNone(result)

    async def test_create_user(self):
        """Тест створення користувача"""
        user_data = UserCreate(email="test@example.com", password="password123")
        self.session.add.return_value = None
        result = await create_user(db=self.session, user=user_data)
        self.assertEqual(result.email, user_data.email)
        self.session.add.assert_called_once()  # Перевірка, що користувач доданий у базу

    async def test_update_user(self):
        """Тест оновлення користувача"""
        user_data = UserUpdate(email="new@example.com")
        self.session.query().filter().first.return_value = self.user
        result = await update_user(db=self.session, user_id=1, user_update=user_data)
        self.assertEqual(result.email, user_data.email)

    async def test_delete_user(self):
        """Тест видалення користувача"""
        self.session.query().filter().first.return_value = self.user
        result = await delete_user(db=self.session, user_id=1)
        self.assertEqual(result, self.user)
        self.session.delete.assert_called_once()  # Перевірка, що користувач видалений з бази


if __name__ == '__main__':
    unittest.main()
