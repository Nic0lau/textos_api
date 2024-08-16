import socket

from datetime import datetime
import time

import sqlite3
from random import randint

import hashlib
from urllib.parse import unquote

import config # Creates constants
import connections # Rudimentary protection agains DDoS
import err # Defines error constants

def add_text(user, author, title, text):
	user_id = cursor.execute("SELECT id FROM Users WHERE name = ?", (user,)).fetchone()[0]
	check_dup = cursor.execute("SELECT * FROM Poems WHERE name = ? AND user = ?", (title, user_id)).fetchall()
	if len(check_dup) == 0:
		cursor.execute("INSERT INTO Poems VALUES (NULL, ?, ?, ?, ?)", (user_id, title, author, text))
		db_con.commit()
		return err.SUCESSFULL_ADD
	else:
		return err.ERR_DUP_TITLE

def query_poem(name, user):
	if name == "0":
		name = "Sonnet " + str(randint(1, 155))

	if user == '':
		res = cursor.execute("SELECT * FROM Poems WHERE name = ?", (name,)).fetchone()
	else:
		user_id = cursor.execute("SELECT id FROM Users WHERE name = ?", (user,)).fetchone()
		if user_id is None:
			return err.ERR_USERNAME_DOESNT_EXIST
		else:
			user_id = user_id[0]
			res = cursor.execute("SELECT * FROM Poems WHERE name = ? AND user = ?", (name, user_id)).fetchone()

	return res

def del_text(user, title):
	user_id = cursor.execute("SELECT id FROM Users WHERE name = ?", (user,)).fetchone()[0]
	res = cursor.execute("DELETE FROM Poems WHERE user = ? AND name = ?", (user_id, title)).fetchone()

	db_con.commit()

	return err.SUCESSFULL_DELETE 

def register(name, pw):
	if name == '' or pw == '':
		return err.ERR_EMPTY_FIELD
	if len(cursor.execute("SELECT * FROM Users WHERE name = ?", (name,)).fetchall()) > 0:
		return err.ERR_USERNAME_TAKEN
	hashed_pass = hashlib.sha256(pw.encode("utf8")).hexdigest()
	cursor.execute("INSERT INTO Users VALUES (NULL, ?, ?)", (name, hashed_pass))
	db_con.commit()

	return err.SUCESSFULL_REGISTER 

def login(name, pw):
	row = cursor.execute("SELECT * FROM Users WHERE name = ?", (name,)).fetchone()
	if row is None:
		return err.ERR_USERNAME_DOESNT_EXIST 
	if row[2] != hashlib.sha256(pw.encode("utf8")).hexdigest():
		return err.ERR_WRONG_PASSWORD

	return err.SUCESSFULL_LOGIN 

def serve_file(path):
	f = open(path, "r")
	data = f.read()
	return f"HTTP/1.1 200 OK\r\nContent-type: text/html; charset=utf-8\r\nContent-length: {len(data)}\r\n\r\n" + data

def parse_req(buf):
	buf = buf.partition('\r')
	
	if buf[2] == "":
		return err.ERR_BAD_REQUEST
	
	first_line = buf[0]
	tokens = first_line.replace("?", " ").replace("/", " ").replace("&", " ").split()
	log_file.write(f'Request: {buf}\n')
	log_file.write(f'Tokenized request: {tokens}\n')

	if tokens[0] != "GET" and tokens[0] != "POST":
		return err.ERR_METHOD_NOT_ALLOWED

	if tokens[0] == "POST":
		body = buf[2].partition("\r\n\r\n")[2]
		body = unquote(body)
		body_tokens = body.replace('&', '#').replace('?', '#').replace('=', '#').replace('+', ' ').split('#')

		if tokens[1] == "reg":
			if len(body_tokens) != 4:
				return err.ERR_BAD_REQUEST
			if body_tokens[0] != 'name' or body_tokens[2] != 'pass':
				return err.ERR_BAD_REQUEST
			return register(body_tokens[1], body_tokens[3])
		elif tokens[1] == "del":
			if len(body_tokens) != 6:
				return err.ERR_BAD_REQUEST
			if body_tokens[0] != 'name' or body_tokens[2] != 'pass' or body_tokens[4] != 'title':
				return err.ERR_BAD_REQUEST

			login_status = login(body_tokens[1], body_tokens[3])

			if login_status == err.SUCESSFULL_LOGIN:
				return del_text(body_tokens[1], body_tokens[5])
			else:
				return login_status
		elif tokens[1] == "add":
			if len(body_tokens) != 10:
				return err.ERR_BAD_REQUEST
			if body_tokens[0] != 'name' or body_tokens[2] != 'pass' or body_tokens[4] != 'title' or body_tokens[6] != 'author' or body_tokens[8] != 'text':
				return err.ERR_BAD_REQUEST

			login_status = login(body_tokens[1], body_tokens[3])

			if login_status == err.SUCESSFULL_LOGIN:
				return add_text(body_tokens[1], body_tokens[7], body_tokens[5], body_tokens[9])
			else:
				return login_status

	tokens.pop(0)

	if tokens[0] == "HTTP" or tokens[0] == "index.html":
		return err.WANTS_FILE
	
	if tokens[0] == "api":
		nome = 0
		usuario = ''
		for t in tokens:
			if  t.lower().find("nome") != -1:
				nome = unquote(t[5::])
			if  t.lower().find("usuario") != -1:
				usuario = unquote(t[8::])
	
		return (nome, usuario)
	else:
		return err.ERR_NOT_FOUND

def handle_client(sock, addr):
	recv_buf = sock.recv(1024 * 1024).decode('utf8')
	log_file.write(recv_buf)
	log_file.write(f"({datetime.today().strftime('%Y-%m-%d %H:%M:%S')})[+] Received request from {addr[0]}:{addr[1]}, info below:\n")
	t1 = time.time()
	req = parse_req(recv_buf)
	log_file.write(f'Params tuple: {req}\n')
	
	match req:
		case err.ERR_BAD_REQUEST:
			data = "HTTP/1.1 400 Bad Request\r\n"
		case err.ERR_WRONG_PASSWORD:
			data = "HTTP/1.1 401 Unauthorized\r\n"
		case err.ERR_NOT_FOUND:
			data = "HTTP/1.1 404 Not Found\r\n"
		case err.ERR_METHOD_NOT_ALLOWED:
			data = "HTTP/1.1 405 Method Not Allowed\r\n"
		case err.WANTS_FILE:
			data = serve_file("./../html/index.html")
		case err.ERR_EMPTY_FIELD:
			msg = "Todos os campos devem ser preenchidos."
			data = "HTTP/1.1 400 Bad Request\r\nContent-type: text/plain\r\nContent-length: {len(msg)}\r\n\r\n"
			data += msg
		case err.ERR_USERNAME_TAKEN:
			msg = "Este nome ja esta em uso."
			data = "HTTP/1.1 400 Bad Request\r\nContent-type: text/plain\r\nContent-length: {len(msg)}\r\n\r\n"
			data += msg
		case err.ERR_DUP_TITLE:
			msg = "Voce ja tem um texto com esse mesmo titulo."
			data = "HTTP/1.1 400 Bad Request\r\nContent-type: text/plain\r\nContent-length: {len(msg)}\r\n\r\n"
			data += msg
		case err.ERR_USERNAME_DOESNT_EXIST:
			msg = "Nao ha usuario cadastrado com esse nome."
			data = "HTTP/1.1 400 Bad Request\r\nContent-type: text/plain\r\nContent-length: {len(msg)}\r\n\r\n"
			data += msg
		case err.SUCESSFULL_REGISTER:
			msg = "Registrado com sucesso."
			data = "HTTP/1.1 200 OK\r\nContent-type: text/plain\r\nContent-length: {len(msg)}\r\n\r\n"
			data += msg
		case err.SUCESSFULL_LOGIN:
			msg = "Logado com sucesso."
			data = "HTTP/1.1 200 OK\r\nContent-type: text/plain\r\nContent-length: {len(msg)}\r\n\r\n"
			data += msg
		case err.SUCESSFULL_ADD:
			msg = "Adicionado com sucesso."
			data = "HTTP/1.1 200 OK\r\nContent-type: text/plain\r\nContent-length: {len(msg)}\r\n\r\n"
			data += msg
		case err.SUCESSFULL_DELETE:
			msg = "Removido com sucesso."
			data = "HTTP/1.1 200 OK\r\nContent-type: text/plain\r\nContent-length: {len(msg)}\r\n\r\n"
			data += msg
		case _:
			msg = query_poem(req[0], req[1])
			if msg == err.ERR_USERNAME_DOESNT_EXIST:
				msg = "Nao ha usuario cadastrado com esse nome."
				data = "HTTP/1.1 400 Bad Request\r\nContent-type: text/plain\r\nContent-length: {len(msg)}\r\n\r\n"
				data += msg	
			elif msg is not None:
				data = f"HTTP/1.1 200 OK\r\nContent-type: text/plain; charset=utf-8\r\nContent-length: {len(msg[2].encode('utf8') + msg[3].encode('utf8') + msg[4].encode('utf8'))+4}\r\n\r\n"
				data += msg[2] + '\n\n' + msg[4] + '\n\n' + msg[3]
			else:
				data = "HTTP/1.1 404 Not Found\r\n"
	try:
		sock.sendall(data.encode('utf8'))
	except Exception as e:
		log_file.write(f"({datetime.today().strftime('%Y-%m-%d %H:%M:%S')})[-] Error sending mensage to {addr[0]}:{addr[1]}. {e}\n")

	t2 = time.time()
	
	log_file.write(f"({datetime.today().strftime('%Y-%m-%d %H:%M:%S')})[+] Response sent, time spent: {t2 - t1}s\n")

	return

log_file = open(config.LOG_FILENAME, "a", buffering=1)

log_file.write('=' * 80 + '\n')

db_con = sqlite3.connect(config.DB_FILENAME)
cursor = db_con.cursor()

log_file.write(f"({datetime.today().strftime('%Y-%m-%d %H:%M:%S')})[+] {config.DB_FILENAME} Database sucessfully open\n")

sock = socket.create_server((config.HOST, config.PORT), family=socket.AF_INET, backlog=config.LISTEN_BACKLOG)
log_file.write(f"({datetime.today().strftime('%Y-%m-%d %H:%M:%S')})[+] Server created, binded at {config.HOST}:{config.PORT} and listening...\n")

conns = []

t1 = time.time()
while True:
	t2 = time.time()
	if (t2 - t1) > 10: # Run every 10 seconds
		t1 = t2
		connections.cleanup_old_connections(conns)
		log_file.write(f"({datetime.today().strftime('%Y-%m-%d %H:%M:%S')})[+] Cleaning up old connections...\n")
		log_file.write(f"({datetime.today().strftime('%Y-%m-%d %H:%M:%S')})[+] Active connections: {[c.addr for c in conns]}\n")

	client_socket, client_addr = sock.accept()
	client_conn = connections.Connection(client_addr[0])
	check = connections.check_connection(conns, client_conn.addr)
	if check >= 0:
		if check == 1:
			conns.append(client_conn)
		log_file.write(f"({datetime.today().strftime('%Y-%m-%d %H:%M:%S')})[+] Sucessfully connected to client {client_addr[0]}:{client_addr[1]}\n")
		log_file.write(f"({datetime.today().strftime('%Y-%m-%d %H:%M:%S')})[+] Active connections: {[c.addr for c in conns]}\n")
		handle_client(client_socket, client_addr)
	else:
		log_file.write(f"({datetime.today().strftime('%Y-%m-%d %H:%M:%S')})[-] Denied connection with client {client_addr[0]}:{client_addr[1]}\n")
		client_socket.sendall("HTTP/1.1 429 Too Many Requests\r\n".encode('ascii'))
	client_socket.close()
	log_file.write(f"({datetime.today().strftime('%Y-%m-%d %H:%M:%S')})[+] Ended connection with {client_addr[0]}:{client_addr[1]}\n")
