from dataclasses import dataclass
import sqlite3
from typing import List, Optional, Dict, Any


@dataclass
class Contrato:
    id: Optional[int]
    numero: str
    cliente: str
    cliente_cpf: str
    valor: float
    data: str


class ContratoDB:
    """Classe simples para manipular um banco SQLite de contratos.

    Métodos:
    - read_all(): retorna lista de `Contrato`
    - insert(contrato): insere e retorna id
    - update(contrato_id, **fields): atualiza campos e retorna True/False
    - delete(contrato_id): remove e retorna True/False
    """

    def __init__(self, db_path: str = "contratos.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self) -> None:
        # Regras para `numero`:
        # - Aceita dígitos contínuos com ao menos 7 dígitos (5+2)
        # - Ou aceita até um hífen separando o sufixo de 2 dígitos: ex. 12345-67
        sql = """
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            cliente TEXT NOT NULL,
            cliente_cpf TEXT NOT NULL,
            valor REAL NOT NULL,
            data TEXT NOT NULL,
            CHECK (
                numero GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9]*'
                OR numero GLOB '[0-9][0-9][0-9][0-9][0-9]*-[0-9][0-9]'
            )
        );
        """
        self.conn.execute(sql)
        self.conn.commit()
        # Migração: se a tabela já existia sem a coluna `cliente_cpf`, adicioná-la.
        cur = self.conn.execute("PRAGMA table_info('contratos')")
        cols = [r[1] for r in cur.fetchall()]
        if 'cliente_cpf' not in cols:
            # Add column with default empty string so existing rows are válidos
            try:
                self.conn.execute("ALTER TABLE contratos ADD COLUMN cliente_cpf TEXT NOT NULL DEFAULT ''")
                self.conn.commit()
            except sqlite3.OperationalError:
                # Em casos raros de restrição, adicionar coluna sem NOT NULL
                try:
                    self.conn.execute("ALTER TABLE contratos ADD COLUMN cliente_cpf TEXT DEFAULT ''")
                    self.conn.commit()
                except Exception:
                    pass
        # Garantir unicidade do número do contrato
        try:
            self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_contratos_numero_unique ON contratos(numero)")
            self.conn.commit()
        except Exception:
            pass

    def read_all(self) -> List[Contrato]:
        cur = self.conn.execute("SELECT id, numero, cliente, cliente_cpf, valor, data FROM contratos ORDER BY id DESC")
        rows = cur.fetchall()
        return [Contrato(id=row["id"], numero=row["numero"], cliente=row["cliente"], cliente_cpf=row["cliente_cpf"], valor=row["valor"], data=row["data"]) for row in rows]

    def exists_numero(self, numero: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM contratos WHERE numero = ? LIMIT 1", (numero,))
        return cur.fetchone() is not None

    def generate_unique_numero(self, attempts: int = 1000) -> str:
        """Gera um número no formato xxxxx-xx único na tabela de contratos.

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
        """Busca contratos pela query `q`.

        by: 'auto'|'nome'|'cpf'|'numero'
        """
        if not q:
            return []
        import re

        q_clean = q.strip()
        digits = re.sub(r"\D", "", q_clean)

        where_clauses = []
        params: List[str] = []

        if by == 'cpf':
            if digits == '':
                return []
            where_clauses.append("cliente_cpf LIKE ?")
            params.append(f"%{digits}%")
        elif by == 'numero':
            where_clauses.append("numero LIKE ?")
            params.append(f"%{q_clean}%")
        elif by == 'nome':
            where_clauses.append("cliente LIKE ?")
            params.append(f"%{q_clean}%")
        else:
            # auto: try to match cpf / numero / nome
            where_clauses.append("cliente LIKE ?")
            params.append(f"%{q_clean}%")
            where_clauses.append("numero LIKE ?")
            params.append(f"%{q_clean}%")
            if digits:
                where_clauses.append("cliente_cpf LIKE ?")
                params.append(f"%{digits}%")

        where_sql = " OR ".join(where_clauses)
        sql = f"SELECT id, numero, cliente, cliente_cpf, valor, data FROM contratos WHERE {where_sql} ORDER BY id DESC"
        cur = self.conn.execute(sql, params)
        rows = cur.fetchall()
        return [Contrato(id=row["id"], numero=row["numero"], cliente=row["cliente"], cliente_cpf=row["cliente_cpf"], valor=row["valor"], data=row["data"]) for row in rows]

    def insert(self, contrato: Contrato) -> int:
        if not self._valid_numero(contrato.numero):
            raise ValueError("Número do contrato inválido. Deve ter 5+ dígitos mais 2 dígitos finais, ex: 12345-67 ou 1234567")
        cur = self.conn.execute(
            "INSERT INTO contratos (numero, cliente, cliente_cpf, valor, data) VALUES (?, ?, ?, ?, ?)",
            (contrato.numero, contrato.cliente, contrato.cliente_cpf, contrato.valor, contrato.data),
        )
        self.conn.commit()
        return cur.lastrowid

    def update(self, contrato_id: int, **fields: Any) -> bool:
        if not fields:
            return False
        allowed = {"numero", "cliente", "cliente_cpf", "valor", "data"}
        updates: Dict[str, Any] = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False
        if "numero" in updates and not self._valid_numero(updates["numero"]):
            raise ValueError("Número do contrato inválido. Deve ter 5+ dígitos mais 2 dígitos finais, ex: 12345-67 ou 1234567")
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        params = list(updates.values()) + [contrato_id]
        sql = f"UPDATE contratos SET {set_clause} WHERE id = ?"
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur.rowcount > 0

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
        cur = self.conn.execute("DELETE FROM contratos WHERE id = ?", (contrato_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
