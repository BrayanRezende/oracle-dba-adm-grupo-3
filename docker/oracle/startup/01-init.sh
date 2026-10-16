#!/bin/bash
echo ">> grupo3: criando tablespace e usuário ${APP_USER} em FREEPDB1"
if ! "$ORACLE_HOME"/bin/sqlplus -s "/ as sysdba" <<EOF
WHENEVER SQLERROR EXIT FAILURE
ALTER SESSION SET CONTAINER = FREEPDB1;
CREATE TABLESPACE IF NOT EXISTS grupo3_data
  DATAFILE '/opt/oracle/oradata/FREE/FREEPDB1/grupo3_data01.dbf'
  SIZE 100M AUTOEXTEND ON NEXT 50M MAXSIZE 2G;
CREATE USER IF NOT EXISTS ${APP_USER} IDENTIFIED BY "${APP_USER_PASSWORD}"
  DEFAULT TABLESPACE grupo3_data QUOTA UNLIMITED ON grupo3_data;
GRANT DB_DEVELOPER_ROLE TO ${APP_USER};
EXIT
EOF
then
  echo ">> grupo3: ERRO ao criar tablespace/usuário"
  return 0
fi

echo ">> grupo3: criando tabela kb_docs"
"$ORACLE_HOME"/bin/sqlplus -s "${APP_USER}/\"${APP_USER_PASSWORD}\"@//localhost:1521/FREEPDB1" <<EOF
WHENEVER SQLERROR EXIT FAILURE
@/grupo3-sql/01-create-table.sql
EXIT
EOF

echo ">> grupo3: init concluído"
