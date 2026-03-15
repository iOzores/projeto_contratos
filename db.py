import os
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, unquote

from pg8000 import dbapi as pg


@dataclass
class Contrato:
    id: Optional[int]
    numero: str
    cliente: str
    cliente_cpf: str
    valor: float
    data: str


class DuplicateNumeroError(ValueError):
    """Erro para número de contrato duplicado."""


class ContratoDB:
    """Classe simples para manipular contratos no PostgreSQL.

    Por padrão, opera na tabela `contratos_bancarios`.

    Métodos:
    - read_all(): retorna lista de `Contrato`
    - insert(contrato): insere e retorna id
    - update(contrato_id, **fields): atualiza campos e retorna True/False
    - delete(contrato_id): remove e retorna True/False
    """

    def __init__(self, db_path: Optional[str] = None, table_name: str = "contratos_bancarios"):
        # `db_path` é mantido por compatibilidade e pode receber uma URL PostgreSQL.
        if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", table_name):
            raise ValueError("Nome de tabela inválido")
        self.table_name = table_name
        self.connection_info = self._build_connection_info(db_path)
        self.conn = pg.connect(**self.connection_info)
        self._create_table()

    @staticmethod
    def _parse_url(url: str) -> Dict[str, Any]:
        parsed = urlparse(url)
        if parsed.scheme not in {"postgres", "postgresql"}:
            raise ValueError("DATABASE_URL inválida")
        return {
            "host": parsed.hostname or "localhost",
            "port": int(parsed.port or 5432),
            "database": (parsed.path or "/projeto_contratos").lstrip("/"),
            "user": unquote(parsed.username or "postgres"),
            "password": unquote(parsed.password or "postgres"),
        }

    def _build_connection_info(self, db_path: Optional[str]) -> Dict[str, Any]:
        if db_path and db_path.startswith(("postgres://", "postgresql://")):
            return self._parse_url(db_path)

        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return self._parse_url(database_url)

        host = os.getenv("PGHOST", "localhost")
        port = os.getenv("PGPORT", "5432")
        dbname = os.getenv("PGDATABASE", "projeto_contratos")
        user = os.getenv("PGUSER", "postgres")
        password = os.getenv("PGPASSWORD", "postgres")
        return {
            "host": host,
            "port": int(port),
            "database": dbname,
            "user": user,
            "password": password,
        }

    def _create_table(self) -> None:
        cur = self.conn.cursor()
        try:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    numero TEXT NOT NULL UNIQUE,
                    cliente TEXT NOT NULL,
                    cliente_cpf TEXT NOT NULL,
                    valor DOUBLE PRECISION NOT NULL,
                    data DATE NOT NULL,
                    CHECK (numero ~ '^(\\d{{7,}}|\\d{{5,}}-\\d{{2}})$')
                );
                """
            )
        finally:
            cur.close()
        self.conn.commit()

    @staticmethod
    def _to_contrato(row: Dict[str, Any]) -> Contrato:
        row_id = row.get("id")
        return Contrato(
            id=int(row_id) if row_id is not None else None,
            numero=str(row.get("numero", "")),
            cliente=str(row.get("cliente", "")),
            cliente_cpf=str(row.get("cliente_cpf", "")),
            valor=float(row.get("valor", 0.0)),
            data=str(row.get("data", "")),
        )

    def read_all(self) -> List[Contrato]:
        cur = self.conn.cursor()
        try:
            cur.execute(
                f"""
                SELECT id, numero, cliente, cliente_cpf, valor, TO_CHAR(data, 'YYYY-MM-DD') AS data
                FROM {self.table_name}
                ORDER BY id DESC
                """
            )
            rows = cur.fetchall()
        finally:
            cur.close()
        return [
            self._to_contrato(
                {
                    "id": row[0],
                    "numero": row[1],
                    "cliente": row[2],
                    "cliente_cpf": row[3],
                    "valor": row[4],
                    "data": row[5],
                }
            )
            for row in rows
        ]

    def exists_numero(self, numero: str) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                f"SELECT 1 FROM {self.table_name} WHERE numero = %s LIMIT 1",
                (numero,),
            )
            return cur.fetchone() is not None
        finally:
            cur.close()

    def generate_unique_numero(self, attempts: int = 1000) -> str:
        """Gera um número no formato xxxxx-xx único na tabela ativa.

        Tenta `attempts` vezes antes de falhar.
        """
        import random

        for _ in range(attempts):
            part1 = random.randint(10000, 99999)
            part2 = random.randint(10, 99)
            numero = f"{part1}-{part2}"
            if not self.exists_numero(numero) and self._valid_numero(numero):
                return numero
        raise RuntimeError("Não foi possível gerar um número de contrato único")

    def search(self, q: str, by: str = 'auto') -> List[Contrato]:
        """Busca contratos bancários pela query `q`.

        by: 'auto'|'nome'|'cpf'|'numero'
        """
        if not q:
            return []
        import re

        q_clean = q.strip()
        digits = re.sub(r"\D", "", q_clean)

        if by == 'cpf':
            if digits == '':
                return []
            where_clause = "cliente_cpf LIKE %s"
            params = (f"%{digits}%",)
        elif by == 'numero':
            where_clause = "numero ILIKE %s"
            params = (f"%{q_clean}%",)
        elif by == 'nome':
            where_clause = "cliente ILIKE %s"
            params = (f"%{q_clean}%",)
        else:
            where_parts = ["cliente ILIKE %s", "numero ILIKE %s"]
            params_list: List[str] = [f"%{q_clean}%", f"%{q_clean}%"]
            if digits:
                where_parts.append("cliente_cpf LIKE %s")
                params_list.append(f"%{digits}%")
            where_clause = " OR ".join(where_parts)
            params = tuple(params_list)

        cur = self.conn.cursor()
        try:
            final_query = (
                f"""
                    SELECT id, numero, cliente, cliente_cpf, valor, TO_CHAR(data, 'YYYY-MM-DD') AS data
                    FROM {self.table_name}
                    WHERE {where_clause}
                    ORDER BY id DESC
                """
            )
            cur.execute(final_query, params)
            rows = cur.fetchall()
        finally:
            cur.close()
        return [
            self._to_contrato(
                {
                    "id": row[0],
                    "numero": row[1],
                    "cliente": row[2],
                    "cliente_cpf": row[3],
                    "valor": row[4],
                    "data": row[5],
                }
            )
            for row in rows
        ]

    def insert(self, contrato: Contrato) -> int:
        if not self._valid_numero(contrato.numero):
            raise ValueError("Número do contrato inválido. Deve ter 5+ dígitos mais 2 dígitos finais, ex: 12345-67 ou 1234567")
        cur = self.conn.cursor()
        try:
            cur.execute(
                f"""
                INSERT INTO {self.table_name} (numero, cliente, cliente_cpf, valor, data)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    contrato.numero,
                    contrato.cliente,
                    contrato.cliente_cpf,
                    float(contrato.valor),
                    contrato.data,
                ),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("Falha ao inserir contrato: id não retornado")
            contrato_id = row[0]
            self.conn.commit()
            return int(contrato_id)
        except pg.IntegrityError as e:
            self.conn.rollback()
            msg = str(e).lower()
            if "duplicate key" not in msg and "unique" not in msg:
                raise
            raise DuplicateNumeroError("Número de contrato já existe")
        finally:
            cur.close()

    def update(self, contrato_id: int, **fields: Any) -> bool:
        if not fields:
            return False
        allowed = {"numero", "cliente", "cliente_cpf", "valor", "data"}
        updates: Dict[str, Any] = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False
        if "numero" in updates and not self._valid_numero(updates["numero"]):
            raise ValueError("Número do contrato inválido. Deve ter 5+ dígitos mais 2 dígitos finais, ex: 12345-67 ou 1234567")
        set_clause = ", ".join([f"{col} = %s" for col in updates.keys()])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = %s"
        params = list(updates.values()) + [contrato_id]

        cur = self.conn.cursor()
        try:
            cur.execute(query, params)
            updated = cur.rowcount > 0
            self.conn.commit()
            return updated
        except pg.IntegrityError as e:
            self.conn.rollback()
            msg = str(e).lower()
            if "duplicate key" not in msg and "unique" not in msg:
                raise
            raise DuplicateNumeroError("Número de contrato já existe")
        finally:
            cur.close()

    def _valid_numero(self, numero: str) -> bool:
        if not isinstance(numero, str) or numero == "":
            return False
        # caso contínuo: pelo menos 7 dígitos
        import re

        if re.fullmatch(r"\d{7,}", numero):
            return True
        # caso com hífen antes dos 2 dígitos finais: >=5 dígitos + '-' + 2 dígitos
        if re.fullmatch(r"\d{5,}-\d{2}", numero):
            return True
        return False

    def delete(self, contrato_id: int) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                f"DELETE FROM {self.table_name} WHERE id = %s",
                (contrato_id,),
            )
            deleted = cur.rowcount > 0
        finally:
            cur.close()
        self.conn.commit()
        return deleted

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
