from dataclasses import dataclass
import sqlite3
from typing import List, Optional, Dict, Any


@dataclass
class Contrato:
    id: Optional[int]
    numero: str
    cliente: str
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

    def read_all(self) -> List[Contrato]:
        cur = self.conn.execute("SELECT id, numero, cliente, valor, data FROM contratos ORDER BY id DESC")
        rows = cur.fetchall()
        return [Contrato(id=row["id"], numero=row["numero"], cliente=row["cliente"], valor=row["valor"], data=row["data"]) for row in rows]

    def insert(self, contrato: Contrato) -> int:
        if not self._valid_numero(contrato.numero):
            raise ValueError("Número do contrato inválido. Deve ter 5+ dígitos mais 2 dígitos finais, ex: 12345-67 ou 1234567")
        cur = self.conn.execute(
            "INSERT INTO contratos (numero, cliente, valor, data) VALUES (?, ?, ?, ?)",
            (contrato.numero, contrato.cliente, contrato.valor, contrato.data),
        )
        self.conn.commit()
        return cur.lastrowid

    def update(self, contrato_id: int, **fields: Any) -> bool:
        if not fields:
            return False
        allowed = {"numero", "cliente", "valor", "data"}
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
