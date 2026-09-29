# E-commerce API — Django REST Framework + AWS Elastic Beanstalk

API REST do tema **E-commerce** (disciplina Projeto de Cloud), feita a partir do projeto de aula
[RestEB](https://github.com/jonh-carvalho/RestEB) e publicada no **AWS Elastic Beanstalk** com o arquivo `deploy/app.zip`.

## 🔗 API publicada

> **URL da API:** http://ecommerce-as-api-env.eba-jpapde3u.us-east-1.elasticbeanstalk.com/api/
>
> **Django Admin:** http://ecommerce-as-api-env.eba-jpapde3u.us-east-1.elasticbeanstalk.com/admin/
>
> **Health check:** http://ecommerce-as-api-env.eba-jpapde3u.us-east-1.elasticbeanstalk.com/ → `{"status": "ok", ...}`
>
> Região: **us-east-1 (N. Virginia)** · Plataforma: Python 3.12 / Amazon Linux 2023 · Single instance

| Item | Nome |
|---|---|
| Projeto Django | `ecommerce` |
| App Django | `vendas` |
| Classes (models) | `Cliente` e `Pedido` |
| Relacionamento | 1:N — um `Cliente` possui vários `Pedido`s (`Pedido.cliente` → `ForeignKey`) |

---

## 1. Alterações em relação ao projeto de aula

| Antes (RestEB) | Agora |
|---|---|
| Projeto `catalogo` | Projeto **`ecommerce`** |
| App `produtos` com a classe `Produto` | **Removidos**. Criado o app **`vendas`** |
| — | Models **`Cliente`** e **`Pedido`** com relacionamento 1:N |
| `/api/produtos/` | `/api/clientes/` e `/api/pedidos/` (CRUD completo) |
| Admin apenas registrava `Produto` | Admin personalizado: listas, filtros, busca e pedidos *inline* dentro do cliente |
| Superusuário criado manualmente | Comando **`python manage.py criar_admin`**, executado automaticamente no deploy |
| Driver `mysqlclient` (precisa compilar no servidor) | Driver **`PyMySQL`** (Python puro, sem compilação no EB) |
| `.ebextensions` com vários arquivos conflitantes | Um único **`.ebextensions/01_django.config`** |
| Cookies "secure" sempre ligados em produção | Ligados só com HTTPS — sem isso o login no admin falha no domínio HTTP do EB |
| — | IP privado da instância adicionado a `ALLOWED_HOSTS` (health check do EB não recebe mais erro 400) |
| — | 13 testes automatizados (`vendas/tests.py`) |
| — | Script `deploy/gerar_app_zip.py` que gera o `app.zip` corretamente |

### Modelos

**Cliente**: `nome`, `email` (único), `cpf` (único), `telefone`, `endereco`, `cidade`, `estado` (UF), `ativo`, `data_cadastro`.

**Pedido**: `cliente` (FK → Cliente, `related_name='pedidos'`, `on_delete=PROTECT`), `data_pedido`, `status`
(`PENDENTE`, `PAGO`, `ENVIADO`, `ENTREGUE`, `CANCELADO`), `forma_pagamento` (`PIX`, `CARTAO`, `BOLETO`),
`valor_total` (não pode ser negativo), `endereco_entrega`, `observacoes`.

`PROTECT` impede apagar um cliente que já tem pedidos (histórico de vendas preservado); nesse caso a API retorna `409`.

---

## 2. Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Health check → `{"status": "ok"}` |
| GET / POST | `/api/clientes/` | Lista / cria clientes |
| GET / PUT / PATCH / DELETE | `/api/clientes/{id}/` | Detalhe (com resumo dos pedidos) / atualiza / remove |
| GET | `/api/clientes/{id}/pedidos/` | Pedidos completos de um cliente |
| GET / POST | `/api/pedidos/` | Lista / cria pedidos |
| GET | `/api/pedidos/?cliente=1&status=PAGO` | Filtros por cliente e/ou status |
| GET / PUT / PATCH / DELETE | `/api/pedidos/{id}/` | Detalhe / atualiza / remove |
| — | `/admin/` | Django Admin |

Exemplos (troque a URL base pela do seu ambiente):

```bash
curl -X POST http://localhost:8000/api/clientes/ -H "Content-Type: application/json" \
  -d '{"nome":"Ana Lima","email":"ana@loja.com","cpf":"321.654.987-00","cidade":"Rio de Janeiro","estado":"RJ"}'

curl -X POST http://localhost:8000/api/pedidos/ -H "Content-Type: application/json" \
  -d '{"cliente":1,"valor_total":"349.90","forma_pagamento":"PIX","endereco_entrega":"Rua do Catete, 10"}'

curl -X PATCH http://localhost:8000/api/pedidos/1/ -H "Content-Type: application/json" -d '{"status":"PAGO"}'

curl http://localhost:8000/api/clientes/1/      # traz total_pedidos e a lista resumida de pedidos
```

Também é possível testar pelo navegador (interface *browsable* do DRF) abrindo `/api/`.

---

## 3. Executar localmente

Requisitos: **Python 3.12+** (o Django 6 não roda em versões anteriores).

```bash
git clone https://github.com/AntonioSinhorelli/ecommerce-api.git
cd ecommerce-api

python -m venv .venv
# Windows:       .venv\Scripts\activate
# Linux / macOS: source .venv/bin/activate

pip install -r requirements.txt

# Configuração
cp .env.example .env          # Windows: copy .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# cole a chave gerada em SECRET_KEY no .env e defina DJANGO_SUPERUSER_PASSWORD

python manage.py migrate
python manage.py criar_admin  # cria o superusuário com os dados do .env
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/api/` e `http://127.0.0.1:8000/admin/`.

Sem variáveis `MYSQL_*` no `.env` o projeto usa **SQLite**. Para MySQL local, descomente as variáveis `MYSQL_*` no `.env`.

Rodar os testes:

```bash
python manage.py test vendas
```

---

## 4. Deploy na AWS Elastic Beanstalk com `app.zip`

### 4.1 Gerar o `app.zip`

```bash
python deploy/gerar_app_zip.py
```

O arquivo `deploy/app.zip` fica com os arquivos **na raiz** (sem pasta pai) e **sem** `.env`, `db.sqlite3`, `.venv` e `__pycache__`:

```
manage.py  requirements.txt  Procfile  runtime.txt
.ebextensions/01_django.config
.platform/hooks/postdeploy/01_permissoes_banco.sh
.platform/confighooks/postdeploy/01_permissoes_banco.sh
ecommerce/   (settings, urls, wsgi)
vendas/      (models, serializers, views, urls, admin, migrations, criar_admin)
```

> ⚠️ Não use "Enviar para > Pasta compactada" do Windows sobre a pasta do projeto: ele cria uma pasta pai dentro do zip
> e o EB não encontra o `manage.py`. Use o script acima.

### 4.2 Criar o ambiente no Console AWS

1. Console AWS → **Elastic Beanstalk** → **Create application**.
2. **Environment tier:** Web server environment.
3. **Application name:** `ecommerce-api` · **Environment name:** ex. `ecommerce-api-env`.
4. **Platform:** Python → **Python 3.12** (Amazon Linux 2023).
5. **Application code:** *Upload your code* → *Local file* → selecione **`deploy/app.zip`**.
6. **Presets:** *Single instance* (suficiente para a disciplina/free tier).
7. **Service access:** use os roles `aws-elasticbeanstalk-service-role` e `aws-elasticbeanstalk-ec2-role`
   (no AWS Academy/Learner Lab: `LabRole` e `LabInstanceProfile`).
8. **Database (opcional, recomendado):** habilite o RDS integrado → Engine **mysql**, classe `db.t4g.micro`/`db.t3.micro`,
   usuário e senha. O EB cria automaticamente as variáveis `RDS_*`.
   - Sem RDS (opção usada nesta entrega) o projeto usa SQLite em `/var/app/data/db.sqlite3`, fora da pasta do código:
     os dados sobrevivem a novos deploys, mas se perdem se a instância EC2 for recriada.

### 4.3 Variáveis de ambiente (Environment properties)

Na etapa **Configure updates, monitoring, and logging** → *Environment properties* (ou depois em
**Configuration → Updates, monitoring, and logging → Edit**):

| Nome | Valor |
|---|---|
| `SECRET_KEY` | chave gerada com o comando da seção 3 (**obrigatória**) |
| `DJANGO_SUPERUSER_PASSWORD` | senha do admin (**obrigatória** para criar o superusuário) |
| `DJANGO_DEBUG` | `False` (opcional — já é o padrão) |
| `DJANGO_ALLOWED_HOSTS` | `.elasticbeanstalk.com` (opcional — já é o padrão) |
| `DJANGO_SUPERUSER_USERNAME` | `admin` (opcional — já é o padrão) |
| `DJANGO_SUPERUSER_EMAIL` | `admin@ecommerce.com` (opcional — já é o padrão) |

> ⚠️ Não use o botão *Import from .env file*: o `.env` local tem `DJANGO_DEBUG=True`.

`RDS_DB_NAME`, `RDS_USERNAME`, `RDS_PASSWORD`, `RDS_HOSTNAME` e `RDS_PORT` são preenchidas pelo EB quando o RDS é
criado junto com o ambiente. Se o RDS foi criado separadamente, adicione-as manualmente e libere a porta `3306` no
Security Group do RDS para o Security Group das instâncias do EB.

### 4.4 O que acontece automaticamente no deploy

O arquivo `.ebextensions/01_django.config` configura:

- `DJANGO_SETTINGS_MODULE=ecommerce.settings` e `WSGIPath=ecommerce.wsgi:application`;
- o nginx servindo `/static` a partir da pasta `static/`, com WhiteNoise como reserva (CSS do admin);
- `container_commands`, executados a cada deploy (como root):
  0. cria a pasta `/var/app/data` (banco SQLite, fora do código);
  1. `migrate` — cria as tabelas de `Cliente` e `Pedido`;
  2. `collectstatic` — copia os arquivos estáticos do admin para `static/`;
  3. **`criar_admin` — cria o superusuário (admin/root)** com as variáveis `DJANGO_SUPERUSER_*`.
     É idempotente: em deploys seguintes só atualiza a senha, sem duplicar o usuário;
  4. passa a pasta `/var/app/data` para o usuário `webapp` (quem roda o site).

Os scripts em `.platform/hooks/postdeploy/` e `.platform/confighooks/postdeploy/` rodam **depois** do deploy
(e depois de mudanças de configuração) e garantem de novo a permissão de gravação do `webapp` no banco.

O `Procfile` inicia o `gunicorn` com `ecommerce.wsgi:application` na porta 8000, atrás do nginx do EB.

### 4.5 Criar / trocar a senha do admin depois do deploy

- **Forma recomendada:** altere `DJANGO_SUPERUSER_PASSWORD` em *Environment properties* e clique em *Apply*.
  Depois faça **Upload and deploy** do mesmo `app.zip`: só o deploy da aplicação roda o `criar_admin` (e o `collectstatic`) de novo.
- **Via SSH (alternativa):**
  ```bash
  eb ssh    # ou "Connect" pelo console EC2
  cd /var/app/current
  source /var/app/venv/*/bin/activate
  sudo -E python3 manage.py createsuperuser
  ```

### 4.6 Validação

1. Aguarde o ambiente ficar com **Health: Ok (Green)**.
2. http://ecommerce-as-api-env.eba-jpapde3u.us-east-1.elasticbeanstalk.com/ → `{"status": "ok", ..., "versao": "v4"}`
3. http://ecommerce-as-api-env.eba-jpapde3u.us-east-1.elasticbeanstalk.com/api/clientes/ e http://ecommerce-as-api-env.eba-jpapde3u.us-east-1.elasticbeanstalk.com/api/pedidos/ → `200`
4. http://ecommerce-as-api-env.eba-jpapde3u.us-east-1.elasticbeanstalk.com/admin/ → login com `admin` → cadastrar um cliente com pedidos.
5. Conferir em `/api/clientes/` que o cliente aparece com `"total_pedidos"` e a lista de pedidos.

### 4.7 Problemas comuns

| Sintoma | Causa / solução |
|---|---|
| Health *Severe*, log com `SECRET_KEY não definida` | Faltou `SECRET_KEY` nas Environment properties |
| `400 Bad Request` ao abrir a URL | Domínio fora de `DJANGO_ALLOWED_HOSTS` — use `.elasticbeanstalk.com` |
| Deploy falha em `01_migrate` | RDS inacessível: confira variáveis `RDS_*` e o Security Group (porta 3306) |
| Admin sem CSS | `collectstatic` falhou — veja *Logs → Request logs → Full logs* (`cfn-init-cmd.log`) |
| Login do admin volta para a tela de login | `DJANGO_SECURE_SSL_REDIRECT` ligado sem HTTPS — deixe `False` |
| `manage.py` não encontrado | Zip com pasta pai; gere de novo com `python deploy/gerar_app_zip.py` |
| Páginas abrem, mas login/salvar dá **500** | Banco sem permissão de escrita para o `webapp` — resolvido pelo passo `04_permissoes` e pelos hooks `.platform` |
| Login do admin recusa a senha | `DJANGO_SUPERUSER_PASSWORD` não cadastrada — adicione em *Configuration*, clique em *Apply* **e depois faça *Upload and deploy* do mesmo `app.zip`** |
| CSS some / `/static/...` dá 404 depois de mudar variáveis | O *Apply* de configuração não roda de novo o `collectstatic` nem o `criar_admin` — faça **Upload and deploy** do mesmo `app.zip` |

Logs: **Elastic Beanstalk → Environment → Logs → Request logs → Last 100 lines / Full logs**
(`web.stdout.log` = erros do Django/gunicorn, `cfn-init-cmd.log` = saída do migrate/collectstatic/criar_admin).
Os erros 500 aparecem com o *traceback* completo no `web.stdout.log` (configuração `LOGGING` no `settings.py`).

### 4.8 Histórico do deploy (etapas realizadas)

| Versão | O que aconteceu | Correção |
|---|---|---|
| v1 | Ambiente criado (Health Ok), mas faltou `DJANGO_SUPERUSER_PASSWORD` → admin não foi criado | Variável adicionada em *Configuration → Environment properties* |
| v1 | Admin abria **sem CSS**: o console novo do EB mapeia `/static` para a pasta `static`, e o projeto usava `staticfiles` | `STATIC_ROOT` passou a ser `static/` + **WhiteNoise** como reserva (v2) |
| v2/v3 | Leitura funcionava, mas login e cadastro davam **500**: o `migrate` roda como root e o site roda como `webapp`, que não conseguia gravar no SQLite | Banco movido para `/var/app/data`, `chown` para `webapp` no deploy (v3) e hooks `.platform` pós-deploy (v4) |
| v4 | Tudo funcionando: API, admin, cadastro de clientes e pedidos | — |
| v4 (us-east-1) | No ambiente novo, depois de ajustar a senha com *Apply*, o admin ficou sem CSS (`/static` 404) e sem usuário | Novo *Upload and deploy* do mesmo `app.zip` (v4b) rodou `collectstatic` e `criar_admin` |
| v4b (final) | Ambiente recriado na região **us-east-1 (N. Virginia)**, a mesma do roteiro de aula, com o `app.zip` v4 | Ambiente anterior em us-east-2 (Ohio) encerrado · versão atual (`"versao": "v4"` na raiz) |

---

## 5. Entrega (GitHub)

1. Crie o repositório no GitHub e envie o código:
   ```bash
   git remote add origin https://github.com/AntonioSinhorelli/ecommerce-api.git
   git push -u origin main
   ```
2. **Settings → Collaborators → Add people** → adicione o professor como colaborador.
3. URL da API publicada informada no topo deste README.

## Estrutura do projeto

```
├── .ebextensions/01_django.config   # config do Elastic Beanstalk (migrate, collectstatic, criar_admin, permissões)
├── .platform/                       # hooks pós-deploy (permissão de gravação no banco)
├── deploy/
│   ├── app.zip                      # pacote enviado ao EB
│   └── gerar_app_zip.py             # gera o app.zip
├── ecommerce/                       # projeto Django (settings, urls, wsgi)
├── vendas/                          # app do tema
│   ├── models.py                    # Cliente e Pedido
│   ├── serializers.py
│   ├── views.py                     # ClienteViewSet e PedidoViewSet
│   ├── urls.py
│   ├── admin.py
│   ├── tests.py
│   └── management/commands/criar_admin.py
├── .env.example
├── Procfile
├── requirements.txt
└── manage.py
```
