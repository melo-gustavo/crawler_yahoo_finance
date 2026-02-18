# Yahoo Finance Crawler

API em FastAPI para coletar empresas do Yahoo Finance Screener por região e exportar os dados em CSV.

## Objetivo

Automatizar a navegação no screener de equities do Yahoo Finance para:

- aplicar filtro de `region`
- configurar `Rows per page = 100`
- paginar resultados
- exportar `symbol`, `name`, `price` em CSV

## Stack

- Python 3.12+
- FastAPI
- Selenium
- BeautifulSoup

## Setup

### 1) Criar ambiente virtual

Windows:

Criar o ambiente virtual

```bash
python -m venv .venv
```

Entrar no ambiente virtual

```bash
.venv\Scripts\Activate.ps1
```

Linux/macOS:

Criar o ambiente virtual

```bash
python3 -m venv .venv
```

Entrar no ambiente virtual

```bash
source .venv/bin/activate
```

### 2) Instalar dependências

```bash
pip install -r requirements.txt
```

### 3) Rodar API

```bash
fastapi dev main.py
```

Docs interativas (Swagger):

```text
http://127.0.0.1:8000/docs
```

### 4) Rodar testes (pytest)

Rodar todos os testes:

```bash
pytest
```

Rodar com saida detalhada:

```bash
pytest -v
```

Rodar um arquivo de teste especifico:

```bash
pytest tests/test_router_crawler.py -v
```

## Endpoint

### `GET /financial-data`

Parâmetros:

- `region` (obrigatório): região a ser filtrada no Yahoo (ex.: `brazil`)
- `max_pages` (opcional): quantidade máxima de páginas para processar
- `headless` (opcional, default `false`): executa navegador sem interface quando `true`

Exemplos:

```http
GET /financial-data?region=brazil
GET /financial-data?region=brazil&headless=true
GET /financial-data?region=brazil&max_pages=3
GET /financial-data?region=brazil&max_pages=3&headless=true
```

Retorno:

- arquivo CSV com colunas: `symbol`, `name`, `price`
