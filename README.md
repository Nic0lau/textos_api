# Introdução  

Esse programa é uma API em escrita em python que permite aos usuários compartilhar textos entre si.

# Uso

Antes de tudo é preciso olhar o arquivo `src/config.py`, lá estão configurações como o ip e a porta onde o servidor será executado, que devem ser ajustados ao seu gosto.

Depois é necessario executar o arquivo `src/init_db.py`, que fará a configuração inicial do banco de dados, criando as tabelas e inserindo nele todos os sonetos de Shakespeare, que constam no arquivo `shakespeare.txt`. Caso queira, você pode remover a parte dos sonetos, que são apenas para testes.

O arquivo `src/server.py` é o servidor HTTP e é ele que deve ser executado após a configuração inicial.
