from fastapi import FastAPI, HTTPException
import os 
import psycopg
from pydantic import BaseModel

app = FastAPI() 

DATABASE_URL = os.getenv("DATABASE_URL")


class TaskCreate(BaseModel):
    title: str
    completed: bool = False


class TaskUpdate(BaseModel):
    completed: bool


def row_to_task(row):
    return {
        "id": row[0],
        "title": row[1],
        "completed": row[2]
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-health")
def db_health():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute ("SELECT 1") 

            return {"database": "ok"}


@app.get("/tasks")
def get_tasks():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tasks;")

            rows = cursor.fetchall()

            tasks = []

            for row in rows:                
                tasks.append(row_to_task(row)) 

    return tasks 



@app.post("/tasks")
def create_task(task: TaskCreate):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO tasks (title, completed) VALUES (%s, %s) RETURNING id, title, completed",
                (task.title, task.completed)
            )
            row = cursor.fetchone() 
    return row_to_task(row) 


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor: 
            cursor.execute(
                "DELETE FROM tasks WHERE id = %s RETURNING id, title, completed",
                (task_id,)
            )

            row = cursor.fetchone()

            if row is None: 
                raise HTTPException(
                    status_code=404, 
                    detail="Task not found"
                    )
            
            return row_to_task(row) 


@app.patch("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor: 
            cursor.execute(
                "UPDATE tasks SET completed = %s WHERE id = %s RETURNING id, title, completed",                    
                (task.completed, task_id)
            )

            row = cursor.fetchone()

            if row is None: 
                raise HTTPException(
                    status_code=404,
                    detail="Task not found"
                )

            return row_to_task(row) 