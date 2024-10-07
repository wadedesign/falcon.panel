from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from ..auth.route import get_current_user, User
import sqlite3

router = APIRouter()

class NodeCreate(BaseModel):
    name: str
    ip_address: str
    port: int

class Node(NodeCreate):
    id: int
    status: str
    user_email: str

@router.post("/nodes", response_model=Node)
async def create_node(node: NodeCreate, current_user: User = Depends(get_current_user)):
    conn = sqlite3.connect("database/falcon_auth.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO nodes (name, ip_address, port, status, user_email) VALUES (?, ?, ?, ?, ?)",
        (node.name, node.ip_address, node.port, "offline", current_user.email)
    )
    node_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return Node(id=node_id, status="offline", user_email=current_user.email, **node.dict())

@router.get("/nodes", response_model=List[Node])
async def get_nodes(current_user: User = Depends(get_current_user)):
    conn = sqlite3.connect("database/falcon_auth.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nodes WHERE user_email = ?", (current_user.email,))
    nodes = cursor.fetchall()
    conn.close()
    return [Node(id=node[0], name=node[1], ip_address=node[2], port=node[3], status=node[4], user_email=node[5]) for node in nodes]

# we wil add more - just testing it out for now