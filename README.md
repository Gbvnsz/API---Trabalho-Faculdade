# API Mercado

Essa é uma API que fiz pra faculdade simulando o backend de um mercado: cadastro de usuário, login com JWT, cadastro de produto, controle de estoque e criação de pedido. Usei FastAPI + SQLAlchemy com um banco SQLite mesmo, pra manter simples.

# Requisitos

- Python 3.x
- fastapi
- uvicorn
- sqlalchemy
- passlib
- bcrypt==4.0.1
- python-jose
- pydantic
- python-dotenv

# Instalando

```bash
pip install -r requirements.txt
```

(o requirements.txt já tá no repo com essas libs acima, uma por linha)

# Sobre a SECRET_KEY

No começo eu tinha deixado a `SECRET_KEY` fixa no `main.py` (gerei ela pelo PowerShell), mas ajustei pra vir de variável de ambiente mesmo, usando `python-dotenv`. Agora o código só faz `SECRET_KEY = os.getenv("SECRET_KEY")`.

Pra rodar o projeto, crie um arquivo `.env` na raiz (esse arquivo não vai pro git, tá no `.gitignore`) com:

```
SECRET_KEY=sua_chave_aqui
```

Tem um `.env.example` no repo só como referência do formato. Sem o `.env` com a chave, a aplicação sobe mas a assinatura do token fica quebrada, então não esquece de criar ele antes de rodar.

# Banco de dados

Não precisa criar nada na mão. Quando a aplicação sobe, o `Base.metadata.create_all()` já cria o `banco.db` (SQLite) com todas as tabelas (produtos, usuarios, estoque, pedidos, itens_pedidos, pagamentos).

# Rodando

```bash
uvicorn main:app --reload
```

# Testando (Swagger)

Com o servidor rodando, a documentação fica em:

`http://127.0.0.1:8000/docs`

Pra testar dá pra usar direto por lá. A ordem que funciona é essa:

1. Cadastrar um usuário (`POST /usuario`)
2. Fazer login (`POST /auth/login`)
3. Copiar o token que volta no login
4. Clicar em "Authorize" e colar o token
5. Criar um produto (`POST /produtos`)
6. Criar estoque pro produto que acabou de criar (`POST /estoques`)
7. Criar o pedido (`POST /pedidos`)

Se pular alguma etapa (tipo criar pedido sem ter estoque cadastrado) a API vai reclamar, então é melhor seguir essa ordem mesmo.
