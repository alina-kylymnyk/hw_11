from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .env.app import crud, models, schemas, auth
from .env.app.database import SessionLocal, engine, get_db
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address
from jose import jwt  # Не забудьте імплементувати jwt

# Конфігурація лімітування запитів
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter

# Ініціалізація моделей
models.Base.metadata.create_all(bind=engine)

@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Реєструє нового користувача.

    Args:
        user (schemas.UserCreate): Дані користувача для реєстрації.
        db (Session): Сесія бази даних.

    Returns:
        schemas.User: Створений користувач.

    Raises:
        HTTPException: Якщо електронна пошта вже зареєстрована.
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/token", response_model=dict)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Аутентифікує користувача і повертає JWT токен.

    Args:
        form_data (OAuth2PasswordRequestForm): Дані для аутентифікації.
        db (Session): Сесія бази даних.

    Returns:
        dict: Доступний токен і тип токена.

    Raises:
        HTTPException: Якщо електронна пошта або пароль невірні.
    """
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/contacts/", response_model=list[schemas.Contact])
def read_contacts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    """
    Повертає список контактів.

    Args:
        skip (int): Кількість пропущених записів (за замовчуванням 0).
        limit (int): Максимальна кількість повернених записів (за замовчуванням 10).
        db (Session): Сесія бази даних.
        current_user (schemas.User): Аутентифікований користувач.

    Returns:
        list[schemas.Contact]: Список контактів.
    """
    return crud.get_contacts(db, skip=skip, limit=limit)

@app.get("/contacts/{contact_id}", response_model=schemas.Contact)
def read_contact(contact_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    """
    Повертає контакт за його ID.

    Args:
        contact_id (int): ID контакту.
        db (Session): Сесія бази даних.
        current_user (schemas.User): Аутентифікований користувач.

    Returns:
        schemas.Contact: Знайдений контакт.

    Raises:
        HTTPException: Якщо контакт не знайдено.
    """
    contact = crud.get_contact(db, contact_id=contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@app.put("/contacts/{contact_id}", response_model=schemas.Contact)
def update_contact(contact_id: int, contact: schemas.ContactCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    """
    Оновлює контакт за його ID.

    Args:
        contact_id (int): ID контакту для оновлення.
        contact (schemas.ContactCreate): Дані для оновлення контакту.
        db (Session): Сесія бази даних.
        current_user (schemas.User): Аутентифікований користувач.

    Returns:
        schemas.Contact: Оновлений контакт.

    Raises:
        HTTPException: Якщо контакт не знайдено.
    """
    updated_contact = crud.update_contact(db, contact_id=contact_id, contact=contact)
    if updated_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated_contact

@app.delete("/contacts/{contact_id}", response_model=schemas.Contact)
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    """
    Видаляє контакт за його ID.

    Args:
        contact_id (int): ID контакту для видалення.
        db (Session): Сесія бази даних.
        current_user (schemas.User): Аутентифікований користувач.

    Returns:
        schemas.Contact: Видалений контакт.

    Raises:
        HTTPException: Якщо контакт не знайдено.
    """
    deleted_contact = crud.delete_contact(db, contact_id=contact_id)
    if deleted_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return deleted_contact

@app.get("/verify_email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Верифікує електронну пошту користувача за токеном.

    Args:
        token (str): Токен для верифікації електронної пошти.
        db (Session): Сесія бази даних.

    Returns:
        dict: Результат верифікації.

    Raises:
        HTTPException: Якщо токен недійсний.
    """
    email = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM]).get("sub")
    user = crud.get_user_by_email(db, email=email)
    if user:
        user.is_verified = True  # Припускаємо, що в моделі є поле для перевірки
        db.commit()
        return {"detail": "Email verified successfully"}
    raise HTTPException(status_code=400, detail="Invalid token")
