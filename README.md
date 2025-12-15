# Robo - Portal Familia

Este repositório contém um pipeline que extrai dados de uma view Oracle (`VWPACIENTES_COMVISITAS`), processa os registros (gera senha/hash Argon2id) e insere/atualiza os usuários na tabela Postgres `UserRegistrationForm`.

Arquivos relevantes:

- `dispatcher.py` — extrai dados do Oracle e enfileira no SQLite local.
- `performer.py` — consome a fila local, gera hash/salt e insere no Postgres.
- `run_pipeline.py` — executa `dispatcher` e, em seguida, `performer` (modo `--once` por padrão). Use `--daemon` para rodar o performer contínuo.
- `pg_client.py` — cliente simples para inserção/upsert no Postgres.
- `robo_user_registration.py` — utilitário para gerar `UserPasswordHash` e `UserPasswordSalt`.
- `settings/.env` — arquivo de configuração de ambiente (NÃO comitar no repositório com segredos).

## Docker (recomendado)

Infra preferida: empacotar e executar via Docker. O projeto já contém `Dockerfile` e `docker-compose.yml` de exemplo.

Passos para infra (exemplo Linux/host):

1. Coloque o Oracle Instant Client no servidor (versão 23.x). Extraia para `/opt/instantclient_23_0` no host ou para um diretório que a equipe prefira.

2. No diretório do projeto, crie a pasta `instantclient` contendo o conteúdo do instant client ou monte diretamente pelo compose. O `docker-compose.yml` já referencia `./instantclient:/opt/oracle/instantclient_23_0`.

3. Crie `settings/.env` no servidor com as credenciais (exemplo já existe no repositório local). Garanta `DRY_RUN=1` para testes iniciais.

4. Build e up:

```bash
docker compose build
docker compose up -d
```

5. Ver logs:

```bash
docker compose logs -f robo
```

6. Após validar (DRY_RUN=1), altere `DRY_RUN=0` no `settings/.env` e reinicie o serviço:

```bash
docker compose restart
```

Notas sobre Instant Client
- Por limitações de licenciamento, o Instant Client não é incluído na imagem. A infra deve disponibilizar os binários e montá-los em `/opt/oracle/instantclient_23_0` (ou alterar `ORACLE_INSTANT_CLIENT` no `settings/.env`).
- Instale `libaio1` no container (o `Dockerfile` já instala). Verifique o Visual C++ Redistributable se usar Windows hosts.

## Alternativas
- `systemd` service (mostrado em comentários no histórico) para máquinas sem Docker.
- Windows: usar NSSM para criar um serviço que execute `python run_pipeline.py --daemon`.

## Checklist para entrega à equipe de infra
- Repositório (ou imagem Docker) e instruções acima.
- `settings/.env` com valores corretos (não comitar).
- Pasta `instantclient` com os binários do Oracle (ou instrução para montar onde infra preferir).
- Garantir que o Postgres tenha PK/unique em `IdAdimission` (usado para ON CONFLICT upsert).
- Decidir `DRY_RUN` e política de logs/rotacionamento.

Se quiser, eu gero a imagem Docker localmente (não tenho acesso ao seu host), ou adapto o `docker-compose.yml` para usar um registry privado e publicar a imagem com tag.
