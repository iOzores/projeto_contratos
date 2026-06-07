# Diagramas Mermaid - Projeto Contratos

Este documento contem os diagramas prontos em Mermaid e o escopo usado para representar o projeto.

## Diagrama de Classe

### Escopo

- Representa as principais classes Python do projeto Flask.
- Representa tambem as tabelas persistidas no PostgreSQL, identificando PK e FK.
- A tabela `contratos_bancarios` guarda os dados principais do contrato.
- A tabela `contratos_bancarios_parcelas` guarda as parcelas simuladas para contratos SAC ou PRICE.
- A FK `contrato_id` aponta para `contratos_bancarios.id` com exclusao em cascata.
- Os services manipulam regras de entrada, consulta, edicao, exclusao e simulacao.
- O arquivo `app.py` atua como camada de rotas/controlador e usa os services.

```mermaid
classDiagram
    direction LR

    class FlaskApp {
        <<controller>>
        +index()
        +incluir_contrato()
        +consultar_contratos()
        +editar_contrato(contrato_id)
        +excluir_contrato(contrato_id)
        +simular_emprestimo()
        +simular_contrato(contrato_id)
        +exportar_contratos()
        -_resumo_parcelas(parcelas)
    }

    class Contrato {
        <<dataclass>>
        +int id
        +str numero
        +str cliente
        +str cliente_cpf
        +float valor
        +int prazo_meses
        +float taxa_juros
        +str data_nascimento
        +str data
        +str sistema_amortizacao
    }

    class ContratoDB {
        <<repository>>
        +str table_name
        +str parcelas_table_name
        +dict connection_info
        +read_all() List~Contrato~
        +get_by_id(contrato_id) Contrato
        +search(q, by) List~Contrato~
        +insert(contrato) int
        +update(contrato_id, fields) bool
        +delete(contrato_id) bool
        +replace_parcelas(contrato_id, sistema, parcelas)
        +exists_numero(numero) bool
        +generate_unique_numero() str
        -_create_table()
        -_create_parcelas_table()
        -_ensure_columns()
        -_to_contrato(row) Contrato
        -_valid_numero(numero) bool
    }

    class IncluirContratoService {
        <<service>>
        +ContratoDB db
        +gerar_numero_preview() str
        +validar_entrada(cliente, cpf, valor, data, taxa_juros, data_nascimento, prazo_meses, sistema_amortizacao)
        +salvar(payload, numero_form)
    }

    class ConsultarContratoService {
        <<service>>
        +ContratoDB db
        +consultar(q, by)
    }

    class EditarContratoService {
        <<service>>
        +ContratoDB db
        +preparar_updates(numero, cliente, cpf, valor, data, taxa_juros, data_nascimento, prazo_meses)
        +editar(contrato_id, updates)
    }

    class ExcluirContratoService {
        <<service>>
        +ContratoDB db
        +excluir(contrato_id)
    }

    class SimuladorService {
        <<service>>
        +simular_sac(valor_total, taxa_juros_percentual, meses) list
        +simular_price(valor_total, taxa_juros_percentual, meses) list
    }

    class DuplicateNumeroError {
        <<exception>>
    }

    class ContratosBancarios {
        <<table>>
        +int id PK
        +text numero UK
        +text cliente
        +text cliente_cpf
        +double valor
        +int prazo_meses
        +date data
        +double taxa_juros
        +date data_nascimento
        +text sistema_amortizacao
    }

    class ContratosBancariosParcelas {
        <<table>>
        +int id PK
        +int contrato_id FK
        +text sistema_amortizacao
        +int mes
        +double prestacao
        +double amortizacao
        +double juros
        +double saldo_devedor
        +unique contrato_id_sistema_mes
    }

    FlaskApp --> IncluirContratoService : usa
    FlaskApp --> ConsultarContratoService : usa
    FlaskApp --> EditarContratoService : usa
    FlaskApp --> ExcluirContratoService : usa
    FlaskApp --> SimuladorService : usa
    FlaskApp --> ContratoDB : usa

    IncluirContratoService --> ContratoDB : persiste
    ConsultarContratoService --> ContratoDB : consulta
    EditarContratoService --> ContratoDB : atualiza
    ExcluirContratoService --> ContratoDB : remove
    IncluirContratoService --> Contrato : cria
    ContratoDB --> Contrato : retorna/mapeia
    ContratoDB --> DuplicateNumeroError : lanca

    ContratoDB ..> ContratosBancarios : CRUD
    ContratoDB ..> ContratosBancariosParcelas : CRUD parcelas
    ContratosBancarios "1" --> "0..*" ContratosBancariosParcelas : contrato_id FK
```

## Diagrama de Caso de Uso

### Escopo

- Representa a interacao de um usuario com o sistema web OzzBank.
- O ator principal e o usuario/operador do sistema.
- O sistema permite consultar, incluir, editar, excluir, simular e exportar contratos.
- A simulacao calcula SAC e PRICE; a contratacao a partir da simulacao reaproveita valor, taxa, prazo e sistema escolhido.
- A exportacao gera CSV a partir da consulta atual.
- O banco PostgreSQL aparece como sistema externo usado para persistencia.

```mermaid
flowchart LR
    Usuario["Usuario / Operador"]
    Banco[("PostgreSQL")]

    subgraph Sistema["Sistema OzzBank - Contratos Bancarios"]
        UC01(["Acessar pagina inicial"])
        UC02(["Consultar contratos"])
        UC03(["Buscar por nome, CPF ou numero"])
        UC04(["Incluir contrato"])
        UC05(["Gerar numero de contrato"])
        UC06(["Validar dados do contrato"])
        UC07(["Editar contrato"])
        UC08(["Excluir contrato"])
        UC09(["Simular emprestimo"])
        UC10(["Calcular parcelas SAC"])
        UC11(["Calcular parcelas PRICE"])
        UC12(["Contratar a partir da simulacao"])
        UC13(["Salvar parcelas do contrato"])
        UC14(["Exportar contratos em CSV"])
    end

    Usuario --> UC01
    Usuario --> UC02
    Usuario --> UC04
    Usuario --> UC07
    Usuario --> UC08
    Usuario --> UC09
    Usuario --> UC14

    UC02 -. inclui .-> UC03
    UC04 -. inclui .-> UC05
    UC04 -. inclui .-> UC06
    UC09 -. inclui .-> UC10
    UC09 -. inclui .-> UC11
    UC12 -. estende .-> UC09
    UC12 -. inclui .-> UC04
    UC12 -. inclui .-> UC13
    UC14 -. usa filtro de .-> UC02

    UC02 --> Banco
    UC04 --> Banco
    UC07 --> Banco
    UC08 --> Banco
    UC13 --> Banco
    UC14 --> Banco
```

## Como Usar no Mermaid

1. Copie o bloco desejado, incluindo a linha inicial `classDiagram` ou `flowchart LR`.
2. Cole no Mermaid Live Editor, em um arquivo Markdown com suporte a Mermaid, ou em extensoes como Mermaid Preview no VS Code.
3. Para exportar, use a opcao de SVG/PNG/PDF da ferramenta Mermaid escolhida.

