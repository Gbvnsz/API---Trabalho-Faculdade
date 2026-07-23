from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy import Column, Integer, String, Float

engine = create_engine("sqlite:///banco.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class produto(BaseModel):
    nome: str
    preco: float
    
class Produto(Base):
    __tablename__ = "produtos"
    idproduto = Column(Integer, primary_key=True)
    nome = Column(String)
    preco = Column(Float)

Base.metadata.create_all(engine)

@app.post("/bancodados")
def criar_produto(produtos: produto, db: Session = Depends(get_db)): #FastAPI, antes de rodar minha função, chama o get_db, pega a session que ele fornece, e me entrega no parâmetro db
    novo_produto = Produto(nome = produtos.nome, preco = produtos.preco)
    db.add(novo_produto) # coloca na fila 
    db.commit() # confirma 
    db.refresh(novo_produto) # recarrega o objeto
    return {"nome": novo_produto.nome, "preco": novo_produto.preco}
