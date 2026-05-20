# README — Alembic, PostgreSQL e Migração de Dados

## Objetivo

Resumo prático sobre:

* Alembic migrations
* Upgrade/Downgrade
* Migração de dados entre tabelas
* PostgreSQL uppercase/lowercase
* INSERT INTO ... SELECT
* UPDATE ... FROM
* server_default
* ARRAY(String)
* Problemas comuns do autogenerate

---

# Estrutura básica do Alembic

Criar migration:

```bash
alembic revision -m "descricao"
```

Aplicar migrations:

```bash
alembic upgrade head
```

Voltar uma migration:

```bash
alembic downgrade -1
```

Voltar tudo:

```bash
alembic downgrade base
```

---

# Como o Alembic funciona

Cada migration possui:

```python
revision = "002"
down_revision = "001"
```

O Alembic aplica automaticamente em ordem.

Exemplo:

```text
001_create_tables.py
002_migrate_data.py
003_drop_old_columns.py
```

Executando:

```bash
alembic upgrade head
```

O Alembic faz:

```text
001 -> 002
002 -> 003
```

---

# upgrade() e downgrade()

## upgrade()

Aplica alterações no banco.

Exemplo:

```python
def upgrade():
    op.add_column(
        "tbcliente",
        sa.Column("CLITOKEN", sa.String())
    )
```

---

## downgrade()

Desfaz alterações.

Exemplo:

```python
def downgrade():
    op.drop_column("tbcliente", "CLITOKEN")
```

---

# Fluxo recomendado para produção

## Migration 1 — Estrutura

Criar novas tabelas:

* tbmeta
* tbconfiguracao
* tbtelefone

Sem remover colunas antigas.

---

## Migration 2 — Migração de dados

Copiar dados das tabelas antigas.

---

## Migration 3 — Cleanup

Remover colunas antigas.

---

# PostgreSQL Uppercase vs Lowercase

No PostgreSQL:

| SQL escrito | Nome real salvo |
| ----------- | --------------- |
| CLIID       | cliid           |
| "CLIID"     | CLIID           |

Sem aspas:

```sql
CREATE TABLE teste (
    CLIID INTEGER
)
```

vira:

```text
cliid
```

Com aspas:

```sql
CREATE TABLE teste (
    "CLIID" INTEGER
)
```

mantém uppercase.

---

# quote=True no Alembic/SQLAlchemy

Para forçar uppercase real:

```python
sa.Column(
    "CLIID",
    sa.Integer(),
    quote=True
)
```

Exemplo:

```python
op.create_table(
    "tbmeta",
    sa.Column(
        "CLIID",
        sa.Integer(),
        primary_key=True,
        quote=True
    ),
    schema="contas"
)
```

---

# relationship() não cria coluna

Exemplo:

```python
cliente = relationship("Cliente")
```

Isso NÃO cria coluna no banco.

Migration só trabalha com:

```python
Column()
ForeignKey()
```

---

# UPDATE não cria registros

Este comando:

```sql
UPDATE contas.tbmeta m
SET "METTOKENUSUARIO" = c."CLITOKEN"
FROM contas.tbcliente c
WHERE m."METCLIID" = c."CLIID"
```

Só atualiza registros já existentes.

Se a tabela estiver vazia:

```text
0 rows updated
```

---

# INSERT INTO ... SELECT

Forma correta para migrar dados:

```python
op.execute("""
    INSERT INTO contas.tbmeta (
        "METCLIID",
        "METTOKENUSUARIO"
    )
    SELECT
        c."CLIID",
        c."CLITOKEN"
    FROM contas.tbcliente c
""")
```

---

# Exemplos de migração

## CLITOKEN -> tbmeta

```python
op.execute("""
    INSERT INTO contas.tbmeta (
        "METCLIID",
        "METTOKENUSUARIO"
    )
    SELECT
        c."CLIID",
        c."CLITOKEN"
    FROM contas.tbcliente c
""")
```

---

## CLIWABAID -> tbmeta

```python
op.execute("""
    INSERT INTO contas.tbmeta (
        "METCLIID",
        "METWABAID"
    )
    SELECT
        c."CLIID",
        c."CLIWABAID"
    FROM contas.tbcliente c
""")
```

---

## CLIIFRAMETOKEN -> tbconfiguracao

```python
op.execute("""
    INSERT INTO contas.tbconfiguracao (
        "CONIDCLIENTE",
        "CONTOKENIFRAME"
    )
    SELECT
        c."CLIID",
        c."CLIIFRAMETOKEN"
    FROM contas.tbcliente c
""")
```

---

## CLIINUMWHATSAPP -> tbtelefone

```python
op.execute("""
    INSERT INTO contas.tbtelefone (
        "TELIDCLIENTE",
        "TELDISPLAYNUMBER"
    )
    SELECT
        c."CLIID",
        c."CLIINUMWHATSAPP"
    FROM contas.tbcliente c
""")
```

---

# Remover colunas antigas

Depois da validação:

```python
op.drop_column(
    "tbcliente",
    "CLITOKEN",
    schema="contas"
)
```

---

# Problema comum do autogenerate

Alembic pode gerar:

```python
op.alter_column(
    "tbtelefone",
    "TELID",
    nullable=True
)
```

Isso vira:

```sql
ALTER COLUMN "TELID" DROP NOT NULL
```

Mas PRIMARY KEY é sempre NOT NULL.

Então deve remover manualmente da migration.

---

# server_default

## Default no banco

```python
server_default=sa.text("false")
```

Gera:

```sql
DEFAULT false
```

---

## Diferença

### default=

Default do SQLAlchemy/Python.

### server_default=

Default real do PostgreSQL.

---

# Boolean default

Correto:

```python
server_default=sa.text("false")
```

ou:

```python
server_default=sa.false()
```

---

# ARRAY(String)

Modelo:

```python
origens: Mapped[list[str] | None] = mapped_column(
    "CONORIGENS",
    MutableList.as_mutable(ARRAY(String(255))),
    comment="Origem do cliente"
)
```

---

# Default para ARRAY

Correto:

```python
default=lambda: ["*"]
```

Não usar:

```python
default=["*"]
```

---

# server_default para ARRAY

```python
server_default=sa.text("ARRAY['*']")
```

---

# Inserindo ARRAY na migration

```python
op.execute("""
    INSERT INTO contas.tbconfiguracao (
        "CONIDCLIENTE",
        "CONORIGENS"
    )
    SELECT
        c."CLIID",
        ARRAY['*']
    FROM contas.tbcliente c
""")
```

PostgreSQL salva como:

```text
{"*"}
```

---

# Erro NOT NULL

Erro:

```text
null value violates not-null constraint
```

Significa:

* coluna é NOT NULL
* insert não enviou valor
* coluna não possui DEFAULT

Soluções:

* enviar valor
* criar server_default
* permitir nullable=True

---

# Comandos úteis PostgreSQL

Ver estrutura da tabela:

```sql
\d contas.tbmeta
```

Ver colunas:

```sql
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'contas'
AND table_name = 'tbmeta';
```

---

# Regra mental importante

| Conceito               | O que faz                   |
| ---------------------- | --------------------------- |
| relationship()         | ORM apenas                  |
| Column()               | cria coluna real            |
| ForeignKey()           | cria FK real                |
| UPDATE                 | altera registros existentes |
| INSERT INTO ... SELECT | cria registros novos        |
| default=               | Python/ORM                  |
| server_default=        | PostgreSQL                  |
