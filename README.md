Para fazer o projeto rodar, precisamos inicialmente criar a nossa .venv

* Para Linux:
    - python3 -m venv .venv

* Para Windows:
    - python3 -m venv .venv

Após criado, vamos precisar navegar para usar o ambiente virtual criado pelo comando anterior:

* Para Linux:
    - source .venv/bin/activate

Com nosso projeto configurado, precisamos instalar as nossas dependências:

* Para linux:
    - pip install -r requirements.txt

O projeto utiliza o FastAPI como framework para rodar o servidor e com ele temos o swagger já instalado que nos ajuda a validar as rotas que temos e rodar o projeto mais facilmente.

* Para acessar as rotas utilize:
    - http://localhost:8000/docs