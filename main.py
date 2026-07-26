from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import declarative_base, sessionmaker,Session
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

# Usei o powershell para gerar uma chave aleatória 
SECRET_KEY = "vp75eutcSmaOEZlJCV6M0ULHhqQWdno89B41KGyNPjRDiszkYw"   
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