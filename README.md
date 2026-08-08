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

1. Cadastrar um usuário com `perfil: "Gerente"` (`POST /usuario`)
2. Fazer login com esse usuário (`POST /auth/login`)
3. Copiar o token que volta no login
4. Clicar em "Authorize" e colar o token
5. Criar um produto (`POST /produtos`)
6. Criar estoque pro produto que acabou de criar (`POST /estoques`)
7. Cadastrar/logar agora com um usuário `perfil: "Cliente"` e criar o pedido (`POST /pedidos`)
8. Pagar o pedido (`POST /pagamentos`, com `aprovar: true` ou `false`)

Se pular alguma etapa (tipo criar pedido sem ter estoque cadastrado) a API vai reclamar, então é melhor seguir essa ordem mesmo. Só o `Gerente` consegue criar produto e estoque — se tentar com `Cliente` a API responde 403.

# Testando pelo Postman

Tem uma collection pronta no repo: [`Raizes-do-Nordeste-API.postman_collection.json`](Raizes-do-Nordeste-API.postman_collection.json). É só importar no Postman (Import → File).

Ela tá organizada em pastas: **Auth**, **Produtos**, **Estoque**, **Pedidos**, **Pagamentos** e **Erros**. As requisições encadeiam sozinhas (token, id do produto, id do pedido ficam salvos em variáveis de collection), então funciona rodar pasta por pasta, na ordem em que aparecem, com o servidor ligado.

## Plano de testes

12 cenários no total (6 positivos, 6 negativos), cobrindo autenticação/autorização, validação de dados, regras de negócio do pedido e o mock de pagamento:

| ID | Cenário | Endpoint | Entrada (resumo) | Status esperado | Status obtido |
|----|---------|----------|-------------------|------------------|----------------|
| T01 | Cadastrar usuário | `POST /usuario` | email/senha/perfil válidos | 200 | 200 |
| T02 | Login válido | `POST /auth/login` | credenciais corretas | 200 + token | 200 |
| T03 | Criar produto (Gerente) | `POST /produtos` | token de Gerente | 200 | 200 |
| T04 | Criar estoque (Gerente) | `POST /estoques` | token de Gerente | 200 | 200 |
| T05 | Criar pedido válido | `POST /pedidos` | produto e estoque existentes | 201 | 201 |
| T06 | Pagamento aprovado | `POST /pagamentos` | `aprovar: true` | 200 + "Sendo preparado" | 200 |
| T07 | Acesso sem token | `GET /produtos` | sem header Authorization | 401 | 401 |
| T08 | Criar produto como Cliente | `POST /produtos` | token de Cliente | 403 | 403 |
| T09 | Pedido com produto inexistente | `POST /pedidos` | `produto_id` que não existe | 404 | 404 |
| T10 | Pedido com estoque insuficiente | `POST /pedidos` | quantidade maior que o estoque | 409 | 409 |
| T11 | Pedido sem `canalPedido` | `POST /pedidos` | campo obrigatório ausente | 422 | 422 |
| T12 | Pagamento recusado | `POST /pagamentos` | `aprovar: false` | 200 + "Pagamento recusado" | 200 |

Todos rodados manualmente contra o servidor local antes de subir a collection — bateu 100% com o esperado.

## Logs/auditoria — não implementado

O roteiro pede registro de logs/auditoria das operações, e isso **não foi implementado** neste projeto. Não existe nenhuma tabela ou arquivo guardando quem fez o quê e quando (só o que já é padrão do próprio `uvicorn` no terminal). Ficou de fora por causa do tempo pra fechar o fluxo principal (autenticação, autorização, pedido e pagamento) primeiro — é uma melhoria futura, não uma coisa que esqueci sem perceber.
