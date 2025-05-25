import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# My implementation
from fastapi import Depends
from .dependencies import get_db
from sqlalchemy.orm import Session



from app.const import TodoItemStatusCode

from .models.item_model import ItemModel
from .models.list_model import ListModel

DEBUG = os.environ.get("DEBUG", "") == "true"

app = FastAPI(
    title="Python Backend Stations",
    debug=DEBUG,
)

if DEBUG:
    from debug_toolbar.middleware import DebugToolbarMiddleware

    # panelsに追加で表示するパネルを指定できる
    app.add_middleware(
        DebugToolbarMiddleware,
        panels=["app.database.SQLAlchemyPanel"],
    )


class NewTodoItem(BaseModel):
    """TODO項目新規作成時のスキーマ."""

    title: str = Field(title="Todo Item Title", min_length=1, max_length=100)
    description: str | None = Field(default=None, title="Todo Item Description", min_length=1, max_length=200)
    due_at: datetime | None = Field(default=None, title="Todo Item Due")


class UpdateTodoItem(BaseModel):
    """TODO項目更新時のスキーマ."""

    title: str | None = Field(default=None, title="Todo Item Title", min_length=1, max_length=100)
    description: str | None = Field(default=None, title="Todo Item Description", min_length=1, max_length=200)
    due_at: datetime | None = Field(default=None, title="Todo Item Due")
    complete: bool | None = Field(default=None, title="Set Todo Item status as completed")


class ResponseTodoItem(BaseModel):
    id: int
    todo_list_id: int
    title: str = Field(title="Todo Item Title", min_length=1, max_length=100)
    description: str | None = Field(default=None, title="Todo Item Description", min_length=1, max_length=200)
    status_code: TodoItemStatusCode = Field(title="Todo Status Code")
    due_at: datetime | None = Field(default=None, title="Todo Item Due")
    created_at: datetime = Field(title="datetime that the item was created")
    updated_at: datetime = Field(title="datetime that the item was updated")


class NewTodoList(BaseModel):
    """TODOリスト新規作成時のスキーマ."""

    title: str = Field(title="Todo List Title", min_length=1, max_length=100)
    description: str | None = Field(default=None, title="Todo List Description", min_length=1, max_length=200)


class UpdateTodoList(BaseModel):
    """TODOリスト更新時のスキーマ."""

    title: str | None = Field(default=None, title="Todo List Title", min_length=1, max_length=100)
    description: str | None = Field(default=None, title="Todo List Description", min_length=1, max_length=200)


class ResponseTodoList(BaseModel):
    """TODOリストのレスポンススキーマ."""

    id: int
    title: str = Field(title="Todo List Title", min_length=1, max_length=100)
    description: str | None = Field(default=None, title="Todo List Description", min_length=1, max_length=200)
    created_at: datetime = Field(title="datetime that the item was created")
    updated_at: datetime = Field(title="datetime that the item was updated")
    model_config = {"from_attributes": True}


# "/echo": パスオペレーションデコレータ．
@app.get("/echo", tags=["Hello"])  # APIパスの定義，デコレータ．  # noqa: RUF003
def get_echo(message: str, name: str):  # パスオペレーション関数
    return {"Message": message + " " + name + "!"}


@app.get("/plus")
def plus(a: int, b: int):
    """2つの整数を受け取り、その和を返すエンドポイント."""
    return a + b


@app.get("/health", tags=["System"])
def get_health():
    """ヘルスチェック用のエンドポイント."""
    return {"status": "ok"}


@app.get("/lists/{todo_list_id}", response_model=ResponseTodoList, tags=["Todoリスト"])
def get_todo_list(todo_list_id: int, db: Session = Depends(get_db)):
    """指定されたIDのTODOリストを取得するエンドポイント."""
    todo_list = db.query(ListModel).filter(ListModel.id == todo_list_id).first()
    if not todo_list:
        raise HTTPException(status_code=404, detail="Todo list not found")
    return ResponseTodoList.model_validate(todo_list)


@app.post("/lists", response_model=ResponseTodoList, tags=["Todoリスト"])
def post_todo_list(new_todo_list: NewTodoList, db: Session = Depends(get_db)):
    """新しいTODOリストを作成するエンドポイント."""
    todo_list = ListModel(
        title=new_todo_list.title,
        description=new_todo_list.description,
    )
    db.add(todo_list)
    db.commit()
    db.refresh(todo_list)
    return ResponseTodoList.model_validate(todo_list)


@app.put("/lists/{todo_list_id}", response_model=ResponseTodoList, tags=["Todoリスト"])
def put_todo_list(
    todo_list_id: int, update_todo_list: UpdateTodoList, db: Session = Depends(get_db)
):
    """指定されたIDのTODOリストを更新するエンドポイント."""
    todo_list = db.query(ListModel).filter(ListModel.id == todo_list_id).first()
    if not todo_list:
        raise HTTPException(status_code=404, detail="Todo list not found")

    if update_todo_list.title is not None:
        todo_list.title = update_todo_list.title
    if update_todo_list.description is not None:
        todo_list.description = update_todo_list.description

    db.commit()
    db.refresh(todo_list)
    return ResponseTodoList.model_validate(todo_list)
