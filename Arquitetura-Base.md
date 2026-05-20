# Arquitetura FastAPI + SQLAlchemy + Repository + Service

## Objetivo

Separar corretamente:

* HTTP
* regras de negócio
* acesso ao banco
* models ORM
* validação de entrada/saída

Isso melhora:

* manutenção
* escalabilidade
* testes
* organização
* segurança

---

# Estrutura recomendada

```text
app/
├── models/
│   └── user.py
├── repositories/
│   └── user_repository.py
├── services/
│   └── user_service.py
├── routes/
│   └── user_router.py
├── schemas/
│   └── user/
│       ├── create_user.py
│       ├── update_user.py
│       └── response_user.py
└── config/
    └── db.py
```

---

# Fluxo da aplicação

```text
Client HTTP
    ↓
Router
    ↓
DTO / Schema
    ↓
Service
    ↓
Repository
    ↓
Model SQLAlchemy
    ↓
Banco de Dados
```

---

# Responsabilidade de cada camada

| Camada     | Responsabilidade             |
| ---------- | ---------------------------- |
| Router     | HTTP, request, response      |
| DTO/Schema | validação e serialização     |
| Service    | regra de negócio e transação |
| Repository | queries e persistência       |
| Model      | estrutura ORM/tabela         |

---

# SQLAlchemy 2.x Tipado

## Antes

```python
id = Column(
    Integer,
    primary_key=True
)
```

## Recomendado

```python
from sqlalchemy.orm import Mapped, mapped_column

id: Mapped[int] = mapped_column(
    primary_key=True
)
```

---

# Tipagem correta

| SQLAlchemy     | Tipagem            |
| -------------- | ------------------ |
| nullable=False | Mapped[str]        |
| nullable=True  | Mapped[str | None] |
| unique=True    | não altera tipagem |

---

# Exemplos de campos

```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, Boolean
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import ARRAY

nome: Mapped[str] = mapped_column(
    String(255),
    nullable=False,
    unique=True
)

razao_social: Mapped[str] = mapped_column(
    Text,
    nullable=False
)

ativo: Mapped[bool] = mapped_column(
    Boolean,
    default=True,
    nullable=False
)

origens: Mapped[list[str] | None] = mapped_column(
    MutableList.as_mutable(
        ARRAY(String(255))
    ),
    nullable=True
)
```

---

# Model

## models/user.py

```python
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from sqlalchemy import (
    String,
    ForeignKey,
    Boolean
)

from app.config.db import Base


class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        nullable=False
    )

    nome: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    senha: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
```

---

# DTO / Schema

## schemas/user/create_user.py

```python
from pydantic import BaseModel, EmailStr


class CreateUserDTO(BaseModel):

    nome: str
    email: EmailStr
    senha: str
```

---

## schemas/user/update_user.py

```python
from pydantic import BaseModel, EmailStr


class UpdateUserDTO(BaseModel):

    nome: str | None = None
    email: EmailStr | None = None
```

---

## schemas/user/response_user.py

```python
from pydantic import BaseModel, EmailStr


class UserResponseDTO(BaseModel):

    id: int
    nome: str
    email: EmailStr

    model_config = {
        "from_attributes": True
    }
```

---

# Repository

## Responsabilidade

O repository:

* faz queries
* adiciona entidades
* remove entidades
* atualiza entidades
* NÃO deve conter regra de negócio
* NÃO deve conhecer autenticação
* NÃO deve conhecer HTTP

---

## repositories/user_repository.py

```python
from sqlalchemy.orm import Session

from app.models.user import User

from app.schemas.user.create_user import (
    CreateUserDTO
)

from app.schemas.user.update_user import (
    UpdateUserDTO
)


class UserRepository:

    @staticmethod
    def create(
        db: Session,
        dto: CreateUserDTO
    ) -> User:

        db_user = User(
            nome=dto.nome,
            email=dto.email,
            senha=dto.senha
        )

        db.add(db_user)

        return db_user

    @staticmethod
    def get_by_id(
        db: Session,
        user_id: int
    ) -> User | None:

        return (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    @staticmethod
    def get_by_email(
        db: Session,
        email: str
    ) -> User | None:

        return (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

    @staticmethod
    def get_all_by_client(
        db: Session,
        client_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[User]:

        return (
            db.query(User)
            .filter(User.client_id == client_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update(
        db: Session,
        db_user: User,
        dto: UpdateUserDTO
    ) -> User:

        update_data = dto.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():

            setattr(
                db_user,
                field,
                value
            )

        db.add(db_user)

        return db_user

    @staticmethod
    def delete(
        db: Session,
        db_user: User
    ) -> None:

        db.delete(db_user)
```

---

# Service

## Responsabilidade

O service:

* controla transação
* faz commit
* faz rollback
* executa regra de negócio
* controla autorização
* orquestra múltiplos repositories

---

## services/user_service.py

```python
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.user_repository import (
    UserRepository
)

from app.schemas.user.create_user import (
    CreateUserDTO
)

from app.schemas.user.update_user import (
    UpdateUserDTO
)

from app.models.user import User


class UserService:

    @staticmethod
    def create(
        db: Session,
        dto: CreateUserDTO
    ) -> User:

        try:

            user = UserRepository.create(
                db,
                dto
            )

            db.commit()

            db.refresh(user)

            return user

        except SQLAlchemyError:

            db.rollback()

            raise

    @staticmethod
    def update(
        db: Session,
        user_id: int,
        dto: UpdateUserDTO
    ) -> User:

        try:

            user = UserRepository.get_by_id(
                db,
                user_id
            )

            if not user:
                raise ValueError(
                    "Usuário não encontrado"
                )

            user = UserRepository.update(
                db,
                user,
                dto
            )

            db.commit()

            db.refresh(user)

            return user

        except SQLAlchemyError:

            db.rollback()

            raise

    @staticmethod
    def delete(
        db: Session,
        authenticated_user: User,
        target_user_id: int
    ) -> None:

        try:

            target_user = UserRepository.get_by_id(
                db,
                target_user_id
            )

            if not target_user:
                raise ValueError(
                    "Usuário não encontrado"
                )

            if not authenticated_user.is_admin:

                if (
                    target_user.client_id
                    != authenticated_user.client_id
                ):

                    raise PermissionError(
                        "Sem permissão"
                    )

            UserRepository.delete(
                db,
                target_user
            )

            db.commit()

        except SQLAlchemyError:

            db.rollback()

            raise
```

---

# Router

## Responsabilidade

O router:

* recebe request HTTP
* chama service
* retorna response
* usa DTOs
* NÃO deve conter regra de negócio

---

## routes/user_router.py

```python
from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.config.db import get_db

from app.schemas.user.create_user import (
    CreateUserDTO
)

from app.schemas.user.response_user import (
    UserResponseDTO
)

from app.services.user_service import (
    UserService
)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post(
    "/",
    response_model=UserResponseDTO,
    status_code=201
)
def create_user(
    dto: CreateUserDTO,
    db: Session = Depends(get_db)
):

    try:

        user = UserService.create(
            db,
            dto
        )

        return user

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
```

---

# Transações complexas

Quando múltiplas entidades precisam ser criadas juntas:

* cliente
* usuário
* permissões
* configurações

O commit deve ficar no service.

---

## Exemplo

```python
try:

    client = ClientRepository.create(
        db,
        client_dto
    )

    db.flush()

    user = UserRepository.create(
        db,
        user_dto
    )

    db.flush()

    PermissionRepository.create(
        db,
        user.id
    )

    db.commit()

except SQLAlchemyError:

    db.rollback()

    raise
```

---

# flush() vs commit()

| Método   | Função                                    |
| -------- | ----------------------------------------- |
| flush()  | envia ao banco sem salvar definitivamente |
| commit() | salva definitivamente                     |

---

# Paginação

```python
skip: int = 0
limit: int = 100
```

Equivalente SQL:

```sql
LIMIT 100 OFFSET 0
```

---

# delete()

## ORM delete

```python
db.delete(user)
```

A remoção real ocorre apenas no:

```python
db.commit()
```

---

# Regras importantes

## Repository NÃO deve saber

* JWT
* usuário autenticado
* admin
* RBAC
* HTTP
* FastAPI

---

## Service deve controlar

* autorização
* transação
* rollback
* regras de negócio

---

# Regra prática

## CRUD simples

Repository pode até controlar commit.

---

## Sistema maior / multi-entidade

Service deve controlar:

* commit
* rollback
* flush
* transação inteira

---

# Conclusão

Essa arquitetura:

* separa responsabilidades
* evita models gordos
* melhora manutenção
* facilita testes
* evita commit parcial
* melhora organização do projeto
* escala muito melhor em APIs grandes
