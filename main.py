import os
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import declarative_base, sessionmaker,Session
from sqlalchemy import ForeignKey, create_engine
from sqlalchemy import Column, Integer, String, Float, Boolean
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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
        
def criarToken(dados: dict):
    token_lido = dados.copy()
    expira = datetime.utcnow() + timedelta(minutes=30)
    token_lido.update({"exp": expira})
    token = jwt.encode(token_lido, SECRET_KEY, algorithm = ALGORITHM)
    return token

def usuariosCadastrados(token: str = Depends(oauth2_scheme)):
    try:
        conteudo = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = conteudo.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido.")
        return conteudo
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")
class produto(BaseModel):
    nome: str
    preco: float

class Produto(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    preco = Column(Float)
    
class usuario(BaseModel):
    email: str
    senha: str
    perfil: str
    
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    senha = Column(String)
    perfil = Column(String)

class estoque(BaseModel):
    produto_id: int
    quantidade_estoque: int
    
class Estoque(Base):
    __tablename__ = "estoque"
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id")) 
    quantidade_estoque = Column(Integer, index=True)
    
class item_entrada(BaseModel):
    produto_id: int
    quantidade: int    
    
class Item_pedido(Base):
    __tablename__ = "itens_pedidos"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    quantidade_pedido = Column(Integer)
    preco_pedido = Column(Float)
    
class pedido(BaseModel):
    canalPedido: str
    itens: List[item_entrada]
    
class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"))
    canalPedido = Column(String, index=True)  
    status = Column(String, index=True)
    total = Column(Float) 

class pagamento(BaseModel):
    pedido_id: int
    
class Pagamento(Base):
    __tablename__ = "pagamentos"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))

Base.metadata.create_all(bind=engine)

@app.post("/produtos")
def criar_produto(produto: produto, db: Session = Depends(get_db)):
    novo_produto = Produto(nome=produto.nome, preco=produto.preco)
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return {"nome": novo_produto.nome, "preco": novo_produto.preco}

@app.get("/produtos")
def lista_produtos(db: Session = Depends(get_db), usuario: dict = Depends(usuariosCadastrados)):
    lista_produtos = db.query(Produto).all()
    return lista_produtos

@app.post("/usuario")
def cadastro(usuario: usuario, db: Session = Depends(get_db)):
    novo_cadastro = Usuario(email=usuario.email, senha = pwd_context.hash(usuario.senha) , perfil = usuario.perfil)
    db.add(novo_cadastro)
    db.commit()
    db.refresh(novo_cadastro)
    return {"email": novo_cadastro.email, "perfil": novo_cadastro.perfil}

@app.post("/auth/login")
def verificacao(email_recebido: usuario, db: Session = Depends(get_db)):
    usuario_cadastrado = db.query(Usuario).filter(Usuario.email == email_recebido.email).first()
    if usuario_cadastrado is None:
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    if not pwd_context.verify(email_recebido.senha, usuario_cadastrado.senha):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    token = criarToken({"sub": usuario_cadastrado.email, "perfil": usuario_cadastrado.perfil})
    return {"accessToken": token, "tokenType": "Bearer"}

@app.post("/pedidos", status_code=201)
def criar_pedido(dados: pedido, db: Session = Depends(get_db), usuario_token: dict = Depends(usuariosCadastrados)):
    
    total = 0.0
    
    itens_validados = []
    
    for item in dados.itens:
        
        produto_banco = db.query(Produto).filter(Produto.id == item.produto_id).first()
        if produto_banco is None:
            raise HTTPException(status_code=404, detail="Produto não encontrado.")
        
        estoque_banco = db.query(Estoque).filter(Estoque.produto_id == item.produto_id).first()
        if estoque_banco is None or estoque_banco.quantidade_estoque < item.quantidade:
            raise HTTPException(status_code=409, detail="Estoque insuficiente.")
        
        total = total + (produto_banco.preco * item.quantidade)
        
        itens_validados.append({
            "produto_id": item.produto_id,
            "quantidade": item.quantidade,
            "preco": produto_banco.preco,
            "estoque": estoque_banco
        })
        
    email_do_token = usuario_token.get("sub")
    cliente = db.query(Usuario).filter(Usuario.email == email_do_token).first()
    novo_pedido = Pedido(cliente_id = cliente_id, canalPedido= dados.canalPedido, status="AGUARDANDO_PAGAMENTO", total=total)
    db.add(novo_pedido)
    db.commit()
    db.refresh(novo_pedido)
    
    for validado in itens_validados:
        novo_item = Item_pedido(
            pedido_id=novo_pedido.id,           
            produto_id=validado["produto_id"],
            quantidade_pedido=validado["quantidade"],
            preco_pedido=validado["preco"]       
        )
        db.add(novo_item)
    
        validado["estoque"].quantidade_estoque = validado["estoque"].quantidade_estoque - validado["quantidade"]

        db.commit()
    
    db.commit()
    
    return {"pedidoId": novo_pedido.id, "status": novo_pedido.status, "total": novo_pedido.total}

@app.post("/estoques")
def criar_estoque(estoque: estoque, db: Session = Depends(get_db)):
    novo_estoque = Estoque(produto_id= estoque.produto_id, quantidade_estoque= estoque.quantidade_estoque)
    db.add(novo_estoque)
    db.commit()
    db.refresh(novo_estoque)
    return {"produtoId": novo_estoque.produto_id, "Quantidade_no_estoque": novo_estoque.quantidade_estoque}