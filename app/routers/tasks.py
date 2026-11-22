from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate, TaskResponse, MessageResponse

router = APIRouter()

# 1. Запрос: POST /api/v1/tasks/ — Создание задачи
@router.post(
    "/tasks/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую задачу",
    description="Создает запись о задаче в базе данных. Требует обязательное непустое поле title."
)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(
        title=task_in.title,
        description=task_in.description,
        is_completed=task_in.is_completed
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

# 2. Запрос: GET /api/v1/tasks/ — Получение списка задач с фильтрацией и пагинацией
@router.get(
    "/tasks/",
    response_model=List[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить список задач",
    description="Возвращает список всех задач. Поддерживает фильтрацию по статусу is_completed."
)
def read_tasks(
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(100, ge=1, le=100, description="Количество возвращаемых записей"),
    completed: Optional[bool] = Query(None, description="Фильтр по статусу выполнения"),
    db: Session = Depends(get_db)
):
    query = db.query(Task)
    if completed is not None:
        query = query.filter(Task.is_completed == completed)
    return query.offset(skip).limit(limit).all()

# 3. Запрос: GET /api/v1/tasks/{task_id} — Получение задачи по ID
@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить задачу по ID",
    description="Возвращает конкретную задачу. Если ID не найден, возвращает 404 Not Found."
)
def read_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача с идентификатором {task_id} не найдена"
        )
    return task

# 4. Запрос: PUT /api/v1/tasks/{task_id} — Полное/частичное обновление задачи
@router.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить задачу",
    description="Обновляет переданные поля задачи по ID. Если задача не найдена — 404 Not Found."
)
def update_task(task_id: int, task_in: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача с идентификатором {task_id} не найдена для обновления"
        )
    
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    return task

# 5. Запрос: DELETE /api/v1/tasks/{task_id} — Удаление задачи
@router.delete(
    "/tasks/{task_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Удалить задачу",
    description="Удаляет задачу по ID. Если задача не существует — 404 Not Found."
)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задача с идентификатором {task_id} не найдена для удаления"
        )
    
    db.delete(task)
    db.commit()
    return {"message": f"Задача с ID {task_id} успешно удалена", "detail": f"ID={task_id}"}
