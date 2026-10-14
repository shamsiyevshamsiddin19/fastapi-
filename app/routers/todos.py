from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from ..schemas import TodoCreate, TodoResponse, TodoUpdate

router = APIRouter(
    prefix="/todos",
    tags=["Todos"]
)

# Xotiradagi vazifalar bazasi (Mock DB)
todos_db = [
    {
        "id": 1,
        "title": "FastAPI darslarini yakunlash",
        "completed": True
    },
    {
        "id": 2,
        "title": "PostgreSQL bazasini ulash",
        "completed": False
    },
    {
        "id": 3,
        "title": "Amaliy mashg'ulotlarni topshirish",
        "completed": False
    }
]
todo_id_counter = 4


@router.get("/", response_model=List[TodoResponse])
def get_todos(
    completed: Optional[bool] = Query(None, description="Bajarilganlik holati bo'yicha filter (True/False)"),
    skip: int = Query(0, ge=0, description="Tashlab o'tiladigan vazifalar soni"),
    limit: int = Query(10, ge=1, le=100, description="Olinadigan maksimal vazifalar soni")
):
    """
    Barcha To-Do vazifalar ro'yxatini olish.

    - **completed**: Ixtiyoriy filter. Agar berilsa, faqat bajarilgan yoki bajarilmaganlarni qaytaradi
    - **skip**: Sahifalash uchun boshlang'ich qadam
    - **limit**: Sahifadagi maksimal elementlar soni
    - **Returns**: Vazifalar ro'yxati
    """
    filtered_todos = todos_db
    if completed is not None:
        filtered_todos = [t for t in todos_db if t["completed"] == completed]
    return filtered_todos[skip : skip + limit]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TodoResponse)
def create_todo(todo: TodoCreate):
    """
    Yangi To-Do vazifa qo'shish.

    - **title**: Vazifa sarlavhasi
    - **completed**: Bajarilganlik holati (default: False)
    - **Returns**: Yaratilgan yangi vazifa
    """
    global todo_id_counter
    todo_dict = todo.model_dump()
    todo_dict["id"] = todo_id_counter
    todo_id_counter += 1
    todos_db.append(todo_dict)
    return todo_dict


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int):
    """
    Bitta To-Do vazifani ID orqali olish.

    - **todo_id**: Vazifaning ID raqami
    - **Returns**: Vazifa ma'lumotlari
    - **Raises**: 404 (Agar vazifa topilmasa)
    """
    for todo in todos_db:
        if todo["id"] == todo_id:
            return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vazifa topilmadi")


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, updated_todo: TodoUpdate):
    """
    Mavjud To-Do vazifani yangilash.

    - **todo_id**: Yangilanadigan vazifa ID si
    - **updated_todo**: Yangi sarlavha va/yoki completed holati
    - **Returns**: Yangilangan vazifa
    - **Raises**: 404 (Agar vazifa topilmasa)
    """
    for index, todo in enumerate(todos_db):
        if todo["id"] == todo_id:
            update_data = updated_todo.model_dump(exclude_unset=True)
            todos_db[index].update(update_data)
            return todos_db[index]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vazifa topilmadi")


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int):
    """
    To-Do vazifani ID bo'yicha o'chirish.

    - **todo_id**: O'chiriladigan vazifa ID si
    - **Returns**: 204 No Content
    - **Raises**: 404 (Agar vazifa topilmasa)
    """
    for index, todo in enumerate(todos_db):
        if todo["id"] == todo_id:
            todos_db.pop(index)
            return None
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vazifa topilmadi")
