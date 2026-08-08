# Raízes do Nordeste - API

Essa é uma API que fiz pra faculdade simulando o backend da "Raízes do Nordeste", uma rede de lanchonetes: cadastro de usuário, login com JWT, cadastro de produto (item de cardápio), controle de estoque e criação de pedido. Usei FastAPI + SQLAlchemy com um banco SQLite mesmo, pra manter simples.

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

Ela tá organizada em pastas: **Auth**, **Produtos**, **Estoque**, **Pedidos**, **Pagamentos** e **Erros**. As requisições encadeiam sozinhas via script na aba Tests (token, id do produto, id do pedido ficam salvos em variáveis de collection), então funciona rodar pasta por pasta, na ordem em que aparecem, com o servidor ligado — sem precisar copiar/colar nada manualmente. Isso foi validado rodando a collection inteira com o Newman (CLI do Postman) direto contra a API: 19 requisições, 20 asserts, 0 falhas.

## Plano de testes

12 cenários no total (6 positivos, 6 negativos), cobrindo autenticação/autorização, validação de dados, regras de negócio do pedido e o mock de pagamento. Todos rodados manualmente contra o servidor local antes de subir a collection — bateu 100% com o esperado. A coluna "Evidência" indica o nome da requisição correspondente na collection Postman.

*(Tabela larga — se for colar no Word, usar orientação paisagem ou reduzir a fonte pra 9pt.)*

| ID | Cenário | Endpoint | Pré-condição | Entrada | Saída esperada | Evidência |
|----|---------|----------|---------------|---------|-----------------|-----------|
| T01 | Cadastrar usuário | `POST /usuario` | — | `{email, senha, perfil: "Cliente"}` | 200 + `{email, perfil}` | Auth/T01 - Cadastrar usuário (Cliente) |
| T02 | Login válido | `POST /auth/login` | usuário cadastrado (T01) | `{email, senha}` | 200 + `accessToken` | Auth/T02 - Login válido (Cliente) |
| T03 | Criar produto (Gerente) | `POST /produtos` | usuário Gerente autenticado | `{nome, preco}` | 200 + `{nome, preco}` | Produtos/T03 - Criar produto (Gerente) |
| T04 | Criar estoque (Gerente) | `POST /estoques` | produto id=1 criado (T03), Gerente autenticado | `{produto_id: 1, quantidade_estoque: 20}` | 200 + `{produtoId, Quantidade_no_estoque}` | Estoque/T04 - Criar estoque (Gerente) |
| T05 | Criar pedido válido | `POST /pedidos` | produto id=1 com estoque=20, Cliente autenticado | `{canalPedido: "loja", itens: [{produto_id: 1, quantidade: 2}]}` | 201 + `pedidoId` + status "Aguardando pagamento" | Pedidos/T05 - Criar pedido válido |
| T06 | Pagamento aprovado | `POST /pagamentos` | pedido id=1 "Aguardando pagamento" (T05) | `{pedido_id: 1, aprovar: true}` | 200 + pedido vira "Sendo preparado" | Pagamentos/T06 - Pagamento aprovado |
| T07 | Acesso sem token | `GET /produtos` | — | sem header `Authorization` | 401 + erro padrão | Erros/T07 - GET /produtos sem token |
| T08 | Criar produto como Cliente | `POST /produtos` | usuário Cliente autenticado | `{nome, preco}` | 403 + "Requer ser Gerente" | Erros/T08 - Criar produto como Cliente |
| T09 | Pedido com produto inexistente | `POST /pedidos` | Cliente autenticado | `{produto_id: 999999, quantidade: 1}` | 404 + "Produto não encontrado" | Erros/T09 - Pedido com produto inexistente |
| T10 | Pedido com estoque insuficiente | `POST /pedidos` | produto id=2 com estoque=1, Cliente autenticado | `{produto_id: 2, quantidade: 5}` | 409 + "Estoque insuficiente" | Erros/T10 - Pedido com estoque insuficiente |
| T11 | Pedido sem `canalPedido` | `POST /pedidos` | Cliente autenticado | `{itens: [{produto_id: 1, quantidade: 1}]}` (sem `canalPedido`) | 422 + erro de validação do campo | Erros/T11 - Pedido sem canalPedido |
| T12 | Pagamento recusado | `POST /pagamentos` | pedido id=2 "Aguardando pagamento" (segundo pedido criado à parte) | `{pedido_id: 2, aprovar: false}` | 200 + pedido vira "Pagamento recusado" | Pagamentos/T12 - Pagamento recusado |

**Logs e auditoria:** não implementado nesta versão. O sistema não registra trilha de auditoria das operações sensíveis. Declarado explicitamente conforme orientação do roteiro; previsto como evolução futura.

**Como reproduzir:** importar o `.json` da collection no Postman, subir a API (`uvicorn main:app --reload`) e seguir a ordem sugerida — cadastrar usuário → login → copiar token → Authorize → criar produto/estoque → criar pedido → pagamento.
